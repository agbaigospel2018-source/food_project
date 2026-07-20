from django.urls import path
from . import views

urlpatterns = [
    path(
        'dashboard/',
        views.vendor_dashboard,
        name='vendor_dashboard'
),
    path(
    'create/',
    views.create_vendor,
    name='create_vendor'
),
    path(
    'profile/',
    views.vendor_profile,
    name='vendor_profile'
),
    path(
    'profile/edit/',
    views.edit_vendor,
    name='edit_vendor'
), 
    path(
    'toggle-status/',
    views.toggle_vendor_status,
    name='toggle_vendor_status'
),
]