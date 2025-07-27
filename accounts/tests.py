"""
Tests for authentication system with Djoser and Simple JWT.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Role, validate_bangladeshi_phone
from .serializers import CustomUserCreateSerializer, CustomUserSerializer
from .permissions import (
    IsSuperAdminPermission, 
    IsAdminOrSuperAdminPermission, 
    IsTeacherOrAbovePermission,
    IsOwnerOrAdminPermission,
    IsGuestOrAbovePermission
)
from unittest.mock import Mock
import json

User = get_user_model()


class BangladeshiPhoneValidationTest(TestCase):
    """Test Bangladeshi phone number validation."""
    
    def test_valid_phone_numbers(self):
        """Test valid Bangladeshi phone numbers."""
        valid_numbers = [
            '01712345678',
            '01812345678',
            '01912345678',
            '01512345678',
            '01612345678',
            '01312345678',
            '01412345678',
        ]
        
        for number in valid_numbers:
            with self.subTest(number=number):
                try:
                    result = validate_bangladeshi_phone(number)
                    self.assertEqual(result, number)
                except Exception as e:
                    self.fail(f"Valid number {number} failed validation: {e}")
    
    def test_invalid_phone_numbers(self):
        """Test invalid phone numbers."""
        invalid_numbers = [
            '1712345678',    # Missing leading 0
            '017123456789',  # Too long
            '0171234567',    # Too short
            '02712345678',   # Wrong prefix
            '01712345abc',   # Contains letters
            '',              # Empty
            '01 712 345 678', # With spaces (should be cleaned)
        ]
        
        for number in invalid_numbers:
            with self.subTest(number=number):
                if number == '01 712 345 678':
                    # This should be cleaned and pass
                    result = validate_bangladeshi_phone(number)
                    self.assertEqual(result, '01712345678')
                else:
                    with self.assertRaises(Exception):
                        validate_bangladeshi_phone(number)


class RoleModelTest(TestCase):
    """Test Role model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.role = Role.objects.create(
            name='TestRole',
            description='Test role for testing',
            permissions={'can_test': True, 'can_view': False}
        )
    
    def test_role_creation(self):
        """Test role creation."""
        self.assertEqual(self.role.name, 'TestRole')
        self.assertEqual(self.role.description, 'Test role for testing')
        self.assertTrue(self.role.has_permission('can_test'))
        self.assertFalse(self.role.has_permission('can_view'))
    
    def test_role_permissions(self):
        """Test role permission methods."""
        # Test adding permission
        self.role.add_permission('can_edit', True)
        self.assertTrue(self.role.has_permission('can_edit'))
        
        # Test removing permission
        self.role.remove_permission('can_test')
        self.assertFalse(self.role.has_permission('can_test'))
    
    def test_role_str_method(self):
        """Test role string representation."""
        self.assertEqual(str(self.role), 'TestRole')


class CustomUserModelTest(TestCase):
    """Test CustomUser model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='01712345678',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation with default role."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.phone_number, '01712345678')
        self.assertEqual(self.user.get_role_name(), 'Guest')
    
    def test_user_role_methods(self):
        """Test user role checking methods."""
        # Create different roles
        admin_role, _ = Role.objects.get_or_create(name='Admin')
        superadmin_role, _ = Role.objects.get_or_create(name='SuperAdmin')
        teacher_role, _ = Role.objects.get_or_create(name='Teacher')
        
        # Test Guest role
        self.assertFalse(self.user.is_super_admin())
        self.assertFalse(self.user.is_admin_or_above())
        self.assertFalse(self.user.is_teacher_or_above())
        
        # Test Admin role
        self.user.role = admin_role
        self.user.save()
        self.assertFalse(self.user.is_super_admin())
        self.assertTrue(self.user.is_admin_or_above())
        self.assertTrue(self.user.is_teacher_or_above())
        
        # Test SuperAdmin role
        self.user.role = superadmin_role
        self.user.save()
        self.assertTrue(self.user.is_super_admin())
        self.assertTrue(self.user.is_admin_or_above())
        self.assertTrue(self.user.is_teacher_or_above())


class CustomUserSerializerTest(TestCase):
    """Test custom user serializers."""
    
    def setUp(self):
        """Set up test data."""
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        self.valid_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'phone_number': '01712345678',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_create_serializer_valid_data(self):
        """Test user creation with valid data."""
        serializer = CustomUserCreateSerializer(data=self.valid_user_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.phone_number, '01712345678')
        self.assertEqual(user.get_role_name(), 'Guest')
    
    def test_user_create_serializer_invalid_phone(self):
        """Test user creation with invalid phone number."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['phone_number'] = '1234567890'  # Invalid format
        
        serializer = CustomUserCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
    
    def test_user_create_serializer_duplicate_email(self):
        """Test user creation with duplicate email."""
        # Create first user
        User.objects.create_user(**self.valid_user_data)
        
        # Try to create second user with same email
        duplicate_data = self.valid_user_data.copy()
        duplicate_data['username'] = 'testuser2'
        duplicate_data['phone_number'] = '01812345678'
        
        serializer = CustomUserCreateSerializer(data=duplicate_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class AuthenticationAPITest(APITestCase):
    """Test authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='01712345678'
        )
        
        self.user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'phone_number': '01812345678',
            'first_name': 'New',
            'last_name': 'User'
        }
    
    def test_user_registration_via_djoser(self):
        """Test user registration through Djoser endpoint."""
        url = reverse('user-list')  # Djoser's user creation endpoint
        response = self.client.post(url, self.user_data, format='json')
        
        # Should create user successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_jwt_token_obtain(self):
        """Test JWT token obtaining."""
        url = reverse('jwt-create')  # Djoser's JWT token endpoint
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_token_refresh(self):
        """Test JWT token refresh."""
        # Get initial tokens
        refresh = RefreshToken.for_user(self.user)
        
        url = reverse('jwt-refresh')
        data = {'refresh': str(refresh)}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_user_profile_access(self):
        """Test accessing user profile with JWT token."""
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Access profile endpoint
        url = reverse('accounts:user-profile')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['role_name'], 'Guest')
    
    def test_user_info_endpoint(self):
        """Test user info endpoint."""
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        access_token = refresh.access_token
        
        # Access user info endpoint
        url = reverse('accounts:user-info')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('role_permissions', response.data)
        self.assertIn('is_super_admin', response.data)
        self.assertFalse(response.data['is_super_admin'])


class PermissionTest(APITestCase):
    """Test custom permission classes."""
    
    def setUp(self):
        """Set up test data."""
        # Create roles
        self.guest_role, _ = Role.objects.get_or_create(name='Guest')
        self.admin_role, _ = Role.objects.get_or_create(name='Admin')
        self.superadmin_role, _ = Role.objects.get_or_create(name='SuperAdmin')
        
        # Create users with different roles
        self.guest_user = User.objects.create_user(
            username='guest',
            email='guest@example.com',
            password='pass123',
            phone_number='01712345678',
            role=self.guest_role
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            phone_number='01812345678',
            role=self.admin_role
        )
        
        self.superadmin_user = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='pass123',
            phone_number='01912345678',
            role=self.superadmin_role
        )
    
    def test_user_list_superadmin_only(self):
        """Test that user list endpoint requires SuperAdmin permission."""
        url = reverse('accounts:user-list')
        
        # Test without authentication
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with Guest user
        refresh = RefreshToken.for_user(self.guest_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with Admin user
        refresh = RefreshToken.for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with SuperAdmin user
        refresh = RefreshToken.for_user(self.superadmin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CustomPermissionClassesTest(TestCase):
    """Test custom permission classes in isolation."""
    
    def setUp(self):
        """Set up test data."""
        # Create or get roles
        self.guest_role, _ = Role.objects.get_or_create(name='Guest')
        self.teacher_role, _ = Role.objects.get_or_create(name='Teacher')
        self.admin_role, _ = Role.objects.get_or_create(name='Admin')
        self.superadmin_role, _ = Role.objects.get_or_create(name='SuperAdmin')
        
        # Create users with different roles
        self.guest_user = User.objects.create_user(
            username='guest',
            email='guest@example.com',
            password='pass123',
            phone_number='01712345678',
            role=self.guest_role
        )
        
        self.teacher_user = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='pass123',
            phone_number='01812345678',
            role=self.teacher_role
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='pass123',
            phone_number='01912345678',
            role=self.admin_role
        )
        
        self.superadmin_user = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='pass123',
            phone_number='01512345678',
            role=self.superadmin_role
        )
        
        # Create mock request and view objects
        self.mock_view = Mock()
        self.mock_obj = Mock()
    
    def create_mock_request(self, user=None):
        """Create a mock request with the given user."""
        mock_request = Mock()
        mock_request.user = user
        return mock_request
    
    def test_is_super_admin_permission(self):
        """Test IsSuperAdminPermission class."""
        permission = IsSuperAdminPermission()
        
        # Test with unauthenticated user
        mock_request = self.create_mock_request(None)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Guest user
        mock_request = self.create_mock_request(self.guest_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Teacher user
        mock_request = self.create_mock_request(self.teacher_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Admin user
        mock_request = self.create_mock_request(self.admin_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with SuperAdmin user
        mock_request = self.create_mock_request(self.superadmin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test object-level permission
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, self.mock_obj))
    
    def test_is_super_admin_permission_with_user_without_role(self):
        """Test IsSuperAdminPermission with user that has no role attribute."""
        permission = IsSuperAdminPermission()
        
        # Create user without role
        user_without_role = Mock()
        user_without_role.is_authenticated = True
        # Remove role attribute to simulate AttributeError
        del user_without_role.role
        
        mock_request = self.create_mock_request(user_without_role)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
    
    def test_is_admin_or_super_admin_permission(self):
        """Test IsAdminOrSuperAdminPermission class."""
        permission = IsAdminOrSuperAdminPermission()
        
        # Test with unauthenticated user
        mock_request = self.create_mock_request(None)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Guest user
        mock_request = self.create_mock_request(self.guest_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Teacher user
        mock_request = self.create_mock_request(self.teacher_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Admin user
        mock_request = self.create_mock_request(self.admin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with SuperAdmin user
        mock_request = self.create_mock_request(self.superadmin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test object-level permission
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, self.mock_obj))
    
    def test_is_teacher_or_above_permission(self):
        """Test IsTeacherOrAbovePermission class."""
        permission = IsTeacherOrAbovePermission()
        
        # Test with unauthenticated user
        mock_request = self.create_mock_request(None)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Guest user
        mock_request = self.create_mock_request(self.guest_user)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Teacher user
        mock_request = self.create_mock_request(self.teacher_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Admin user
        mock_request = self.create_mock_request(self.admin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with SuperAdmin user
        mock_request = self.create_mock_request(self.superadmin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test object-level permission
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, self.mock_obj))
    
    def test_is_guest_or_above_permission(self):
        """Test IsGuestOrAbovePermission class."""
        permission = IsGuestOrAbovePermission()
        
        # Test with unauthenticated user
        mock_request = self.create_mock_request(None)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Guest user
        mock_request = self.create_mock_request(self.guest_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Teacher user
        mock_request = self.create_mock_request(self.teacher_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with Admin user
        mock_request = self.create_mock_request(self.admin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test with SuperAdmin user
        mock_request = self.create_mock_request(self.superadmin_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test object-level permission
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, self.mock_obj))
    
    def test_is_owner_or_admin_permission(self):
        """Test IsOwnerOrAdminPermission class."""
        permission = IsOwnerOrAdminPermission()
        
        # Test with unauthenticated user
        mock_request = self.create_mock_request(None)
        self.assertFalse(permission.has_permission(mock_request, self.mock_view))
        
        # Test with authenticated user (should allow access to view)
        mock_request = self.create_mock_request(self.guest_user)
        self.assertTrue(permission.has_permission(mock_request, self.mock_view))
        
        # Test object-level permission with owner (user field)
        mock_obj_with_user = Mock()
        mock_obj_with_user.user = self.guest_user
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_user))
        
        # Test object-level permission with non-owner
        mock_obj_with_user.user = self.teacher_user
        self.assertFalse(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_user))
        
        # Test object-level permission with Admin user (should have access regardless of ownership)
        mock_request = self.create_mock_request(self.admin_user)
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_user))
        
        # Test object-level permission with SuperAdmin user
        mock_request = self.create_mock_request(self.superadmin_user)
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_user))
        
        # Test object-level permission with created_by field
        mock_obj_with_created_by = Mock()
        mock_obj_with_created_by.created_by = self.guest_user
        del mock_obj_with_created_by.user  # Remove user attribute
        
        mock_request = self.create_mock_request(self.guest_user)
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_created_by))
        
        # Test object-level permission with owner field
        mock_obj_with_owner = Mock()
        mock_obj_with_owner.owner = self.guest_user
        del mock_obj_with_owner.user  # Remove user attribute
        del mock_obj_with_owner.created_by  # Remove created_by attribute
        
        mock_request = self.create_mock_request(self.guest_user)
        self.assertTrue(permission.has_object_permission(mock_request, self.mock_view, mock_obj_with_owner))
        
        # Test object-level permission with no ownership field
        mock_obj_no_owner = Mock()
        del mock_obj_no_owner.user
        del mock_obj_no_owner.created_by
        del mock_obj_no_owner.owner
        
        mock_request = self.create_mock_request(self.guest_user)
        self.assertFalse(permission.has_object_permission(mock_request, self.mock_view, mock_obj_no_owner))
    
    def test_permission_classes_with_unauthenticated_user(self):
        """Test all permission classes with unauthenticated user."""
        permissions = [
            IsSuperAdminPermission(),
            IsAdminOrSuperAdminPermission(),
            IsTeacherOrAbovePermission(),
            IsGuestOrAbovePermission(),
            IsOwnerOrAdminPermission()
        ]
        
        # Create mock user that is not authenticated
        mock_user = Mock()
        mock_user.is_authenticated = False
        mock_request = self.create_mock_request(mock_user)
        
        for permission in permissions:
            with self.subTest(permission=permission.__class__.__name__):
                self.assertFalse(permission.has_permission(mock_request, self.mock_view))
    
    def test_permission_classes_with_none_user(self):
        """Test all permission classes with None user."""
        permissions = [
            IsSuperAdminPermission(),
            IsAdminOrSuperAdminPermission(),
            IsTeacherOrAbovePermission(),
            IsGuestOrAbovePermission(),
            IsOwnerOrAdminPermission()
        ]
        
        mock_request = self.create_mock_request(None)
        
        for permission in permissions:
            with self.subTest(permission=permission.__class__.__name__):
                self.assertFalse(permission.has_permission(mock_request, self.mock_view))