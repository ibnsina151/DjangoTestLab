from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class Alert(models.Model):
    ALERT_TYPES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    title = models.CharField(max_length=100, blank=False)
    message = models.TextField(blank=False)
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES, default='info')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        if not self.title.strip():
            raise ValidationError("Title cannot be empty or whitespace only.")
        if not self.message.strip():
            raise ValidationError("Message cannot be empty or whitespace only.")
        if self.alert_type not in dict(self.ALERT_TYPES):
            raise ValidationError("Invalid alert type.")

    def __str__(self):
        return f"{self.title} ({self.alert_type})"

    class Meta:
        ordering = ['-created_at']


class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    alerts = models.ManyToManyField(Alert, related_name='locations', blank=True)

    def clean(self):
        if not self.name.strip():
            raise ValidationError("Location name cannot be empty.")
        if self.latitude and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError("Latitude must be between -90 and 90.")
        if self.longitude and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError("Longitude must be between -180 and 180.")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
