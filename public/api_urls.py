"""
API URL configuration for public app.
"""
from django.urls import path
from . import views

# API URLs (for /api/public/)
urlpatterns = [
    path("notices/", views.NoticeListAPIView.as_view(), name="notice-list-api"),
    path("applications/", views.AdmissionApplicationCreateAPIView.as_view(), name="admission-application-create-api"),
    path("register/", views.UserRegistrationAPIView.as_view(), name="user-registration-api"),
]