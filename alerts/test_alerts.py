from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from alerts.models import Alert, Location, Profile
import requests
import time
from alerts.tasks import fetch_alerts_task

class AlertModelTest(TestCase):
    def test_alert_creation_valid(self):
        alert = Alert(title="Test Alert", message="This is a test message", alert_type="info")
        alert.full_clean()  # Should not raise
        alert.save()
        self.assertEqual(alert.title, "Test Alert")
        self.assertEqual(alert.alert_type, "info")
        self.assertTrue(alert.is_active)
        self.assertIsNotNone(alert.created_at)

    def test_alert_str_method(self):
        alert = Alert(title="Sample", message="Msg", alert_type="warning")
        self.assertEqual(str(alert), "Sample (warning)")

    def test_alert_title_validation_empty(self):
        alert = Alert(title="", message="Valid message", alert_type="info")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_alert_title_validation_whitespace(self):
        alert = Alert(title="   ", message="Valid message", alert_type="info")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_alert_message_validation_empty(self):
        alert = Alert(title="Valid Title", message="", alert_type="info")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_alert_message_validation_whitespace(self):
        alert = Alert(title="Valid Title", message="   ", alert_type="info")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_alert_type_validation_invalid(self):
        alert = Alert(title="Valid Title", message="Valid message", alert_type="invalid")
        with self.assertRaises(ValidationError):
            alert.full_clean()

    def test_alert_type_validation_valid_choices(self):
        for alert_type in ['info', 'warning', 'error']:
            alert = Alert(title="Title", message="Message", alert_type=alert_type)
            alert.full_clean()  # Should not raise


class LocationModelTest(TestCase):
    def setUp(self):
        self.location1 = Location.objects.create(name="New York", latitude=Decimal('40.7128'), longitude=Decimal('-74.0060'))
        self.location2 = Location.objects.create(name="London", latitude=Decimal('51.5074'), longitude=Decimal('-0.1278'))
        self.alert1 = Alert.objects.create(title="Alert 1", message="Message 1", alert_type="warning")
        self.alert2 = Alert.objects.create(title="Alert 2", message="Message 2", alert_type="error")

    def test_location_creation_valid(self):
        location = Location(name="Paris", latitude=Decimal('48.8566'), longitude=Decimal('2.3522'))
        location.full_clean()
        location.save()
        self.assertEqual(location.name, "Paris")
        self.assertEqual(location.latitude, Decimal('48.8566'))

    def test_location_str_method(self):
        self.assertEqual(str(self.location1), "New York")

    def test_location_name_validation_empty(self):
        location = Location(name="", latitude=Decimal('0'), longitude=Decimal('0'))
        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_location_latitude_validation_invalid(self):
        location = Location(name="Test", latitude=Decimal('91'), longitude=Decimal('0'))
        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_location_longitude_validation_invalid(self):
        location = Location(name="Test", latitude=Decimal('0'), longitude=Decimal('181'))
        with self.assertRaises(ValidationError):
            location.full_clean()

    def test_many_to_many_relation(self):
        # Add alerts to location
        self.location1.alerts.add(self.alert1, self.alert2)
        self.location1.save()
        self.assertIn(self.alert1, self.location1.alerts.all())
        self.assertIn(self.alert2, self.location1.alerts.all())

        # Check reverse relation
        self.assertIn(self.location1, self.alert1.locations.all())

    def test_orm_queries(self):
        # Associate alerts with locations
        self.location1.alerts.add(self.alert1)
        self.location2.alerts.add(self.alert2)

        # Query locations with specific alerts
        locations_with_alert1 = Location.objects.filter(alerts=self.alert1)
        self.assertIn(self.location1, locations_with_alert1)
        self.assertNotIn(self.location2, locations_with_alert1)

        # Query alerts for a location
        alerts_for_location1 = self.location1.alerts.all()
        self.assertEqual(list(alerts_for_location1), [self.alert1])

        # Query alerts with locations
        alerts_with_locations = Alert.objects.filter(locations__isnull=False)
        self.assertEqual(set(alerts_with_locations), {self.alert1, self.alert2})

        # Filter locations by alert type
        locations_with_warning = Location.objects.filter(alerts__alert_type='warning')
        self.assertIn(self.location1, locations_with_warning)


class ServiceFunctionsTest(TestCase):
    @patch('alerts.services.Alert.objects')
    def test_filter_alerts_by_location_instance(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_alerts.filter.return_value = mock_queryset
        location = Location(name="Test")

        from alerts.services import filter_alerts_by_location
        result = filter_alerts_by_location(location)

        mock_alerts.filter.assert_called_once_with(locations=location)
        self.assertEqual(result, mock_queryset)

    @patch('alerts.services.Alert.objects')
    def test_filter_alerts_by_location_id(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_alerts.filter.return_value = mock_queryset

        from alerts.services import filter_alerts_by_location
        result = filter_alerts_by_location(1)

        mock_alerts.filter.assert_called_once_with(locations__id=1)
        self.assertEqual(result, mock_queryset)

    @patch('alerts.services.Alert.objects')
    def test_filter_alerts_by_location_with_severities(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_filtered = MagicMock()
        mock_alerts.filter.return_value = mock_queryset
        mock_queryset.filter.return_value = mock_filtered

        from alerts.services import filter_alerts_by_location
        result = filter_alerts_by_location(1, ['warning', 'error'])

        mock_alerts.filter.assert_called_once_with(locations__id=1)
        mock_queryset.filter.assert_called_once_with(alert_type__in=['warning', 'error'])
        self.assertEqual(result, mock_filtered)

    @patch('alerts.services.Alert.objects')
    def test_filter_alerts_by_severity(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_alerts.filter.return_value = mock_queryset

        from alerts.services import filter_alerts_by_severity
        result = filter_alerts_by_severity(['info', 'warning'])

        mock_alerts.filter.assert_called_once_with(alert_type__in=['info', 'warning'])
        self.assertEqual(result, mock_queryset)

    @patch('alerts.services.Alert.objects')
    def test_get_active_alerts_for_location_instance(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_alerts.filter.return_value = mock_queryset
        location = Location(name="Test")

        from alerts.services import get_active_alerts_for_location
        result = get_active_alerts_for_location(location)

        mock_alerts.filter.assert_called_once_with(locations=location, is_active=True)
        self.assertEqual(result, mock_queryset)

    @patch('alerts.services.Alert.objects')
    def test_get_active_alerts_for_location_id(self, mock_alerts):
        mock_queryset = MagicMock()
        mock_alerts.filter.return_value = mock_queryset

        from alerts.services import get_active_alerts_for_location
        result = get_active_alerts_for_location(2)

        mock_alerts.filter.assert_called_once_with(locations__id=2, is_active=True)
        self.assertEqual(result, mock_queryset)

    @patch('alerts.services.requests.get')
    def test_fetch_external_alerts_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [{'title': 'External Alert', 'message': 'External Message'}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        from alerts.services import fetch_external_alerts
        result = fetch_external_alerts('http://example.com/alerts')

        mock_get.assert_called_once_with('http://example.com/alerts')
        mock_response.raise_for_status.assert_called_once()
        mock_response.json.assert_called_once()
        self.assertEqual(result, [{'title': 'External Alert', 'message': 'External Message'}])

    @patch('alerts.services.requests.get')
    def test_fetch_external_alerts_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_get.return_value = mock_response

        from alerts.services import fetch_external_alerts
        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_external_alerts('http://example.com/alerts')

        mock_get.assert_called_once_with('http://example.com/alerts')
        mock_response.raise_for_status.assert_called_once()


class AsyncTaskTests(TestCase):
    @patch('alerts.services.requests.get')
    def test_async_task_underlying_function_success(self, mock_get):
        # Test the underlying function that the task uses
        mock_response = MagicMock()
        mock_response.json.return_value = [{'title': 'Async Alert'}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        from alerts.services import fetch_external_alerts
        result = fetch_external_alerts('http://example.com/alerts')

        self.assertEqual(result, [{'title': 'Async Alert'}])
        mock_get.assert_called_once_with('http://example.com/alerts')

    @patch('alerts.services.requests.get')
    def test_async_task_underlying_function_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        from alerts.services import fetch_external_alerts
        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_external_alerts('http://example.com/alerts')

        mock_get.assert_called_once_with('http://example.com/alerts')


class IntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='integration', password='integrate')
        self.client.login(username='integration', password='integrate')
        self.location = Location.objects.create(name="Integration Location", latitude=Decimal('40.7128'), longitude=Decimal('-74.0060'))

    def test_full_workflow_alert_creation_and_viewing(self):
        # Create alert via API
        alert_data = {
            'title': 'Integration Alert',
            'message': 'Test message',
            'alert_type': 'warning'
        }
        response = self.client.post(reverse('alerts:alert_list_api'), alert_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        alert_id = response.data['id']

        # View alert list
        response = self.client.get(reverse('alerts:alert_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Alert')

        # View alert detail
        response = self.client.get(reverse('alerts:alert_detail', kwargs={'pk': alert_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Alert')

        # View via API
        response = self.client.get(reverse('alerts:alert_detail_api', kwargs={'pk': alert_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Integration Alert')

    def test_location_workflow(self):
        # View locations
        response = self.client.get(reverse('alerts:location_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Location')

        # View location detail
        response = self.client.get(reverse('alerts:location_detail', kwargs={'pk': self.location.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Integration Location')

    def test_profile_creation(self):
        # Check profile was created
        profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(profile)
        # Associate location
        profile.location = self.location
        profile.save()
        self.assertEqual(profile.location, self.location)


class PerformanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='perf', password='perf')
        self.client.login(username='perf', password='perf')
        # Create some data
        for i in range(10):
            Alert.objects.create(title=f'Alert {i}', message=f'Message {i}')

    def test_api_response_time(self):
        start_time = time.time()
        response = self.client.get(reverse('alerts:alert_list_api'))
        end_time = time.time()
        response_time = end_time - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Should respond in less than 1 second

    def test_page_load_time(self):
        start_time = time.time()
        response = self.client.get(reverse('alerts:alert_list'))
        end_time = time.time()
        response_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # Should load in less than 1 second


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        self.location1 = Location.objects.create(name="New York", latitude=Decimal('40.7128'), longitude=Decimal('-74.0060'))
        self.location2 = Location.objects.create(name="London", latitude=Decimal('51.5074'), longitude=Decimal('-0.1278'))
        self.alert1 = Alert.objects.create(title="Alert 1", message="Message 1", alert_type="warning")
        self.alert2 = Alert.objects.create(title="Alert 2", message="Message 2", alert_type="error")
        self.location1.alerts.add(self.alert1)

    def test_alert_list_view(self):
        response = self.client.get(reverse('alerts:alert_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'alerts/alert_list.html')
        self.assertContains(response, 'Alerts')
        self.assertContains(response, self.alert1.title)
        self.assertContains(response, self.alert2.title)

    def test_alert_detail_view(self):
        response = self.client.get(reverse('alerts:alert_detail', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'alerts/alert_detail.html')
        self.assertContains(response, self.alert1.title)
        self.assertContains(response, self.alert1.message)
        self.assertContains(response, self.alert1.get_alert_type_display())
        self.assertContains(response, self.location1.name)

    def test_alert_detail_view_not_found(self):
        response = self.client.get(reverse('alerts:alert_detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 404)

    def test_location_list_view(self):
        response = self.client.get(reverse('alerts:location_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'alerts/location_list.html')
        self.assertContains(response, 'Locations')
        self.assertContains(response, self.location1.name)
        self.assertContains(response, self.location2.name)

    def test_location_detail_view(self):
        response = self.client.get(reverse('alerts:location_detail', kwargs={'pk': self.location1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'alerts/location_detail.html')
        self.assertContains(response, self.location1.name)
        self.assertContains(response, self.alert1.title)

    def test_location_detail_view_not_found(self):
        response = self.client.get(reverse('alerts:location_detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, 404)


class PermissionTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name="Test Location")
        self.alert = Alert.objects.create(title="Test Alert", message="Test Message")

    def test_alert_list_requires_login(self):
        response = self.client.get(reverse('alerts:alert_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn('/accounts/login/', response['Location'])

    def test_alert_detail_requires_login(self):
        response = self.client.get(reverse('alerts:alert_detail', kwargs={'pk': self.alert.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_location_list_requires_login(self):
        response = self.client.get(reverse('alerts:location_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_location_detail_requires_login(self):
        response = self.client.get(reverse('alerts:location_detail', kwargs={'pk': self.location.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


class ProfileTests(TestCase):
    def test_profile_created_on_user_creation(self):
        user = User.objects.create_user(username='profiletest', email='test@example.com')
        profile = Profile.objects.get(user=user)
        self.assertIsNotNone(profile)
        self.assertEqual(str(profile), "profiletest's profile")

    def test_profile_associated_with_location(self):
        user = User.objects.create_user(username='profileloc')
        location = Location.objects.create(name="Profile Location")
        profile = Profile.objects.get(user=user)
        profile.location = location
        profile.save()
        self.assertEqual(profile.location, location)


class APITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apitest', password='apipass')
        self.client.login(username='apitest', password='apipass')
        self.location1 = Location.objects.create(name="API Location", latitude=Decimal('40.7128'), longitude=Decimal('-74.0060'))
        self.alert1 = Alert.objects.create(title="API Alert 1", message="API Message 1", alert_type="warning")
        self.alert2 = Alert.objects.create(title="API Alert 2", message="API Message 2", alert_type="error")
        self.alert1.locations.add(self.location1)

    def test_alert_list_api_authenticated(self):
        response = self.client.get(reverse('alerts:alert_list_api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data)
        self.assertGreaterEqual(len(data), 2)
        titles = [item['title'] for item in data]
        self.assertIn(self.alert1.title, titles)
        self.assertIn(self.alert2.title, titles)

    def test_alert_list_api_pagination(self):
        # Create more alerts to test pagination
        for i in range(15):
            Alert.objects.create(title=f"Alert {i}", message=f"Message {i}")
        response = self.client.get(reverse('alerts:alert_list_api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # PAGE_SIZE
        self.assertIn('next', response.data)
        self.assertIsNotNone(response.data['next'])

    def test_alert_detail_api(self):
        response = self.client.get(reverse('alerts:alert_detail_api', kwargs={'pk': self.alert1.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.alert1.title)
        self.assertEqual(len(response.data['locations']), 1)
        self.assertEqual(response.data['locations'][0]['name'], self.location1.name)

    def test_alert_detail_api_not_found(self):
        response = self.client.get(reverse('alerts:alert_detail_api', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_alert_api_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse('alerts:alert_list_api'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
