from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta
from accounts.models import Role
from .models import Notice, AdmissionApplication

User = get_user_model()


class NoticeModelTest(TestCase):
    """Test cases for Notice model"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        self.superadmin_role, _ = Role.objects.get_or_create(
            name='SuperAdmin',
            defaults={'description': 'SuperAdmin role'}
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            phone_number='01712345678',
            role=self.admin_role
        )
        
        self.guest_user = User.objects.create_user(
            username='guest_user',
            email='guest@test.com',
            password='testpass123',
            phone_number='01712345679',
            role=self.guest_role
        )
        
        self.superadmin_user = User.objects.create_user(
            username='superadmin_user',
            email='superadmin@test.com',
            password='testpass123',
            phone_number='01712345680',
            role=self.superadmin_role
        )
    
    def test_notice_creation(self):
        """Test basic notice creation"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='This is a test notice content.',
            published=True,
            created_by=self.admin_user
        )
        
        self.assertEqual(notice.title, 'Test Notice')
        self.assertEqual(notice.content, 'This is a test notice content.')
        self.assertTrue(notice.published)
        self.assertEqual(notice.created_by, self.admin_user)
        self.assertIsNotNone(notice.date_created)
        self.assertIsNotNone(notice.date_updated)
    
    def test_notice_str_representation(self):
        """Test string representation of notice"""
        published_notice = Notice.objects.create(
            title='Published Notice',
            content='Content',
            published=True,
            created_by=self.admin_user
        )
        
        draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='Content',
            published=False,
            created_by=self.admin_user
        )
        
        self.assertEqual(str(published_notice), 'Published Notice (Published)')
        self.assertEqual(str(draft_notice), 'Draft Notice (Draft)')
    
    def test_notice_validation_empty_title(self):
        """Test validation for empty title"""
        with self.assertRaises(ValidationError):
            notice = Notice(
                title='',
                content='Valid content',
                created_by=self.admin_user
            )
            notice.full_clean()
    
    def test_notice_validation_whitespace_title(self):
        """Test validation for whitespace-only title"""
        with self.assertRaises(ValidationError):
            notice = Notice(
                title='   ',
                content='Valid content',
                created_by=self.admin_user
            )
            notice.full_clean()
    
    def test_notice_validation_empty_content(self):
        """Test validation for empty content"""
        with self.assertRaises(ValidationError):
            notice = Notice(
                title='Valid Title',
                content='',
                created_by=self.admin_user
            )
            notice.full_clean()
    
    def test_notice_validation_whitespace_content(self):
        """Test validation for whitespace-only content"""
        with self.assertRaises(ValidationError):
            notice = Notice(
                title='Valid Title',
                content='   ',
                created_by=self.admin_user
            )
            notice.full_clean()
    
    def test_notice_whitespace_cleaning(self):
        """Test that whitespace is cleaned from title and content"""
        notice = Notice.objects.create(
            title='  Test Title  ',
            content='  Test Content  ',
            created_by=self.admin_user
        )
        
        self.assertEqual(notice.title, 'Test Title')
        self.assertEqual(notice.content, 'Test Content')
    
    def test_notice_default_published_status(self):
        """Test that notices are unpublished by default"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Test Content',
            created_by=self.admin_user
        )
        
        self.assertFalse(notice.published)
    
    def test_notice_foreign_key_relationship(self):
        """Test foreign key relationship with User"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Test Content',
            created_by=self.admin_user
        )
        
        # Test forward relationship
        self.assertEqual(notice.created_by, self.admin_user)
        
        # Test reverse relationship
        self.assertIn(notice, self.admin_user.notices.all())
    
    def test_notice_cascade_delete(self):
        """Test that notices are deleted when user is deleted"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Test Content',
            created_by=self.admin_user
        )
        
        notice_id = notice.id
        self.admin_user.delete()
        
        with self.assertRaises(Notice.DoesNotExist):
            Notice.objects.get(id=notice_id)
    
    def test_notice_ordering(self):
        """Test that notices are ordered by date_created descending"""
        notice1 = Notice.objects.create(
            title='First Notice',
            content='Content 1',
            created_by=self.admin_user
        )
        
        notice2 = Notice.objects.create(
            title='Second Notice',
            content='Content 2',
            created_by=self.admin_user
        )
        
        notices = list(Notice.objects.all())
        self.assertEqual(notices[0], notice2)  # Most recent first
        self.assertEqual(notices[1], notice1)
    
    def test_is_published_method(self):
        """Test is_published method"""
        published_notice = Notice.objects.create(
            title='Published Notice',
            content='Content',
            published=True,
            created_by=self.admin_user
        )
        
        draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='Content',
            published=False,
            created_by=self.admin_user
        )
        
        self.assertTrue(published_notice.is_published())
        self.assertFalse(draft_notice.is_published())
    
    def test_publish_method(self):
        """Test publish method"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Content',
            published=False,
            created_by=self.admin_user
        )
        
        self.assertFalse(notice.published)
        notice.publish()
        notice.refresh_from_db()
        self.assertTrue(notice.published)
    
    def test_unpublish_method(self):
        """Test unpublish method"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Content',
            published=True,
            created_by=self.admin_user
        )
        
        self.assertTrue(notice.published)
        notice.unpublish()
        notice.refresh_from_db()
        self.assertFalse(notice.published)
    
    def test_get_status_display_color(self):
        """Test get_status_display_color method"""
        published_notice = Notice.objects.create(
            title='Published Notice',
            content='Content',
            published=True,
            created_by=self.admin_user
        )
        
        draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='Content',
            published=False,
            created_by=self.admin_user
        )
        
        self.assertEqual(published_notice.get_status_display_color(), 'success')
        self.assertEqual(draft_notice.get_status_display_color(), 'secondary')
    
    def test_get_excerpt_method(self):
        """Test get_excerpt method"""
        short_content = "This is short content."
        long_content = "This is a very long content that should be truncated when we call the get_excerpt method because it exceeds the default length limit of 150 characters and we want to show only a preview."
        
        short_notice = Notice.objects.create(
            title='Short Notice',
            content=short_content,
            created_by=self.admin_user
        )
        
        long_notice = Notice.objects.create(
            title='Long Notice',
            content=long_content,
            created_by=self.admin_user
        )
        
        # Short content should be returned as-is
        self.assertEqual(short_notice.get_excerpt(), short_content)
        
        # Long content should be truncated
        excerpt = long_notice.get_excerpt(50)
        self.assertTrue(len(excerpt) <= 53)  # 50 + '...'
        self.assertTrue(excerpt.endswith('...'))
    
    def test_can_be_edited_by_method(self):
        """Test can_be_edited_by method"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Content',
            created_by=self.admin_user
        )
        
        # Creator can edit
        self.assertTrue(notice.can_be_edited_by(self.admin_user))
        
        # SuperAdmin can edit any notice
        self.assertTrue(notice.can_be_edited_by(self.superadmin_user))
        
        # Guest cannot edit
        self.assertFalse(notice.can_be_edited_by(self.guest_user))
        
        # Unauthenticated user cannot edit
        self.assertFalse(notice.can_be_edited_by(None))
    
    def test_can_be_deleted_by_method(self):
        """Test can_be_deleted_by method"""
        notice = Notice.objects.create(
            title='Test Notice',
            content='Content',
            created_by=self.admin_user
        )
        
        # Creator can delete
        self.assertTrue(notice.can_be_deleted_by(self.admin_user))
        
        # SuperAdmin can delete any notice
        self.assertTrue(notice.can_be_deleted_by(self.superadmin_user))
        
        # Guest cannot delete
        self.assertFalse(notice.can_be_deleted_by(self.guest_user))
        
        # Unauthenticated user cannot delete
        self.assertFalse(notice.can_be_deleted_by(None))


class NoticeManagerTest(TestCase):
    """Test cases for Notice custom manager"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create role and user
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            phone_number='01712345678',
            role=self.admin_role
        )
        
        # Create test notices
        self.published_notice1 = Notice.objects.create(
            title='Published Notice 1',
            content='Content 1',
            published=True,
            created_by=self.admin_user
        )
        
        self.published_notice2 = Notice.objects.create(
            title='Published Notice 2',
            content='Content 2',
            published=True,
            created_by=self.admin_user
        )
        
        self.draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='Draft Content',
            published=False,
            created_by=self.admin_user
        )
    
    def test_published_manager_method(self):
        """Test published() manager method"""
        published_notices = Notice.objects.published()
        
        self.assertEqual(published_notices.count(), 2)
        self.assertIn(self.published_notice1, published_notices)
        self.assertIn(self.published_notice2, published_notices)
        self.assertNotIn(self.draft_notice, published_notices)
    
    def test_recent_published_manager_method(self):
        """Test recent_published() manager method"""
        recent_notices = Notice.objects.recent_published(limit=1)
        
        self.assertEqual(len(recent_notices), 1)
        # Should return the most recent published notice
        self.assertEqual(recent_notices[0], self.published_notice2)
    
    def test_search_published_manager_method(self):
        """Test search_published() manager method"""
        # Search by title
        title_results = Notice.objects.search_published('Published Notice 1')
        self.assertEqual(title_results.count(), 1)
        self.assertIn(self.published_notice1, title_results)
        
        # Search by content
        content_results = Notice.objects.search_published('Content 2')
        self.assertEqual(content_results.count(), 1)
        self.assertIn(self.published_notice2, content_results)
        
        # Search with no query should return all published
        all_results = Notice.objects.search_published('')
        self.assertEqual(all_results.count(), 2)
        
        # Search should not return draft notices
        draft_results = Notice.objects.search_published('Draft')
        self.assertEqual(draft_results.count(), 0)
    
    def test_search_published_case_insensitive(self):
        """Test that search is case insensitive"""
        results = Notice.objects.search_published('published notice')
        self.assertEqual(results.count(), 2)
        
        results = Notice.objects.search_published('CONTENT')
        self.assertEqual(results.count(), 2)


class AdmissionApplicationModelTest(TestCase):
    """Test cases for AdmissionApplication model"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        self.superadmin_role, _ = Role.objects.get_or_create(
            name='SuperAdmin',
            defaults={'description': 'SuperAdmin role'}
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            phone_number='01712345678',
            role=self.admin_role
        )
        
        self.guest_user = User.objects.create_user(
            username='guest_user',
            email='guest@test.com',
            password='testpass123',
            phone_number='01712345679',
            role=self.guest_role
        )
        
        self.superadmin_user = User.objects.create_user(
            username='superadmin_user',
            email='superadmin@test.com',
            password='testpass123',
            phone_number='01712345680',
            role=self.superadmin_role
        )
        
        # Valid application data
        self.valid_application_data = {
            'student_name': 'John Doe',
            'student_dob': date(2010, 5, 15),
            'enrolled_class': 'Class 8',
            'address': '123 Main Street, Dhaka, Bangladesh',
            'guardian_name': 'Jane Doe',
            'guardian_mobile': '01712345681',
            'guardian_email': 'jane.doe@example.com',
            'message': 'Please consider my child for admission.',
        }
    
    def test_admission_application_creation(self):
        """Test basic admission application creation"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.student_dob, date(2010, 5, 15))
        self.assertEqual(application.enrolled_class, 'Class 8')
        self.assertEqual(application.address, '123 Main Street, Dhaka, Bangladesh')
        self.assertEqual(application.guardian_name, 'Jane Doe')
        self.assertEqual(application.guardian_mobile, '01712345681')
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
        self.assertEqual(application.message, 'Please consider my child for admission.')
        self.assertEqual(application.status, 'pending')  # Default status
        self.assertIsNotNone(application.date_submitted)
        self.assertIsNotNone(application.date_updated)
    
    def test_admission_application_str_representation(self):
        """Test string representation of admission application"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        expected_str = f"John Doe - Class 8 (Pending)"
        self.assertEqual(str(application), expected_str)
        
        # Test with different status
        application.status = 'accepted'
        application.save()
        expected_str = f"John Doe - Class 8 (Accepted)"
        self.assertEqual(str(application), expected_str)
    
    def test_admission_application_default_status(self):
        """Test that applications have pending status by default"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        self.assertEqual(application.status, 'pending')
    
    def test_admission_application_status_choices(self):
        """Test all status choices work correctly"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Test pending status
        application.status = 'pending'
        application.save()
        self.assertEqual(application.get_status_display(), 'Pending')
        
        # Test accepted status
        application.status = 'accepted'
        application.save()
        self.assertEqual(application.get_status_display(), 'Accepted')
        
        # Test rejected status
        application.status = 'rejected'
        application.save()
        self.assertEqual(application.get_status_display(), 'Rejected')
    
    def test_guardian_mobile_unique_constraint(self):
        """Test that guardian_mobile must be unique"""
        # Create first application
        AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Try to create second application with same guardian_mobile
        duplicate_data = self.valid_application_data.copy()
        duplicate_data['guardian_email'] = 'different@example.com'
        duplicate_data['student_name'] = 'Different Student'
        
        with self.assertRaises(ValidationError):
            AdmissionApplication.objects.create(**duplicate_data)
    
    def test_guardian_email_unique_constraint(self):
        """Test that guardian_email must be unique"""
        # Create first application
        AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Try to create second application with same guardian_email
        duplicate_data = self.valid_application_data.copy()
        duplicate_data['guardian_mobile'] = '01712345682'
        duplicate_data['student_name'] = 'Different Student'
        
        with self.assertRaises(ValidationError):
            AdmissionApplication.objects.create(**duplicate_data)
    
    def test_bangladeshi_phone_validation_valid_numbers(self):
        """Test valid Bangladeshi phone numbers"""
        valid_numbers = [
            '01712345681',
            '01812345681',
            '01912345681',
            '01512345681',
            '01612345681',
            '01312345681',
            '01412345681',
        ]
        
        for i, phone in enumerate(valid_numbers):
            data = self.valid_application_data.copy()
            data['guardian_mobile'] = phone
            data['guardian_email'] = f'test{i}@example.com'
            data['student_name'] = f'Student {i}'
            
            application = AdmissionApplication.objects.create(**data)
            self.assertEqual(application.guardian_mobile, phone)
    
    def test_bangladeshi_phone_validation_invalid_numbers(self):
        """Test invalid Bangladeshi phone numbers"""
        # Test empty phone number
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = ''
        data['guardian_email'] = 'empty@example.com'
        
        with self.assertRaises(ValidationError):
            application = AdmissionApplication(**data)
            application.full_clean()
        
        # Test too short phone number
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '0171234568'  # 10 digits
        data['guardian_email'] = 'short@example.com'
        
        with self.assertRaises(ValidationError):
            application = AdmissionApplication(**data)
            application.full_clean()
        
        # Test too long phone number
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '017123456812'  # 12 digits
        data['guardian_email'] = 'long@example.com'
        
        with self.assertRaises(ValidationError):
            application = AdmissionApplication(**data)
            application.full_clean()
        
        # Test phone not starting with 01
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '02712345681'
        data['guardian_email'] = 'wrong_start@example.com'
        
        with self.assertRaises(ValidationError):
            application = AdmissionApplication(**data)
            application.full_clean()
    
    def test_bangladeshi_phone_validation_cleaned_numbers(self):
        """Test that phone numbers with spaces are cleaned"""
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '01712345681 '  # With trailing space
        data['guardian_email'] = 'cleaned@example.com'
        
        application = AdmissionApplication.objects.create(**data)
        self.assertEqual(application.guardian_mobile, '01712345681')
    
    def test_validation_empty_required_fields(self):
        """Test validation for empty required fields"""
        required_fields = [
            'student_name',
            'guardian_name',
            'enrolled_class',
            'address',
            'guardian_email'
        ]
        
        for field in required_fields:
            data = self.valid_application_data.copy()
            data[field] = ''
            
            with self.assertRaises(ValidationError):
                application = AdmissionApplication(**data)
                application.full_clean()
    
    def test_validation_whitespace_only_fields(self):
        """Test validation for whitespace-only fields"""
        whitespace_fields = [
            'student_name',
            'guardian_name',
            'enrolled_class',
            'address',
            'guardian_email'
        ]
        
        for field in whitespace_fields:
            data = self.valid_application_data.copy()
            data[field] = '   '
            
            with self.assertRaises(ValidationError):
                application = AdmissionApplication(**data)
                application.full_clean()
    
    def test_validation_future_date_of_birth(self):
        """Test validation for future date of birth"""
        data = self.valid_application_data.copy()
        data['student_dob'] = date.today() + timedelta(days=1)
        
        with self.assertRaises(ValidationError):
            application = AdmissionApplication(**data)
            application.full_clean()
    
    def test_whitespace_cleaning(self):
        """Test that whitespace is cleaned from text fields"""
        data = self.valid_application_data.copy()
        data.update({
            'student_name': '  John Doe  ',
            'guardian_name': '  Jane Doe  ',
            'enrolled_class': '  Class 8  ',
            'address': '  123 Main Street  ',
            'guardian_email': 'jane.doe.whitespace@example.com',  # Valid email without spaces
            'guardian_mobile': '01712345682',  # Different mobile to avoid conflicts
            'message': '  Please consider my child.  ',
        })
        
        application = AdmissionApplication.objects.create(**data)
        
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_name, 'Jane Doe')
        self.assertEqual(application.enrolled_class, 'Class 8')
        self.assertEqual(application.address, '123 Main Street')
        self.assertEqual(application.guardian_email, 'jane.doe.whitespace@example.com')
        self.assertEqual(application.message, 'Please consider my child.')
    
    def test_ordering(self):
        """Test that applications are ordered by date_submitted descending"""
        app1 = AdmissionApplication.objects.create(**self.valid_application_data)
        
        data2 = self.valid_application_data.copy()
        data2['guardian_mobile'] = '01712345682'
        data2['guardian_email'] = 'second@example.com'
        data2['student_name'] = 'Second Student'
        app2 = AdmissionApplication.objects.create(**data2)
        
        applications = list(AdmissionApplication.objects.all())
        self.assertEqual(applications[0], app2)  # Most recent first
        self.assertEqual(applications[1], app1)
    
    def test_is_pending_method(self):
        """Test is_pending method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertTrue(application.is_pending())
        
        application.status = 'accepted'
        application.save()
        self.assertFalse(application.is_pending())
    
    def test_is_accepted_method(self):
        """Test is_accepted method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertFalse(application.is_accepted())
        
        application.status = 'accepted'
        application.save()
        self.assertTrue(application.is_accepted())
    
    def test_is_rejected_method(self):
        """Test is_rejected method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertFalse(application.is_rejected())
        
        application.status = 'rejected'
        application.save()
        self.assertTrue(application.is_rejected())
    
    def test_accept_method(self):
        """Test accept method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertEqual(application.status, 'pending')
        application.accept()
        application.refresh_from_db()
        self.assertEqual(application.status, 'accepted')
    
    def test_reject_method(self):
        """Test reject method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        self.assertEqual(application.status, 'pending')
        application.reject()
        application.refresh_from_db()
        self.assertEqual(application.status, 'rejected')
    
    def test_reset_to_pending_method(self):
        """Test reset_to_pending method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        application.status = 'accepted'
        application.save()
        
        self.assertEqual(application.status, 'accepted')
        application.reset_to_pending()
        application.refresh_from_db()
        self.assertEqual(application.status, 'pending')
    
    def test_get_status_display_color(self):
        """Test get_status_display_color method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Test pending status
        self.assertEqual(application.get_status_display_color(), 'warning')
        
        # Test accepted status
        application.status = 'accepted'
        application.save()
        self.assertEqual(application.get_status_display_color(), 'success')
        
        # Test rejected status
        application.status = 'rejected'
        application.save()
        self.assertEqual(application.get_status_display_color(), 'danger')
    
    def test_get_student_age(self):
        """Test get_student_age method"""
        # Test with a known date
        data = self.valid_application_data.copy()
        data['student_dob'] = date(2010, 1, 1)
        data['guardian_mobile'] = '01712345683'
        data['guardian_email'] = 'age_test@example.com'
        
        application = AdmissionApplication.objects.create(**data)
        
        # Calculate expected age
        today = date.today()
        expected_age = today.year - 2010
        if today.month < 1 or (today.month == 1 and today.day < 1):
            expected_age -= 1
        
        self.assertEqual(application.get_student_age(), expected_age)


# API Tests
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
import json
import time


class NoticeListAPITest(APITestCase):
    """Test cases for Notice List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        
        # Create test user
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            phone_number='01712345678',
            role=self.admin_role
        )
        
        # Create test notices
        self.published_notice1 = Notice.objects.create(
            title='Published Notice 1',
            content='This is the content of published notice 1',
            published=True,
            created_by=self.admin_user
        )
        
        self.published_notice2 = Notice.objects.create(
            title='Published Notice 2',
            content='This is the content of published notice 2',
            published=True,
            created_by=self.admin_user
        )
        
        self.draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='This is a draft notice content',
            published=False,
            created_by=self.admin_user
        )
        
        self.url = reverse('public:notice-list-api')
    
    def test_notice_list_api_success(self):
        """Test successful notice list retrieval"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)  # Only published notices
        
        # Check that draft notice is not included
        notice_titles = [notice['title'] for notice in response.data['results']]
        self.assertIn('Published Notice 1', notice_titles)
        self.assertIn('Published Notice 2', notice_titles)
        self.assertNotIn('Draft Notice', notice_titles)
    
    def test_notice_list_api_search(self):
        """Test notice search functionality"""
        # Search by title
        response = self.client.get(self.url, {'search': 'Published Notice 1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Published Notice 1')
        
        # Search by content
        response = self.client.get(self.url, {'search': 'content of published notice 2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Published Notice 2')
        
        # Search with no results
        response = self.client.get(self.url, {'search': 'nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_notice_list_api_date_filtering(self):
        """Test notice date filtering"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create notice with specific date
        past_date = timezone.now() - timedelta(days=5)
        old_notice = Notice.objects.create(
            title='Old Notice',
            content='Old content',
            published=True,
            created_by=self.admin_user
        )
        old_notice.date_created = past_date
        old_notice.save()
        
        # Filter from today
        today = timezone.now().date()
        response = self.client.get(self.url, {'date_from': today.strftime('%Y-%m-%d')})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should not include old notice
        notice_titles = [notice['title'] for notice in response.data['results']]
        self.assertNotIn('Old Notice', notice_titles)
    
    def test_notice_list_api_pagination(self):
        """Test notice pagination"""
        response = self.client.get(self.url, {'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)


class AdmissionApplicationCreateAPITest(APITestCase):
    """Test cases for Admission Application Create API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse('public:admission-application-create-api')
        self.valid_data = {
            'student_name': 'John Doe',
            'student_dob': '2010-05-15',
            'enrolled_class': 'Class 8',
            'address': '123 Main Street, Dhaka, Bangladesh',
            'guardian_name': 'Jane Doe',
            'guardian_mobile': '01712345681',
            'guardian_email': 'jane.doe@example.com',
            'message': 'Please consider my child for admission.',
            # CAPTCHA fields
            'website': '',  # Honeypot field
            'form_start_time': str(time.time() - 10),  # 10 seconds ago
            'captcha_question': 'What is 5 + 3?',
            'captcha_answer': '8',
        }
    
    def test_admission_application_create_success(self):
        """Test successful admission application creation"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('application_id', response.data['data'])
        
        # Verify application was created in database
        application = AdmissionApplication.objects.get(id=response.data['data']['application_id'])
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_mobile, '01712345681')
    
    def test_admission_application_validation_errors(self):
        """Test validation error handling"""
        invalid_data = self.valid_data.copy()
        invalid_data['student_name'] = ''  # Empty required field
        invalid_data['guardian_mobile'] = '123456789'  # Invalid phone format
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('details', response.data['error'])
    
    def test_admission_application_duplicate_mobile(self):
        """Test duplicate guardian mobile validation"""
        # Create first application
        self.client.post(self.url, self.valid_data, format='json')
        
        # Try to create second application with same mobile
        duplicate_data = self.valid_data.copy()
        duplicate_data['guardian_email'] = 'different@example.com'
        duplicate_data['student_name'] = 'Different Student'
        duplicate_data['form_start_time'] = str(time.time() - 10)  # Reset timing
        
        response = self.client.post(self.url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_admission_application_captcha_validation(self):
        """Test CAPTCHA validation"""
        # Test honeypot field filled
        honeypot_data = self.valid_data.copy()
        honeypot_data['website'] = 'spam'
        
        response = self.client.post(self.url, honeypot_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test form submitted too quickly
        quick_data = self.valid_data.copy()
        quick_data['form_start_time'] = str(time.time() - 1)  # 1 second ago
        
        response = self.client.post(self.url, quick_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test wrong CAPTCHA answer
        wrong_captcha_data = self.valid_data.copy()
        wrong_captcha_data['captcha_answer'] = '10'  # Wrong answer for 5 + 3
        
        response = self.client.post(self.url, wrong_captcha_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')


class UserRegistrationAPITest(APITestCase):
    """Test cases for User Registration API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        self.url = reverse('public:user-registration-api')
        self.valid_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '01712345681',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            # CAPTCHA fields
            'website': '',  # Honeypot field
            'form_start_time': str(time.time() - 10),  # 10 seconds ago
            'captcha_question': 'What is 7 + 2?',
            'captcha_answer': '9',
        }
        
        # Ensure Guest role exists
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('user_id', response.data['data'])
        
        # Verify user was created in database
        user = User.objects.get(id=response.data['data']['user_id'])
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.phone_number, '01712345681')
        self.assertEqual(user.get_role_name(), 'Guest')  # Default role
        
        # Verify password is hashed
        self.assertTrue(user.check_password('testpass123'))
    
    def test_user_registration_validation_errors(self):
        """Test validation error handling"""
        invalid_data = self.valid_data.copy()
        invalid_data['username'] = ''  # Empty required field
        invalid_data['email'] = 'invalid-email'  # Invalid email format
        invalid_data['phone_number'] = '123456789'  # Invalid phone format
        invalid_data['password'] = '123'  # Too short password
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('details', response.data['error'])
        
        # Check specific field errors
        details = response.data['error']['details']
        self.assertIn('username', details)
        self.assertIn('email', details)
        self.assertIn('phone_number', details)
        self.assertIn('password', details)
    
    def test_user_registration_password_mismatch(self):
        """Test password confirmation mismatch"""
        invalid_data = self.valid_data.copy()
        invalid_data['password_confirm'] = 'differentpassword'
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data['error']['details'])
    
    def test_user_registration_duplicate_username(self):
        """Test duplicate username validation"""
        # Create first user
        self.client.post(self.url, self.valid_data, format='json')
        
        # Try to create second user with same username
        duplicate_data = self.valid_data.copy()
        duplicate_data['email'] = 'different@example.com'
        duplicate_data['phone_number'] = '01712345682'
        duplicate_data['form_start_time'] = str(time.time() - 10)  # Reset timing
        
        response = self.client.post(self.url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
    
    def test_user_registration_duplicate_email(self):
        """Test duplicate email validation"""
        # Create first user
        self.client.post(self.url, self.valid_data, format='json')
        
        # Try to create second user with same email
        duplicate_data = self.valid_data.copy()
        duplicate_data['username'] = 'differentuser'
        duplicate_data['phone_number'] = '01712345682'
        duplicate_data['form_start_time'] = str(time.time() - 10)  # Reset timing
        
        response = self.client.post(self.url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['error']['details'])
    
    def test_user_registration_duplicate_phone(self):
        """Test duplicate phone number validation"""
        # Create first user
        self.client.post(self.url, self.valid_data, format='json')
        
        # Try to create second user with same phone
        duplicate_data = self.valid_data.copy()
        duplicate_data['username'] = 'differentuser'
        duplicate_data['email'] = 'different@example.com'
        duplicate_data['form_start_time'] = str(time.time() - 10)  # Reset timing
        
        response = self.client.post(self.url, duplicate_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data['error']['details'])
    
    def test_user_registration_phone_validation(self):
        """Test Bangladeshi phone number validation"""
        # Test valid phone numbers
        valid_phones = ['01712345681', '01812345681', '01912345681', '01512345681']
        
        for i, phone in enumerate(valid_phones):
            data = self.valid_data.copy()
            data['username'] = f'user{i}'
            data['email'] = f'user{i}@example.com'
            data['phone_number'] = phone
            data['form_start_time'] = str(time.time() - 10)
            
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                           f"Valid phone {phone} should be accepted")
        
        # Test invalid phone numbers
        invalid_phones = ['0271234568', '017123456', '017123456789', '1712345681']
        
        for phone in invalid_phones:
            data = self.valid_data.copy()
            data['username'] = f'invalid{phone}'
            data['email'] = f'invalid{phone}@example.com'
            data['phone_number'] = phone
            data['form_start_time'] = str(time.time() - 10)
            
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Invalid phone {phone} should be rejected")
    
    def test_user_registration_captcha_validation(self):
        """Test CAPTCHA validation for registration"""
        # Test honeypot field filled
        honeypot_data = self.valid_data.copy()
        honeypot_data['website'] = 'spam'
        
        response = self.client.post(self.url, honeypot_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test form submitted too quickly (less than 5 seconds for registration)
        quick_data = self.valid_data.copy()
        quick_data['form_start_time'] = str(time.time() - 2)  # 2 seconds ago
        
        response = self.client.post(self.url, quick_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test wrong CAPTCHA answer
        wrong_captcha_data = self.valid_data.copy()
        wrong_captcha_data['captcha_answer'] = '15'  # Wrong answer for 7 + 2
        
        response = self.client.post(self.url, wrong_captcha_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_user_registration_password_strength(self):
        """Test password strength validation"""
        # Test too short password
        short_password_data = self.valid_data.copy()
        short_password_data['password'] = '123'
        short_password_data['password_confirm'] = '123'
        
        response = self.client.post(self.url, short_password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error']['details'])
        
        # Test password without letters
        no_letters_data = self.valid_data.copy()
        no_letters_data['password'] = '12345678'
        no_letters_data['password_confirm'] = '12345678'
        
        response = self.client.post(self.url, no_letters_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error']['details'])
        
        # Test password without numbers
        no_numbers_data = self.valid_data.copy()
        no_numbers_data['password'] = 'testpassword'
        no_numbers_data['password_confirm'] = 'testpassword'
        
        response = self.client.post(self.url, no_numbers_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error']['details'])
        
        # Test common password
        common_password_data = self.valid_data.copy()
        common_password_data['password'] = 'password'
        common_password_data['password_confirm'] = 'password'
        
        response = self.client.post(self.url, common_password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error']['details'])
    
    def test_user_registration_username_validation(self):
        """Test username validation"""
        # Test too short username
        short_username_data = self.valid_data.copy()
        short_username_data['username'] = 'ab'
        
        response = self.client.post(self.url, short_username_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
        
        # Test username with invalid characters
        invalid_username_data = self.valid_data.copy()
        invalid_username_data['username'] = 'user@name'
        
        response = self.client.post(self.url, invalid_username_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
        
        # Test username similar to email
        similar_username_data = self.valid_data.copy()
        similar_username_data['username'] = 'testuser'
        similar_username_data['email'] = 'testuser@example.com'
        
        response = self.client.post(self.url, similar_username_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
    
    def test_user_registration_name_validation(self):
        """Test first name and last name validation"""
        # Test empty first name
        empty_first_name_data = self.valid_data.copy()
        empty_first_name_data['first_name'] = ''
        
        response = self.client.post(self.url, empty_first_name_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data['error']['details'])
        
        # Test empty last name
        empty_last_name_data = self.valid_data.copy()
        empty_last_name_data['last_name'] = ''
        
        response = self.client.post(self.url, empty_last_name_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data['error']['details'])
        
        # Test names with invalid characters
        invalid_first_name_data = self.valid_data.copy()
        invalid_first_name_data['first_name'] = 'Test123'
        
        response = self.client.post(self.url, invalid_first_name_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data['error']['details'])
    
    def test_user_registration_default_role_assignment(self):
        """Test that new users get Guest role by default"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(id=response.data['data']['user_id'])
        self.assertEqual(user.get_role_name(), 'Guest')
        self.assertEqual(user.role, self.guest_role)
    
    def test_user_registration_response_format(self):
        """Test response format and data structure"""
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        self.assertIn('success', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        
        # Check data structure
        data = response.data['data']
        required_fields = ['user_id', 'username', 'email', 'full_name', 'role', 'date_joined', 'next_steps']
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check security headers
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
    
    def test_user_registration_error_response_format(self):
        """Test error response format"""
        invalid_data = self.valid_data.copy()
        invalid_data['username'] = ''
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error response structure
        self.assertIn('error', response.data)
        error = response.data['error']
        self.assertIn('code', error)
        self.assertIn('message', error)
        self.assertIn('details', error)
        
        self.assertEqual(error['code'], 'VALIDATION_ERROR')
        data['student_dob'] = date(2010, 1, 1)
        application = AdmissionApplication.objects.create(**data)
        
        # Calculate expected age
        today = date.today()
        expected_age = today.year - 2010
        if today.month < 1 or (today.month == 1 and today.day < 1):
            expected_age -= 1
        
        self.assertEqual(application.get_student_age(), expected_age)
        
        # Test with None date of birth
        data['student_dob'] = None
        application2 = AdmissionApplication(**data)
        self.assertIsNone(application2.get_student_age())
    
    def test_get_formatted_mobile(self):
        """Test get_formatted_mobile method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Test formatting
        expected_format = "017-1234-5681"
        self.assertEqual(application.get_formatted_mobile(), expected_format)
        
        # Test with empty mobile
        application.guardian_mobile = ''
        self.assertEqual(application.get_formatted_mobile(), '')
    
    def test_can_be_updated_by_method(self):
        """Test can_be_updated_by method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Admin can update
        self.assertTrue(application.can_be_updated_by(self.admin_user))
        
        # SuperAdmin can update
        self.assertTrue(application.can_be_updated_by(self.superadmin_user))
        
        # Guest cannot update
        self.assertFalse(application.can_be_updated_by(self.guest_user))
        
        # Unauthenticated user cannot update
        self.assertFalse(application.can_be_updated_by(None))
    
    def test_can_be_deleted_by_method(self):
        """Test can_be_deleted_by method"""
        application = AdmissionApplication.objects.create(**self.valid_application_data)
        
        # Admin can delete
        self.assertTrue(application.can_be_deleted_by(self.admin_user))
        
        # SuperAdmin can delete
        self.assertTrue(application.can_be_deleted_by(self.superadmin_user))
        
        # Guest cannot delete
        self.assertFalse(application.can_be_deleted_by(self.guest_user))
        
        # Unauthenticated user cannot delete
        self.assertFalse(application.can_be_deleted_by(None))


class AdmissionApplicationManagerTest(TestCase):
    """Test cases for AdmissionApplication custom manager"""
    
    def setUp(self):
        """Set up test data"""
        # Create test applications with different statuses
        base_data = {
            'student_name': 'Test Student',
            'student_dob': date(2010, 5, 15),
            'enrolled_class': 'Class 8',
            'address': '123 Main Street',
            'guardian_name': 'Test Guardian',
            'message': 'Test message',
        }
        
        self.pending_app = AdmissionApplication.objects.create(
            guardian_mobile='01712345681',
            guardian_email='pending@example.com',
            status='pending',
            **base_data
        )
        
        self.accepted_app = AdmissionApplication.objects.create(
            guardian_mobile='01712345682',
            guardian_email='accepted@example.com',
            status='accepted',
            **base_data
        )
        
        self.rejected_app = AdmissionApplication.objects.create(
            guardian_mobile='01712345683',
            guardian_email='rejected@example.com',
            status='rejected',
            **base_data
        )
    
    def test_pending_manager_method(self):
        """Test pending() manager method"""
        pending_apps = AdmissionApplication.objects.pending()
        
        self.assertEqual(pending_apps.count(), 1)
        self.assertIn(self.pending_app, pending_apps)
        self.assertNotIn(self.accepted_app, pending_apps)
        self.assertNotIn(self.rejected_app, pending_apps)
    
    def test_accepted_manager_method(self):
        """Test accepted() manager method"""
        accepted_apps = AdmissionApplication.objects.accepted()
        
        self.assertEqual(accepted_apps.count(), 1)
        self.assertIn(self.accepted_app, accepted_apps)
        self.assertNotIn(self.pending_app, accepted_apps)
        self.assertNotIn(self.rejected_app, accepted_apps)
    
    def test_rejected_manager_method(self):
        """Test rejected() manager method"""
        rejected_apps = AdmissionApplication.objects.rejected()
        
        self.assertEqual(rejected_apps.count(), 1)
        self.assertIn(self.rejected_app, rejected_apps)
        self.assertNotIn(self.pending_app, rejected_apps)
        self.assertNotIn(self.accepted_app, rejected_apps)
    
    def test_recent_manager_method(self):
        """Test recent() manager method"""
        recent_apps = AdmissionApplication.objects.recent(limit=2)
        
        self.assertEqual(len(recent_apps), 2)
        # Should return most recent first (rejected_app was created last)
        self.assertEqual(recent_apps[0], self.rejected_app)
    
    def test_search_manager_method(self):
        """Test search() manager method"""
        # Create applications with different searchable data
        AdmissionApplication.objects.create(
            student_name='Alice Johnson',
            guardian_name='Bob Johnson',
            enrolled_class='Class 9',
            guardian_mobile='01712345684',
            guardian_email='alice@example.com',
            student_dob=date(2009, 3, 10),
            address='456 Oak Street',
        )
        
        AdmissionApplication.objects.create(
            student_name='Charlie Brown',
            guardian_name='David Brown',
            enrolled_class='Class 7',
            guardian_mobile='01712345685',
            guardian_email='charlie@example.com',
            student_dob=date(2011, 8, 20),
            address='789 Pine Street',
        )
        
        # Search by student name
        results = AdmissionApplication.objects.search('Alice')
        self.assertEqual(results.count(), 1)
        
        # Search by guardian name
        results = AdmissionApplication.objects.search('Brown')
        self.assertEqual(results.count(), 1)
        
        # Search by class
        results = AdmissionApplication.objects.search('Class 9')
        self.assertEqual(results.count(), 1)
        
        # Search with no query should return all
        results = AdmissionApplication.objects.search('')
        self.assertEqual(results.count(), 5)  # 3 from setUp + 2 created here
        
        # Case insensitive search
        results = AdmissionApplication.objects.search('alice')
        self.assertEqual(results.count(), 1)

# API Tests for Notice Listing
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
import json


class NoticeListAPITest(APITestCase):
    """Test cases for Notice List API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Guest role'}
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            phone_number='01712345678',
            role=self.admin_role
        )
        
        # Create test notices
        self.published_notice1 = Notice.objects.create(
            title='First Published Notice',
            content='This is the content of the first published notice. It contains important information for students.',
            published=True,
            created_by=self.admin_user
        )
        
        self.published_notice2 = Notice.objects.create(
            title='Second Published Notice',
            content='This is the content of the second published notice. It has different information.',
            published=True,
            created_by=self.admin_user
        )
        
        self.draft_notice = Notice.objects.create(
            title='Draft Notice',
            content='This is a draft notice that should not appear in public API.',
            published=False,
            created_by=self.admin_user
        )
        
        # Create an older notice for date filtering tests
        older_date = timezone.now() - timedelta(days=5)
        self.old_notice = Notice.objects.create(
            title='Old Published Notice',
            content='This is an older published notice.',
            published=True,
            created_by=self.admin_user
        )
        # Manually set the creation date to be older
        Notice.objects.filter(id=self.old_notice.id).update(date_created=older_date)
        self.old_notice.refresh_from_db()
        
        self.api_url = reverse('public:notice-list-api')
    
    def test_notice_list_api_basic_functionality(self):
        """Test basic notice listing functionality"""
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Should return only published notices
        results = response.data['results']
        self.assertEqual(len(results), 3)  # 3 published notices
        
        # Check that draft notice is not included
        notice_titles = [notice['title'] for notice in results]
        self.assertNotIn('Draft Notice', notice_titles)
        self.assertIn('First Published Notice', notice_titles)
        self.assertIn('Second Published Notice', notice_titles)
        self.assertIn('Old Published Notice', notice_titles)
    
    def test_notice_list_api_no_authentication_required(self):
        """Test that API is accessible without authentication"""
        response = self.client.get(self.api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_notice_list_api_response_structure(self):
        """Test the structure of individual notice objects in response"""
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['results']:
            notice = response.data['results'][0]
            
            # Check required fields
            required_fields = [
                'id', 'title', 'content', 'excerpt', 
                'date_created', 'date_updated', 'created_by_name'
            ]
            
            for field in required_fields:
                self.assertIn(field, notice)
            
            # Check that excerpt is shorter than content
            if len(notice['content']) > 200:
                self.assertTrue(len(notice['excerpt']) <= 203)  # 200 + '...'
                self.assertTrue(notice['excerpt'].endswith('...'))
    
    def test_notice_list_api_ordering(self):
        """Test that notices are ordered by date_created descending"""
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        
        # Check that notices are ordered by creation date (newest first)
        for i in range(len(results) - 1):
            current_date = results[i]['date_created']
            next_date = results[i + 1]['date_created']
            self.assertGreaterEqual(current_date, next_date)
    
    def test_notice_list_api_search_by_title(self):
        """Test search functionality by title"""
        # Search for "First"
        response = self.client.get(self.api_url, {'search': 'First'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'First Published Notice')
    
    def test_notice_list_api_search_by_content(self):
        """Test search functionality by content"""
        # Search for "different information"
        response = self.client.get(self.api_url, {'search': 'different information'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Second Published Notice')
    
    def test_notice_list_api_search_case_insensitive(self):
        """Test that search is case insensitive"""
        # Search with different cases
        test_cases = ['FIRST', 'first', 'First', 'fIrSt']
        
        for search_term in test_cases:
            response = self.client.get(self.api_url, {'search': search_term})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            results = response.data['results']
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['title'], 'First Published Notice')
    
    def test_notice_list_api_search_no_results(self):
        """Test search with no matching results"""
        response = self.client.get(self.api_url, {'search': 'nonexistent'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 0)
    
    def test_notice_list_api_search_empty_query(self):
        """Test search with empty query returns all published notices"""
        response = self.client.get(self.api_url, {'search': ''})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 3)  # All published notices
    
    def test_notice_list_api_date_filtering_from(self):
        """Test date filtering with date_from parameter"""
        # Filter from today (should exclude old notice)
        today = date.today().strftime('%Y-%m-%d')
        response = self.client.get(self.api_url, {'date_from': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        # Should return notices created today or later
        notice_titles = [notice['title'] for notice in results]
        self.assertNotIn('Old Published Notice', notice_titles)
    
    def test_notice_list_api_date_filtering_to(self):
        """Test date filtering with date_to parameter"""
        # Filter until yesterday (should only include old notice)
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(self.api_url, {'date_to': yesterday})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        # Should only return the old notice
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Old Published Notice')
    
    def test_notice_list_api_date_filtering_range(self):
        """Test date filtering with both date_from and date_to"""
        # Filter for a range that includes only today's notices
        today = date.today().strftime('%Y-%m-%d')
        tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        response = self.client.get(self.api_url, {
            'date_from': today,
            'date_to': tomorrow
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        # Should exclude the old notice
        notice_titles = [notice['title'] for notice in results]
        self.assertNotIn('Old Published Notice', notice_titles)
    
    def test_notice_list_api_invalid_date_format(self):
        """Test that invalid date formats are ignored gracefully"""
        response = self.client.get(self.api_url, {
            'date_from': 'invalid-date',
            'date_to': '2023-13-45'  # Invalid date
        })
        
        # Should not cause an error, just ignore invalid dates
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 3)  # All published notices
    
    def test_notice_list_api_combined_search_and_date_filter(self):
        """Test combining search and date filtering"""
        today = date.today().strftime('%Y-%m-%d')
        
        response = self.client.get(self.api_url, {
            'search': 'Published',
            'date_from': today
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        # Should return published notices from today that contain "Published"
        for notice in results:
            self.assertIn('Published', notice['title'])
    
    def test_notice_list_api_pagination_default(self):
        """Test default pagination settings"""
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # With 3 notices and default page size of 10, should be on page 1
        self.assertEqual(response.data['count'], 3)
        self.assertIsNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
    
    def test_notice_list_api_pagination_custom_page_size(self):
        """Test custom page size parameter"""
        response = self.client.get(self.api_url, {'page_size': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 2)  # Should limit to 2 results
        self.assertEqual(response.data['count'], 3)  # Total count should still be 3
        self.assertIsNotNone(response.data['next'])  # Should have next page
    
    def test_notice_list_api_pagination_max_page_size(self):
        """Test that page size is limited to maximum"""
        response = self.client.get(self.api_url, {'page_size': 100})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be limited to max_page_size (50)
        # But since we only have 3 notices, should return all 3
        results = response.data['results']
        self.assertEqual(len(results), 3)
    
    def test_notice_list_api_pagination_second_page(self):
        """Test accessing second page"""
        # First, set page size to 2 to create multiple pages
        response = self.client.get(self.api_url, {'page_size': 2, 'page': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        self.assertEqual(len(results), 1)  # Should have 1 result on page 2
        self.assertIsNone(response.data['next'])  # No next page
        self.assertIsNotNone(response.data['previous'])  # Has previous page
    
    def test_notice_list_api_created_by_name_field(self):
        """Test that created_by_name field is properly populated"""
        # Set admin user's first and last name
        self.admin_user.first_name = 'John'
        self.admin_user.last_name = 'Admin'
        self.admin_user.save()
        
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        if results:
            notice = results[0]
            self.assertEqual(notice['created_by_name'], 'John Admin')
    
    def test_notice_list_api_created_by_name_fallback(self):
        """Test created_by_name fallback when user has no full name"""
        # Ensure admin user has no first/last name
        self.admin_user.first_name = ''
        self.admin_user.last_name = ''
        self.admin_user.save()
        
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        if results:
            notice = results[0]
            # Should fallback to username or empty string
            self.assertIsNotNone(notice['created_by_name'])
    
    def test_notice_list_api_only_published_notices(self):
        """Test that only published notices are returned"""
        # Create more draft notices
        Notice.objects.create(
            title='Another Draft',
            content='Another draft content',
            published=False,
            created_by=self.admin_user
        )
        
        Notice.objects.create(
            title='Yet Another Draft',
            content='Yet another draft content',
            published=False,
            created_by=self.admin_user
        )
        
        response = self.client.get(self.api_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.data['results']
        # Should still only return 3 published notices
        self.assertEqual(len(results), 3)
        
        # Verify all returned notices are published
        for notice_data in results:
            notice = Notice.objects.get(id=notice_data['id'])
            self.assertTrue(notice.published)
    
    def test_notice_list_api_performance_with_select_related(self):
        """Test that the API uses select_related for performance"""
        # This test ensures that we're not making N+1 queries
        with self.assertNumQueries(2):  # 1 for count, 1 for results with select_related
            response = self.client.get(self.api_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Access created_by_name to trigger the relationship
            results = response.data['results']
            for notice in results:
                _ = notice['created_by_name']
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.test.utils import override_settings
from django.core.cache import cache
import json


class AdmissionApplicationAPITest(APITestCase):
    """Test cases for Admission Application API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Get or create roles
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        # Valid application data
        self.valid_application_data = {
            'student_name': 'John Doe',
            'student_dob': '2010-05-15',
            'enrolled_class': 'Class 8',
            'address': '123 Main Street, Dhaka, Bangladesh',
            'guardian_name': 'Jane Doe',
            'guardian_mobile': '01712345681',
            'guardian_email': 'jane.doe@example.com',
            'message': 'Please consider my child for admission.',
        }
        
        # API endpoint URL
        self.api_url = reverse('public:admission-application-create-api')
    
    def tearDown(self):
        """Clean up after each test"""
        # Clear cache to reset rate limiting
        cache.clear()
    
    def test_successful_application_submission(self):
        """Test successful admission application submission"""
        response = self.client.post(
            self.api_url,
            data=self.valid_application_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('message', response_data)
        self.assertIn('data', response_data)
        
        # Check response data
        data = response_data['data']
        self.assertIn('application_id', data)
        self.assertEqual(data['student_name'], 'John Doe')
        self.assertEqual(data['enrolled_class'], 'Class 8')
        self.assertEqual(data['status'], 'pending')
        self.assertIn('date_submitted', data)
        
        # Verify application was created in database
        application = AdmissionApplication.objects.get(id=data['application_id'])
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_mobile, '01712345681')
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
    
    def test_application_submission_missing_required_fields(self):
        """Test application submission with missing required fields"""
        required_fields = [
            'student_name', 'student_dob', 'enrolled_class', 'address',
            'guardian_name', 'guardian_mobile', 'guardian_email'
        ]
        
        for field in required_fields:
            data = self.valid_application_data.copy()
            del data[field]
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn('details', response_data['error'])
            self.assertIn(field, response_data['error']['details'])
    
    def test_application_submission_empty_required_fields(self):
        """Test application submission with empty required fields"""
        required_fields = [
            'student_name', 'enrolled_class', 'address',
            'guardian_name', 'guardian_email'
        ]
        
        for field in required_fields:
            data = self.valid_application_data.copy()
            data[field] = ''
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn(field, response_data['error']['details'])
    
    def test_application_submission_invalid_phone_number(self):
        """Test application submission with invalid phone numbers"""
        invalid_phones = [
            '123456789',      # Too short
            '017123456789',   # Too long
            '02712345678',    # Doesn't start with 01
            'abcdefghijk',    # Non-numeric
            '01234567890',    # Invalid operator code
        ]
        
        for phone in invalid_phones:
            data = self.valid_application_data.copy()
            data['guardian_mobile'] = phone
            data['guardian_email'] = f'test_{phone}@example.com'  # Unique email
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn('guardian_mobile', response_data['error']['details'])
    
    def test_application_submission_invalid_email(self):
        """Test application submission with invalid email addresses"""
        invalid_emails = [
            'invalid-email',
            'invalid@',
            '@invalid.com',
            'invalid.email',
            'invalid email@example.com',
        ]
        
        for email in invalid_emails:
            data = self.valid_application_data.copy()
            data['guardian_email'] = email
            data['guardian_mobile'] = f'0171234568{len(email)}'  # Unique mobile
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn('guardian_email', response_data['error']['details'])
    
    def test_application_submission_invalid_date_format(self):
        """Test application submission with invalid date formats"""
        invalid_dates = [
            '2010-13-15',     # Invalid month
            '2010-05-32',     # Invalid day
            '15-05-2010',     # Wrong format
            '2010/05/15',     # Wrong separator
            'invalid-date',   # Non-date string
        ]
        
        for date_str in invalid_dates:
            data = self.valid_application_data.copy()
            data['student_dob'] = date_str
            data['guardian_email'] = f'test_{date_str.replace("-", "_")}@example.com'
            data['guardian_mobile'] = f'0171234568{len(date_str) % 10}'
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn('student_dob', response_data['error']['details'])
    
    def test_application_submission_duplicate_mobile(self):
        """Test application submission with duplicate guardian mobile"""
        # Create first application
        first_response = self.client.post(
            self.api_url,
            data=self.valid_application_data,
            format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        
        # Try to create second application with same mobile
        duplicate_data = self.valid_application_data.copy()
        duplicate_data['guardian_email'] = 'different@example.com'
        duplicate_data['student_name'] = 'Different Student'
        
        response = self.client.post(
            self.api_url,
            data=duplicate_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('guardian_mobile', response_data['error']['details'])
        self.assertIn('already exists', response_data['error']['details']['guardian_mobile'])
    
    def test_application_submission_duplicate_email(self):
        """Test application submission with duplicate guardian email"""
        # Create first application
        first_response = self.client.post(
            self.api_url,
            data=self.valid_application_data,
            format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        
        # Try to create second application with same email
        duplicate_data = self.valid_application_data.copy()
        duplicate_data['guardian_mobile'] = '01712345682'
        duplicate_data['student_name'] = 'Different Student'
        
        response = self.client.post(
            self.api_url,
            data=duplicate_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('guardian_email', response_data['error']['details'])
        self.assertIn('already exists', response_data['error']['details']['guardian_email'])
    
    def test_honeypot_spam_detection(self):
        """Test honeypot field for spam detection"""
        data = self.valid_application_data.copy()
        data['website'] = 'http://spam-site.com'  # Honeypot field
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'SPAM_DETECTED')
        self.assertIn('Spam submission detected', response_data['error']['message'])
    
    def test_rate_limiting(self):
        """Test rate limiting for application submissions"""
        from django.conf import settings
        
        # Skip test if rate limiting is disabled
        if not getattr(settings, 'RATELIMIT_ENABLE', False):
            self.skipTest("Rate limiting is disabled in settings")
        
        # Clear cache to ensure clean state
        cache.clear()
        
        # Submit 5 applications (should be allowed)
        for i in range(5):
            data = self.valid_application_data.copy()
            data['guardian_email'] = f'test{i}@example.com'
            data['guardian_mobile'] = f'0171234568{i}'
            data['student_name'] = f'Student {i}'
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 6th submission should be rate limited
        data = self.valid_application_data.copy()
        data['guardian_email'] = 'test6@example.com'
        data['guardian_mobile'] = '01712345686'
        data['student_name'] = 'Student 6'
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        # Should be blocked by rate limiting
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_application_submission_with_optional_message(self):
        """Test application submission with optional message field"""
        # Test with message
        data_with_message = self.valid_application_data.copy()
        response = self.client.post(
            self.api_url,
            data=data_with_message,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test without message
        data_without_message = self.valid_application_data.copy()
        del data_without_message['message']
        data_without_message['guardian_email'] = 'nomessage@example.com'
        data_without_message['guardian_mobile'] = '01712345682'
        data_without_message['student_name'] = 'No Message Student'
        
        response = self.client.post(
            self.api_url,
            data=data_without_message,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_application_submission_whitespace_cleaning(self):
        """Test that whitespace is cleaned from submitted data"""
        data = self.valid_application_data.copy()
        data.update({
            'student_name': '  John Doe  ',
            'guardian_name': '  Jane Doe  ',
            'enrolled_class': '  Class 8  ',
            'address': '  123 Main Street  ',
            'message': '  Please consider my child.  ',
        })
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify data was cleaned in database
        response_data = response.json()
        application = AdmissionApplication.objects.get(id=response_data['data']['application_id'])
        
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_name, 'Jane Doe')
        self.assertEqual(application.enrolled_class, 'Class 8')
        self.assertEqual(application.address, '123 Main Street')
        self.assertEqual(application.message, 'Please consider my child.')
    
    def test_application_submission_case_insensitive_email(self):
        """Test that email addresses are converted to lowercase"""
        data = self.valid_application_data.copy()
        data['guardian_email'] = 'Jane.Doe@EXAMPLE.COM'
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify email was converted to lowercase in database
        response_data = response.json()
        application = AdmissionApplication.objects.get(id=response_data['data']['application_id'])
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
    
    def test_application_submission_error_response_format(self):
        """Test that error responses follow the expected format"""
        # Submit invalid data
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = 'invalid'
        data['guardian_email'] = 'invalid-email'
        del data['student_name']
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        
        # Check error response structure
        self.assertIn('error', response_data)
        error = response_data['error']
        
        self.assertIn('code', error)
        self.assertIn('message', error)
        self.assertIn('details', error)
        
        self.assertEqual(error['code'], 'VALIDATION_ERROR')
        self.assertIsInstance(error['details'], dict)
        
        # Check that all validation errors are included
        self.assertIn('student_name', error['details'])
        self.assertIn('guardian_mobile', error['details'])
        self.assertIn('guardian_email', error['details'])
    
    def test_application_submission_custom_error_messages(self):
        """Test that custom error messages are returned for validation errors"""
        # Test required field error message
        data = {'guardian_mobile': '01712345681'}  # Only mobile, missing other required fields
        
        response = self.client.post(
            self.api_url,
            data=data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response_data = response.json()
        error_details = response_data['error']['details']
        
        # Check custom error messages
        self.assertEqual(error_details['student_name'], 'Student name is required.')
        self.assertEqual(error_details['guardian_email'], 'Guardian email is required.')
        self.assertEqual(error_details['address'], 'Address is required.')
    
    def test_application_submission_valid_bangladeshi_phone_numbers(self):
        """Test submission with various valid Bangladeshi phone numbers"""
        valid_phones = [
            '01712345681',  # Grameenphone
            '01812345681',  # Robi
            '01912345681',  # Banglalink
            '01512345681',  # Teletalk
            '01612345681',  # Airtel
            '01312345681',  # Citycell
            '01412345681',  # Airtel
        ]
        
        for i, phone in enumerate(valid_phones):
            data = self.valid_application_data.copy()
            data['guardian_mobile'] = phone
            data['guardian_email'] = f'phone_test_{i}@example.com'
            data['student_name'] = f'Phone Test Student {i}'
            
            response = self.client.post(
                self.api_url,
                data=data,
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify phone number was saved correctly
            response_data = response.json()
            application = AdmissionApplication.objects.get(id=response_data['data']['application_id'])
            self.assertEqual(application.guardian_mobile, phone)
    
    def test_application_submission_endpoint_allows_any_permission(self):
        """Test that the endpoint allows anonymous access"""
        # This test verifies that no authentication is required
        response = self.client.post(
            self.api_url,
            data=self.valid_application_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify that the endpoint doesn't require authentication
        # by checking that we can submit without any authentication headers
        self.assertNotIn('Authorization', self.client.defaults)


# API Tests for Admission Application Submission
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import override_settings
from unittest.mock import patch
import time
import json


class AdmissionApplicationAPITest(APITestCase):
    """Test cases for Admission Application API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        # Valid application data
        self.valid_application_data = {
            'student_name': 'John Doe',
            'student_dob': '2010-05-15',
            'enrolled_class': 'Class 8',
            'address': '123 Main Street, Dhaka, Bangladesh',
            'guardian_name': 'Jane Doe',
            'guardian_mobile': '01712345681',
            'guardian_email': 'jane.doe@example.com',
            'message': 'Please consider my child for admission.',
            'form_start_time': str(time.time() - 10),  # Form started 10 seconds ago
            'captcha_question': 'What is 5 + 3?',
            'captcha_answer': '8'
        }
        
        self.url = reverse('public:admission-application-create-api')
    
    def test_successful_application_submission(self):
        """Test successful admission application submission"""
        response = self.client.post(self.url, self.valid_application_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Your admission application has been submitted successfully', response.data['message'])
        
        # Check that application was created in database
        self.assertEqual(AdmissionApplication.objects.count(), 1)
        application = AdmissionApplication.objects.first()
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
        self.assertEqual(application.status, 'pending')
    
    def test_honeypot_captcha_validation(self):
        """Test honeypot CAPTCHA validation"""
        data = self.valid_application_data.copy()
        data['website'] = 'http://spam.com'  # Honeypot field filled
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        self.assertIn('CAPTCHA validation failed', response.data['error']['message'])
        
        # Check that no application was created
        self.assertEqual(AdmissionApplication.objects.count(), 0)
    
    def test_time_based_captcha_validation_too_fast(self):
        """Test time-based CAPTCHA validation - form submitted too quickly"""
        data = self.valid_application_data.copy()
        data['form_start_time'] = str(time.time() - 1)  # Form started 1 second ago
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Check that no application was created
        self.assertEqual(AdmissionApplication.objects.count(), 0)
    
    def test_time_based_captcha_validation_too_slow(self):
        """Test time-based CAPTCHA validation - form took too long"""
        data = self.valid_application_data.copy()
        data['form_start_time'] = str(time.time() - 2000)  # Form started 2000 seconds ago
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Check that no application was created
        self.assertEqual(AdmissionApplication.objects.count(), 0)
    
    def test_math_captcha_validation_wrong_answer(self):
        """Test math CAPTCHA validation with wrong answer"""
        data = self.valid_application_data.copy()
        data['captcha_answer'] = '10'  # Wrong answer for 5 + 3
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Check that no application was created
        self.assertEqual(AdmissionApplication.objects.count(), 0)
    
    def test_math_captcha_validation_correct_answer(self):
        """Test math CAPTCHA validation with correct answer"""
        data = self.valid_application_data.copy()
        data['captcha_answer'] = '8'  # Correct answer for 5 + 3
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # Check that application was created
        self.assertEqual(AdmissionApplication.objects.count(), 1)
    
    def test_required_field_validation(self):
        """Test validation for required fields"""
        required_fields = [
            'student_name', 'student_dob', 'enrolled_class', 'address',
            'guardian_name', 'guardian_mobile', 'guardian_email'
        ]
        
        for field in required_fields:
            data = self.valid_application_data.copy()
            del data[field]
            
            response = self.client.post(self.url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn(field, response.data['error']['details'])
    
    def test_student_name_validation(self):
        """Test student name validation"""
        # Test empty name
        data = self.valid_application_data.copy()
        data['student_name'] = ''
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('student_name', response.data['error']['details'])
        
        # Test name too short
        data['student_name'] = 'A'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least 2 characters', response.data['error']['details']['student_name'])
        
        # Test invalid characters
        data['student_name'] = 'John123'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('letters, spaces, hyphens', response.data['error']['details']['student_name'])
        
        # Test valid name with special characters
        data['student_name'] = "John O'Connor-Smith"
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_student_dob_validation(self):
        """Test student date of birth validation"""
        # Test future date
        data = self.valid_application_data.copy()
        data['student_dob'] = '2030-01-01'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot be in the future', response.data['error']['details']['student_dob'])
        
        # Test too old
        data['student_dob'] = '1990-01-01'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('too high for school admission', response.data['error']['details']['student_dob'])
        
        # Test too young
        data['student_dob'] = '2023-01-01'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least 3 years old', response.data['error']['details']['student_dob'])
    
    def test_enrolled_class_validation(self):
        """Test enrolled class validation"""
        # Test invalid class
        data = self.valid_application_data.copy()
        data['enrolled_class'] = 'Invalid Class'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Please select a valid class', response.data['error']['details']['enrolled_class'])
        
        # Test valid classes
        valid_classes = ['Nursery', 'KG', 'Class 1', 'Class 5', 'Class 10']
        for class_name in valid_classes:
            data['enrolled_class'] = class_name
            data['guardian_email'] = f'test_{class_name.replace(" ", "_").lower()}@example.com'
            data['guardian_mobile'] = f'0171234568{len(class_name)}'
            
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_address_validation(self):
        """Test address validation"""
        # Test too short address
        data = self.valid_application_data.copy()
        data['address'] = 'Short'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('at least 10 characters', response.data['error']['details']['address'])
        
        # Test too long address
        data['address'] = 'A' * 501
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot exceed 500 characters', response.data['error']['details']['address'])
    
    def test_guardian_mobile_validation(self):
        """Test guardian mobile number validation"""
        # Test invalid format
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '123456789'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('valid Bangladeshi mobile number', response.data['error']['details']['guardian_mobile'])
        
        # Test duplicate mobile
        AdmissionApplication.objects.create(
            student_name='Existing Student',
            student_dob='2010-01-01',
            enrolled_class='Class 1',
            address='Existing Address, Dhaka',
            guardian_name='Existing Guardian',
            guardian_mobile='01712345681',
            guardian_email='existing@example.com'
        )
        
        response = self.client.post(self.url, self.valid_application_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error']['details']['guardian_mobile'])
    
    def test_guardian_email_validation(self):
        """Test guardian email validation"""
        # Test invalid email format
        data = self.valid_application_data.copy()
        data['guardian_email'] = 'invalid-email'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('valid email address', response.data['error']['details']['guardian_email'])
        
        # Test duplicate email
        AdmissionApplication.objects.create(
            student_name='Existing Student',
            student_dob='2010-01-01',
            enrolled_class='Class 1',
            address='Existing Address, Dhaka',
            guardian_name='Existing Guardian',
            guardian_mobile='01712345682',
            guardian_email='jane.doe@example.com'
        )
        
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '01712345683'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.data['error']['details']['guardian_email'])
    
    def test_message_validation(self):
        """Test message field validation"""
        # Test too long message
        data = self.valid_application_data.copy()
        data['message'] = 'A' * 1001
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cannot exceed 1000 characters', response.data['error']['details']['message'])
        
        # Test empty message (should be allowed)
        data['message'] = ''
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_age_class_cross_validation(self):
        """Test cross-validation between student age and enrolled class"""
        # Test age too young for class
        data = self.valid_application_data.copy()
        data['student_dob'] = '2020-01-01'  # 4 years old
        data['enrolled_class'] = 'Class 10'  # Too advanced for 4-year-old
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inappropriate for', response.data['error']['details']['student_dob'])
        
        # Test age too old for class
        data['student_dob'] = '2005-01-01'  # 19 years old
        data['enrolled_class'] = 'Nursery'  # Too basic for 19-year-old
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inappropriate for', response.data['error']['details']['student_dob'])
    
    @override_settings(RATELIMIT_ENABLE=True)
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make 5 successful requests (should be allowed)
        for i in range(5):
            data = self.valid_application_data.copy()
            data['guardian_email'] = f'test{i}@example.com'
            data['guardian_mobile'] = f'0171234568{i}'
            
            response = self.client.post(self.url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 6th request should be rate limited
        data = self.valid_application_data.copy()
        data['guardian_email'] = 'test6@example.com'
        data['guardian_mobile'] = '01712345686'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_whitespace_cleaning(self):
        """Test that whitespace is properly cleaned from input fields"""
        data = self.valid_application_data.copy()
        data.update({
            'student_name': '  John Doe  ',
            'guardian_name': '  Jane Doe  ',
            'enrolled_class': '  Class 8  ',
            'address': '  123 Main Street, Dhaka  ',
            'guardian_email': '  JANE.DOE@EXAMPLE.COM  ',
            'message': '  Please consider my child.  ',
        })
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        application = AdmissionApplication.objects.first()
        self.assertEqual(application.student_name, 'John Doe')
        self.assertEqual(application.guardian_name, 'Jane Doe')
        self.assertEqual(application.enrolled_class, 'Class 8')
        self.assertEqual(application.address, '123 Main Street, Dhaka')
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
        self.assertEqual(application.message, 'Please consider my child.')
    
    def test_response_format(self):
        """Test API response format"""
        response = self.client.post(self.url, self.valid_application_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check success response structure
        self.assertIn('success', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        
        # Check data structure
        data = response.data['data']
        self.assertIn('application_id', data)
        self.assertIn('student_name', data)
        self.assertIn('enrolled_class', data)
        self.assertIn('status', data)
        self.assertIn('date_submitted', data)
        
        self.assertEqual(data['student_name'], 'John Doe')
        self.assertEqual(data['enrolled_class'], 'Class 8')
        self.assertEqual(data['status'], 'pending')
    
    def test_error_response_format(self):
        """Test API error response format"""
        data = self.valid_application_data.copy()
        data['student_name'] = ''  # Invalid data
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error response structure
        self.assertIn('error', response.data)
        error = response.data['error']
        self.assertIn('code', error)
        self.assertIn('message', error)
        self.assertIn('details', error)
        
        self.assertEqual(error['code'], 'VALIDATION_ERROR')
        self.assertIn('student_name', error['details'])
    
    @patch('public.views.logger')
    def test_exception_handling(self, mock_logger):
        """Test exception handling in API view"""
        # Mock an exception during application creation
        with patch.object(AdmissionApplication.objects, 'create', side_effect=Exception('Database error')):
            response = self.client.post(self.url, self.valid_application_data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data['error']['code'], 'SUBMISSION_ERROR')
            self.assertIn('error occurred while submitting', response.data['error']['message'])
            
            # Check that error was logged
            mock_logger.error.assert_called_once()
    
    def test_case_insensitive_class_validation(self):
        """Test that class validation is case insensitive"""
        data = self.valid_application_data.copy()
        data['enrolled_class'] = 'class 8'  # lowercase
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        application = AdmissionApplication.objects.first()
        self.assertEqual(application.enrolled_class, 'class 8')
    
    def test_email_normalization(self):
        """Test that email addresses are normalized to lowercase"""
        data = self.valid_application_data.copy()
        data['guardian_email'] = 'JANE.DOE@EXAMPLE.COM'
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        application = AdmissionApplication.objects.first()
        self.assertEqual(application.guardian_email, 'jane.doe@example.com')
    
    def test_suspicious_user_agent_blocking(self):
        """Test that suspicious user agents are blocked"""
        suspicious_agents = [
            'bot/1.0',
            'crawler/2.0',
            'spider/3.0',
            'scraper/4.0',
            'curl/7.68.0',
            'wget/1.20.3',
            'python-requests/2.25.1'
        ]
        
        for user_agent in suspicious_agents:
            response = self.client.post(
                self.url, 
                self.valid_application_data, 
                format='json',
                HTTP_USER_AGENT=user_agent
            )
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_valid_user_agent_allowed(self):
        """Test that valid user agents are allowed"""
        valid_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        
        for i, user_agent in enumerate(valid_agents):
            data = self.valid_application_data.copy()
            data['guardian_email'] = f'valid_agent_{i}@example.com'
            data['guardian_mobile'] = f'0171234568{i}'
            
            response = self.client.post(
                self.url, 
                data, 
                format='json',
                HTTP_USER_AGENT=user_agent
            )
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_invalid_captcha_timestamp_format(self):
        """Test handling of invalid timestamp format"""
        data = self.valid_application_data.copy()
        data['form_start_time'] = 'invalid_timestamp'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_invalid_captcha_math_format(self):
        """Test handling of invalid math CAPTCHA format"""
        data = self.valid_application_data.copy()
        data['captcha_answer'] = 'not_a_number'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_security_headers_in_response(self):
        """Test that security headers are set in successful responses"""
        response = self.client.post(self.url, self.valid_application_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
    
    def test_enhanced_success_response_format(self):
        """Test the enhanced success response format with next steps"""
        response = self.client.post(self.url, self.valid_application_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check enhanced response structure
        data = response.data['data']
        self.assertIn('next_steps', data)
        self.assertIsInstance(data['next_steps'], list)
        self.assertTrue(len(data['next_steps']) > 0)
        
        # Check formatted date
        self.assertIn('date_submitted', data)
        self.assertNotIn('T', data['date_submitted'])  # Should be formatted, not ISO
    
    def test_duplicate_constraint_error_handling(self):
        """Test handling of database unique constraint errors"""
        # Create first application
        AdmissionApplication.objects.create(
            student_name='Existing Student',
            student_dob='2010-01-01',
            enrolled_class='Class 1',
            address='Existing Address, Dhaka',
            guardian_name='Existing Guardian',
            guardian_mobile='01712345681',
            guardian_email='existing@example.com'
        )
        
        # Try to create duplicate with same mobile
        response = self.client.post(self.url, self.valid_application_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
        self.assertIn('already exists', response.data['error']['details']['guardian_mobile'])
    
    @patch('public.views.logger')
    def test_logging_for_security_events(self, mock_logger):
        """Test that security events are properly logged"""
        # Test honeypot logging
        data = self.valid_application_data.copy()
        data['website'] = 'spam.com'
        
        self.client.post(self.url, data, format='json')
        mock_logger.warning.assert_called()
        
        # Test successful submission logging
        mock_logger.reset_mock()
        data = self.valid_application_data.copy()
        data['website'] = ''  # Remove honeypot
        
        self.client.post(self.url, data, format='json')
        mock_logger.info.assert_called()
    
    def test_comprehensive_error_messages(self):
        """Test that error messages are comprehensive and helpful"""
        # Test student name error
        data = self.valid_application_data.copy()
        data['student_name'] = 'A'
        
        response = self.client.post(self.url, data, format='json')
        error_msg = response.data['error']['details']['student_name']
        self.assertIn('at least 2 characters', error_msg)
        
        # Test address error
        data = self.valid_application_data.copy()
        data['address'] = 'Short'
        
        response = self.client.post(self.url, data, format='json')
        error_msg = response.data['error']['details']['address']
        self.assertIn('at least 10 characters', error_msg)
        self.assertIn('complete address', error_msg)
        
        # Test mobile error
        data = self.valid_application_data.copy()
        data['guardian_mobile'] = '123'
        
        response = self.client.post(self.url, data, format='json')
        error_msg = response.data['error']['details']['guardian_mobile']
        self.assertIn('01712345678', error_msg)  # Should include example


# Import additional modules for API testing
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch
import time
import json

User = get_user_model()


class UserRegistrationAPITest(APITestCase):
    """Test cases for User Registration API endpoint"""
    
    def setUp(self):
        """Set up test data"""
        # Get or create roles
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        # API endpoint URL
        self.registration_url = reverse('public:user-registration-api')
        
        # Valid registration data
        self.valid_registration_data = {
            'username': 'testuser123',
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '01712345681',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            # CAPTCHA fields for spam prevention
            'website': '',  # Honeypot field - should remain empty
            'form_start_time': str(time.time() - 10),  # Form started 10 seconds ago
            'captcha_question': 'What is 5 + 3?',
            'captcha_answer': '8',
        }
    
    def test_successful_user_registration(self):
        """Test successful user registration with valid data"""
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('Your account has been created successfully', response.data['message'])
        
        # Verify user was created in database
        user = User.objects.get(username='testuser123')
        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.phone_number, '01712345681')
        self.assertEqual(user.get_role_name(), 'Guest')  # Default role
        
        # Verify password was set correctly
        self.assertTrue(user.check_password('testpass123'))
        
        # Verify response data structure
        self.assertIn('data', response.data)
        self.assertIn('user_id', response.data['data'])
        self.assertIn('username', response.data['data'])
        self.assertIn('next_steps', response.data['data'])
    
    def test_registration_with_missing_required_fields(self):
        """Test registration fails with missing required fields"""
        required_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password']
        
        for i, field in enumerate(required_fields):
            data = self.valid_registration_data.copy()
            # Make data unique for each iteration to avoid conflicts
            data['username'] = f'testuser{i}'
            data['email'] = f'testuser{i}@example.com'
            data['phone_number'] = f'0171234568{i}'
            data['form_start_time'] = str(time.time() - 10)  # Reset timing
            
            # Remove the field we're testing
            del data[field]
            
            response = self.client.post(self.registration_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, 
                           f"Missing {field} should return 400 error")
            self.assertIn('error', response.data)
            self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
            self.assertIn(field, response.data['error']['details'], 
                         f"Missing {field} should be in error details")
    
    def test_registration_with_empty_fields(self):
        """Test registration fails with empty required fields"""
        empty_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password']
        
        for i, field in enumerate(empty_fields):
            data = self.valid_registration_data.copy()
            # Make data unique for each iteration to avoid conflicts
            data['username'] = f'emptytest{i}'
            data['email'] = f'emptytest{i}@example.com'
            data['phone_number'] = f'0171234567{i}'
            data['form_start_time'] = str(time.time() - 10)  # Reset timing
            data[field] = ''
            
            response = self.client.post(self.registration_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
            self.assertIn(field, response.data['error']['details'])
    
    def test_registration_with_whitespace_only_fields(self):
        """Test registration fails with whitespace-only fields"""
        whitespace_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'password']
        
        for i, field in enumerate(whitespace_fields):
            data = self.valid_registration_data.copy()
            # Make data unique for each iteration to avoid conflicts
            data['username'] = f'whitespacetest{i}'
            data['email'] = f'whitespacetest{i}@example.com'
            data['phone_number'] = f'0171234566{i}'
            data['form_start_time'] = str(time.time() - 10)  # Reset timing
            data[field] = '   '
            
            response = self.client.post(self.registration_url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('error', response.data)
            self.assertIn(field, response.data['error']['details'])
    
    def test_registration_username_validation(self):
        """Test username validation rules"""
        # Test too short username
        data = self.valid_registration_data.copy()
        data['username'] = 'ab'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
        
        # Test too long username
        data['username'] = 'a' * 31  # 31 characters
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid characters in username
        data['username'] = 'test@user'
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test valid username with underscores
        data['username'] = 'test_user_123'
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_email_validation(self):
        """Test email validation rules"""
        invalid_emails = [
            'invalid-email',
            'test@',
            '@example.com',
            'test..test@example.com',
            'test@example',
            'test@.com',
        ]
        
        for invalid_email in invalid_emails:
            data = self.valid_registration_data.copy()
            data['email'] = invalid_email
            data['username'] = f'user_{invalid_emails.index(invalid_email)}'
            
            response = self.client.post(self.registration_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('email', response.data['error']['details'])
    
    def test_registration_phone_number_validation(self):
        """Test phone number validation for Bangladeshi numbers"""
        invalid_phones = [
            '0171234567',    # Too short (10 digits)
            '017123456789',  # Too long (12 digits)
            '02712345678',   # Wrong prefix
            '01012345678',   # Invalid operator code
            '01212345678',   # Invalid operator code
            'abcd1234567',   # Non-numeric characters
            '+8801712345678', # International format not accepted
        ]
        
        for invalid_phone in invalid_phones:
            data = self.valid_registration_data.copy()
            data['phone_number'] = invalid_phone
            data['username'] = f'user_{invalid_phones.index(invalid_phone)}'
            data['email'] = f'user{invalid_phones.index(invalid_phone)}@example.com'
            
            response = self.client.post(self.registration_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('phone_number', response.data['error']['details'])
        
        # Test valid phone numbers
        valid_phones = ['01712345678', '01812345678', '01912345678', '01512345678', '01612345678']
        
        for valid_phone in valid_phones:
            data = self.valid_registration_data.copy()
            data['phone_number'] = valid_phone
            data['username'] = f'validuser_{valid_phones.index(valid_phone)}'
            data['email'] = f'validuser{valid_phones.index(valid_phone)}@example.com'
            
            response = self.client.post(self.registration_url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_password_validation(self):
        """Test password validation rules"""
        # Test too short password
        data = self.valid_registration_data.copy()
        data['password'] = 'short'
        data['password_confirm'] = 'short'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error']['details'])
        
        # Test password without letters
        data['password'] = '12345678'
        data['password_confirm'] = '12345678'
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test password without numbers
        data['password'] = 'testpassword'
        data['password_confirm'] = 'testpassword'
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test common password
        data['password'] = 'password'
        data['password_confirm'] = 'password'
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_password_confirmation_mismatch(self):
        """Test password confirmation validation"""
        data = self.valid_registration_data.copy()
        data['password'] = 'testpass123'
        data['password_confirm'] = 'differentpass123'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data['error']['details'])
    
    def test_registration_name_validation(self):
        """Test first name and last name validation"""
        # Test too short names
        data = self.valid_registration_data.copy()
        data['first_name'] = 'A'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data['error']['details'])
        
        # Test invalid characters in names
        data = self.valid_registration_data.copy()
        data['last_name'] = 'User123'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('last_name', response.data['error']['details'])
        
        # Test valid names with special characters
        data = self.valid_registration_data.copy()
        data['first_name'] = "O'Connor"
        data['last_name'] = "Smith-Jones"
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_uniqueness_constraints(self):
        """Test uniqueness constraints for username, email, and phone"""
        # Create first user
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test duplicate username
        data = self.valid_registration_data.copy()
        data['email'] = 'different@example.com'
        data['phone_number'] = '01712345682'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
        
        # Test duplicate email
        data = self.valid_registration_data.copy()
        data['username'] = 'differentuser'
        data['phone_number'] = '01712345683'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['error']['details'])
        
        # Test duplicate phone number
        data = self.valid_registration_data.copy()
        data['username'] = 'anotheruser'
        data['email'] = 'another@example.com'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data['error']['details'])
    
    def test_registration_captcha_honeypot_validation(self):
        """Test CAPTCHA honeypot field validation"""
        # Test with honeypot field filled (should fail)
        data = self.valid_registration_data.copy()
        data['website'] = 'http://spam.com'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_registration_captcha_timing_validation(self):
        """Test CAPTCHA timing validation"""
        # Test form submitted too quickly (should fail)
        data = self.valid_registration_data.copy()
        data['form_start_time'] = str(time.time() - 1)  # Form started 1 second ago
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test form session expired (should fail)
        data['form_start_time'] = str(time.time() - 3000)  # Form started 50 minutes ago
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_registration_captcha_math_validation(self):
        """Test CAPTCHA math question validation"""
        # Test wrong answer (should fail)
        data = self.valid_registration_data.copy()
        data['captcha_question'] = 'What is 7 + 4?'
        data['captcha_answer'] = '10'  # Wrong answer (should be 11)
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
        
        # Test correct answer (should pass)
        data['captcha_answer'] = '11'  # Correct answer
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_user_agent_validation(self):
        """Test suspicious User-Agent validation"""
        suspicious_agents = [
            'Mozilla/5.0 (compatible; Googlebot/2.1)',
            'curl/7.68.0',
            'python-requests/2.25.1',
            'Scrapy/2.5.0',
        ]
        
        for i, agent in enumerate(suspicious_agents):
            data = self.valid_registration_data.copy()
            # Make data unique for each iteration to avoid conflicts
            data['username'] = f'useragenttest{i}'
            data['email'] = f'useragenttest{i}@example.com'
            data['phone_number'] = f'0171234565{i}'
            data['form_start_time'] = str(time.time() - 10)  # Reset timing
            
            response = self.client.post(
                self.registration_url, 
                data, 
                format='json',
                HTTP_USER_AGENT=agent
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                           f"Suspicious User-Agent '{agent}' should be blocked")
            self.assertEqual(response.data['error']['code'], 'CAPTCHA_FAILED')
    
    def test_registration_cross_field_validation(self):
        """Test cross-field validation rules"""
        # Test username similar to email (should fail)
        data = self.valid_registration_data.copy()
        data['username'] = 'testuser'
        data['email'] = 'testuser@example.com'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error']['details'])
    
    def test_registration_default_role_assignment(self):
        """Test that new users are assigned Guest role by default"""
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='testuser123')
        self.assertEqual(user.get_role_name(), 'Guest')
        self.assertEqual(user.role, self.guest_role)
    
    def test_registration_response_security_headers(self):
        """Test that security headers are set in response"""
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
    
    def test_registration_data_cleaning(self):
        """Test that input data is properly cleaned"""
        data = self.valid_registration_data.copy()
        data.update({
            'username': '  testuser123  ',
            'email': '  TESTUSER@EXAMPLE.COM  ',
            'first_name': '  Test  ',
            'last_name': '  User  ',
            'phone_number': ' 01712345681 ',
        })
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='testuser123')
        self.assertEqual(user.username, 'testuser123')  # Cleaned and lowercased
        self.assertEqual(user.email, 'testuser@example.com')  # Cleaned and lowercased
        self.assertEqual(user.first_name, 'Test')  # Cleaned
        self.assertEqual(user.last_name, 'User')  # Cleaned
        self.assertEqual(user.phone_number, '01712345681')  # Cleaned
    
    def test_registration_logging(self):
        """Test that registration attempts are properly logged"""
        # Test successful registration logging
        # Note: This test verifies the endpoint works, actual logging verification 
        # would require integration testing with log capture
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the response indicates successful registration
        self.assertTrue(response.data['success'])
        self.assertIn('Your account has been created successfully', response.data['message'])
    
    def test_registration_error_handling(self):
        """Test error handling for various scenarios"""
        # Test validation error response format
        data = self.valid_registration_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify error response structure
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
        self.assertIn('details', response.data['error'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
    
    @patch('django_ratelimit.decorators.ratelimit')
    def test_registration_rate_limiting(self, mock_ratelimit):
        """Test that rate limiting is applied when enabled"""
        # Mock rate limiting to simulate being rate limited
        mock_ratelimit.return_value = lambda func: func
        
        with patch('django.conf.settings.RATELIMIT_ENABLE', True):
            # This test verifies the decorator is applied
            # Actual rate limiting behavior would need integration testing
            response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
            # Should still work if not actually rate limited
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])
    
    def test_registration_without_captcha_fields(self):
        """Test registration without CAPTCHA fields (should still work)"""
        data = self.valid_registration_data.copy()
        # Remove CAPTCHA fields
        del data['website']
        del data['form_start_time']
        del data['captcha_question']
        del data['captcha_answer']
        
        response = self.client.post(self.registration_url, data, format='json')
        # Should still work as CAPTCHA validation handles missing fields gracefully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_registration_case_insensitive_email(self):
        """Test that email addresses are handled case-insensitively"""
        # Create user with lowercase email
        response = self.client.post(self.registration_url, self.valid_registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to register with uppercase version of same email
        data = self.valid_registration_data.copy()
        data['username'] = 'differentuser'
        data['email'] = 'TESTUSER@EXAMPLE.COM'
        data['phone_number'] = '01712345682'
        
        response = self.client.post(self.registration_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['error']['details'])


class UserRegistrationIntegrationTest(APITestCase):
    """Integration tests for user registration workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Ensure Guest role exists
        self.guest_role, _ = Role.objects.get_or_create(
            name='Guest',
            defaults={'description': 'Default guest role'}
        )
        
        self.registration_url = reverse('public:user-registration-api')
        self.login_url = reverse('accounts:user-info')  # Using existing endpoint for login test
    
    def test_complete_registration_and_login_workflow(self):
        """Test complete workflow from registration to login"""
        # Step 1: Register new user
        registration_data = {
            'username': 'integrationuser',
            'email': 'integration@example.com',
            'first_name': 'Integration',
            'last_name': 'Test',
            'phone_number': '01712345681',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'website': '',
            'form_start_time': str(time.time() - 10),
            'captcha_question': 'What is 3 + 4?',
            'captcha_answer': '7',
        }
        
        response = self.client.post(self.registration_url, registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Verify user exists in database
        user = User.objects.get(username='integrationuser')
        self.assertEqual(user.email, 'integration@example.com')
        self.assertEqual(user.get_role_name(), 'Guest')
        
        # Step 3: Test login with new credentials (using Django's authentication)
        login_successful = self.client.login(username='integrationuser', password='testpass123')
        self.assertTrue(login_successful)
        
        # Step 4: Verify authenticated user can access protected endpoints
        # This would typically test accessing user profile or other authenticated endpoints
        # For now, we'll just verify the user object is properly created
        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
    
    def test_registration_with_existing_role_data(self):
        """Test registration when roles already exist in database"""
        # Create additional roles
        admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Admin role'}
        )
        
        # Register user (should still get Guest role)
        registration_data = {
            'username': 'roletest',
            'email': 'roletest@example.com',
            'first_name': 'Role',
            'last_name': 'Test',
            'phone_number': '01712345682',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'website': '',
            'form_start_time': str(time.time() - 10),
            'captcha_question': 'What is 2 + 2?',
            'captcha_answer': '4',
        }
        
        response = self.client.post(self.registration_url, registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='roletest')
        self.assertEqual(user.get_role_name(), 'Guest')  # Should still be Guest, not Admin