from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/', views.AlertDetailView.as_view(), name='alert_detail'),
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    path('locations/<int:pk>/', views.LocationDetailView.as_view(), name='location_detail'),
    # API endpoints
    path('api/alerts/', views.AlertListAPI.as_view(), name='alert_list_api'),
    path('api/alerts/<int:pk>/', views.AlertDetailAPI.as_view(), name='alert_detail_api'),
]