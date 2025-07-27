"""
URL configuration for public app.
Frontend URLs only.
"""
from django.urls import path
from . import views

app_name = 'public'

# Frontend URLs (for root /)
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('notices/', views.NoticeListView.as_view(), name='notices'),
    path('admission/', views.AdmissionApplicationCreateView.as_view(), name='admission_form'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]