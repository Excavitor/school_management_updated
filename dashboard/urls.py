from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import role_views

# API Router
router = DefaultRouter()
router.register(r'notices', views.NoticeViewSet, basename='notice')
router.register(r'applications', views.AdmissionApplicationViewSet, basename='application')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'roles', views.RoleViewSet, basename='role')

app_name = 'dashboard'

urlpatterns = [
    # Frontend URLs
    path('', views.DashboardHomeView.as_view(), name='home'),
    
    # Notice Management URLs
    path('notices/', views.NoticeListView.as_view(), name='notice_list'),
    path('notices/create/', views.NoticeCreateView.as_view(), name='notice_create'),
    path('notices/<int:pk>/edit/', views.NoticeUpdateView.as_view(), name='notice_edit'),
    path('notices/<int:pk>/delete/', views.NoticeDeleteView.as_view(), name='notice_delete'),
    
    # Application Management URLs
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/edit/', views.ApplicationUpdateView.as_view(), name='application_edit'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
    path('applications/export/', views.ApplicationExportView.as_view(), name='application_export'),
    
    # User Management URLs (SuperAdmin only)
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # Role Management URLs (SuperAdmin only)
    path('roles/', role_views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', role_views.RoleCreateView.as_view(), name='role_create'),
    path('roles/<int:pk>/edit/', role_views.RoleUpdateView.as_view(), name='role_edit'),
    path('roles/<int:pk>/delete/', role_views.RoleDeleteView.as_view(), name='role_delete'),
    path('roles/<int:pk>/', role_views.RoleDetailView.as_view(), name='role_detail'),
    
    # API URLs
    path('api/stats/', views.DashboardStatsAPIView.as_view(), name='dashboard-stats-api'),
    path('api/profile/', views.UserProfileAPIView.as_view(), name='user-profile-api'),
    path('api/', include(router.urls)),
]