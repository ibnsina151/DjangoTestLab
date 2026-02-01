from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated
from .models import Alert, Location
from .serializers import AlertSerializer


class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    template_name = 'alerts/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 10


class AlertDetailView(LoginRequiredMixin, DetailView):
    model = Alert
    template_name = 'alerts/alert_detail.html'
    context_object_name = 'alert'


class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'alerts/location_list.html'
    context_object_name = 'locations'
    paginate_by = 10


class LocationDetailView(LoginRequiredMixin, DetailView):
    model = Location
    template_name = 'alerts/location_detail.html'
    context_object_name = 'location'


class AlertListAPI(generics.ListCreateAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]


class AlertDetailAPI(generics.RetrieveAPIView):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
