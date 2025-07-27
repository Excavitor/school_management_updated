"""
URL configuration for accounts app.
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Custom authentication endpoints
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('info/', views.user_info, name='user-info'),
    path('users/', views.UserListView.as_view(), name='user-list'),
]