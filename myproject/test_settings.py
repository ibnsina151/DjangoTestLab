from django.test import TestCase
from django.conf import settings

class SettingsTest(TestCase):
    def test_debug_is_false_in_test(self):
        # In tests, DEBUG should be False by default, but let's check
        self.assertFalse(settings.DEBUG)