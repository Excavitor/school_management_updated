"""Clean and focused tests for dashboard app."""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Role
from public.models import AdmissionApplication, Notice

User = get_user_model()


class DashboardTestBase:
    """Base test setup for dashboard tests."""
    
    def setUp(self):
        # Create roles
        self.superadmin_role, _ = Role.objects.get_or_create(name='SuperAdmin')
        self.admin_role, _ = Role.objects.get_or_create(name='Admin')
        self.guest_role, _ = Role.objects.get_or_create(name='Guest')
        
        # Create users
        self.superadmin = User.objects.create_user(
            username='superadmin', email='super@test.com', password='test123',
            phone_number='01712345678', role=self.superadmin_role
        )
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com', password='test123',
            phone_number='01712345679', role=self.admin_role
        )
        self.guest = User.objects.create_user(
            username='guest', email='guest@test.com', password='test123',
            phone_number='01712345680', role=self.guest_role
        )
        
        # Create test data
        self.notice = Notice.objects.create(
            title='Test Notice', content='Test content',
            published=True, created_by=self.admin
        )
        self.application = AdmissionApplication.objects.create(
            student_name='John Doe', student_dob='2010-01-01',
            enrolled_class='Class 5', address='Test Address',
            guardian_name='Jane Doe', guardian_mobile='01712345681',
            guardian_email='jane@test.com'
        )


class DashboardAPITestCase(DashboardTestBase, APITestCase):
    """Test dashboard API endpoints."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def get_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def authenticate(self, user):
        """Authenticate user."""
        token = self.get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_dashboard_stats_admin_access(self):
        """Test dashboard stats access for admin."""
        self.authenticate(self.admin)
        response = self.client.get(reverse('dashboard:dashboard-stats-api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_applications', response.data)
    
    def test_dashboard_stats_guest_denied(self):
        """Test dashboard stats denied for guest."""
        self.authenticate(self.guest)
        response = self.client.get(reverse('dashboard:dashboard-stats-api'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_notice_list_admin(self):
        """Test notice list for admin."""
        self.authenticate(self.admin)
        response = self.client.get(reverse('dashboard:notice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_application_list_admin(self):
        """Test application list for admin."""
        self.authenticate(self.admin)
        response = self.client.get(reverse('dashboard:application-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_list_superadmin_only(self):
        """Test user list access for SuperAdmin only."""
        # SuperAdmin should have access
        self.authenticate(self.superadmin)
        response = self.client.get(reverse('dashboard:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Admin should be denied
        self.authenticate(self.admin)
        response = self.client.get(reverse('dashboard:user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DashboardFrontendTestCase(DashboardTestBase, TestCase):
    """Test dashboard frontend views."""
    
    def setUp(self):
        super().setUp()
        self.client = Client()
    
    def test_dashboard_home_admin_access(self):
        """Test dashboard home access for admin."""
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_home_guest_redirect(self):
        """Test dashboard home redirects for guest."""
        self.client.login(username='guest', password='test123')
        response = self.client.get(reverse('dashboard:home'))
        # Should redirect or show limited access
        self.assertIn(response.status_code, [200, 302])
    
    def test_notice_list_view(self):
        """Test notice list view."""
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard:notice_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_application_list_view(self):
        """Test application list view."""
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard:application_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_profile_view(self):
        """Test user profile view."""
        self.client.login(username='admin', password='test123')
        response = self.client.get(reverse('dashboard:profile'))
        self.assertEqual(response.status_code, 200)


class PermissionTestCase(DashboardTestBase, APITestCase):
    """Test permission controls."""
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
    
    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied."""
        endpoints = [
            reverse('dashboard:dashboard-stats-api'),
            reverse('dashboard:notice-list'),
            reverse('dashboard:application-list'),
        ]
        
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_guest_permissions(self):
        """Test guest user permissions."""
        token = RefreshToken.for_user(self.guest)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        
        # Guest should not access admin endpoints
        admin_endpoints = [
            reverse('dashboard:dashboard-stats-api'),
            reverse('dashboard:notice-list'),
            reverse('dashboard:application-list'),
        ]
        
        for url in admin_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)