#!/usr/bin/env python
"""
Test script to verify the implemented changes:
1. Terms and conditions checkbox validation
2. Email login instead of username login
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings.dev')
django.setup()

User = get_user_model()

def test_email_login():
    """Test that users can login with email instead of username"""
    print("Testing email login functionality...")
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    client = Client()
    
    # Test login with email
    response = client.post('/login/', 
        data='{"username": "test@example.com", "password": "testpass123"}',
        content_type='application/json'
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Email login works correctly")
        else:
            print("❌ Email login failed:", data.get('error'))
    else:
        print("❌ Email login request failed with status:", response.status_code)
    
    # Test login with wrong email
    response = client.post('/login/', 
        data='{"username": "wrong@example.com", "password": "testpass123"}',
        content_type='application/json'
    )
    
    if response.status_code == 400:
        data = response.json()
        if 'Invalid email or password' in data.get('error', ''):
            print("✅ Invalid email properly rejected")
        else:
            print("❌ Wrong error message for invalid email:", data.get('error'))
    else:
        print("❌ Invalid email should return 400 status")
    
    # Clean up
    user.delete()

def test_terms_validation():
    """Test that terms and conditions checkbox is properly validated"""
    print("\nTesting terms and conditions validation...")
    
    from public.forms import UserRegistrationForm, AdmissionApplicationForm
    from public.serializers import UserRegistrationSerializer, AdmissionApplicationCreateSerializer
    
    # Test UserRegistrationForm without terms
    form_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '01712345678',
        'password1': 'testpass123',
        'password2': 'testpass123',
        # 'terms': True,  # Missing terms
    }
    
    form = UserRegistrationForm(data=form_data)
    if not form.is_valid():
        if 'terms' in form.errors:
            print("✅ Registration form properly validates terms checkbox")
        else:
            print("❌ Registration form should validate terms checkbox")
            print("Form errors:", form.errors)
    else:
        print("❌ Registration form should be invalid without terms")
    
    # Test UserRegistrationForm with terms
    form_data['terms'] = True
    form = UserRegistrationForm(data=form_data)
    # Note: This will still fail due to reCAPTCHA, but terms should not be in errors
    if 'terms' not in form.errors:
        print("✅ Registration form accepts terms when checked")
    else:
        print("❌ Registration form should accept terms when checked")
    
    # Test AdmissionApplicationForm without terms
    admission_data = {
        'student_name': 'Test Student',
        'student_dob': '2010-01-01',
        'enrolled_class': 'Class 5',
        'address': 'Test Address, Test City',
        'guardian_name': 'Test Guardian',
        'guardian_mobile': '01712345678',
        'guardian_email': 'guardian@example.com',
        'message': 'Test message',
        # 'terms': True,  # Missing terms
    }
    
    admission_form = AdmissionApplicationForm(data=admission_data)
    if not admission_form.is_valid():
        if 'terms' in admission_form.errors:
            print("✅ Admission form properly validates terms checkbox")
        else:
            print("❌ Admission form should validate terms checkbox")
            print("Form errors:", admission_form.errors)
    else:
        print("❌ Admission form should be invalid without terms")

if __name__ == '__main__':
    print("Running tests for implemented changes...\n")
    test_email_login()
    test_terms_validation()
    print("\nTest completed!")