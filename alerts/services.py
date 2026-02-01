import requests
from .models import Alert, Location


def filter_alerts_by_location(location, severities=None):
    """
    Filter alerts by location and optionally by severities.

    :param location: Location instance or location id
    :param severities: list of alert types (e.g., ['warning', 'error']) or None for all
    :return: QuerySet of Alert objects
    """
    if isinstance(location, Location):
        queryset = Alert.objects.filter(locations=location)
    else:
        queryset = Alert.objects.filter(locations__id=location)

    if severities:
        queryset = queryset.filter(alert_type__in=severities)

    return queryset


def filter_alerts_by_severity(severities):
    """
    Filter alerts by severities.

    :param severities: list of alert types
    :return: QuerySet of Alert objects
    """
    return Alert.objects.filter(alert_type__in=severities)


def get_active_alerts_for_location(location):
    """
    Get active alerts for a specific location.

    :param location: Location instance or location id
    :return: QuerySet of active Alert objects
    """
    if isinstance(location, Location):
        return Alert.objects.filter(locations=location, is_active=True)
    else:
        return Alert.objects.filter(locations__id=location, is_active=True)


def fetch_external_alerts(url):
    """
    Fetch alerts from an external API.

    :param url: The URL of the external API
    :return: List of alert data or raises exception
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise for bad status
    return response.json()