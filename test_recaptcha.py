#!/usr/bin/env python
"""
Test script to verify reCAPTCHA configuration
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings.dev')
django.setup()

def test_recaptcha_config():
    """Test reCAPTCHA configuration"""
    print("Testing reCAPTCHA Configuration...")
    print("=" * 50)
    
    # Check if django_recaptcha is in INSTALLED_APPS
    if 'django_recaptcha' in settings.INSTALLED_APPS:
        print("✓ django_recaptcha is in INSTALLED_APPS")
    else:
        print("✗ django_recaptcha is NOT in INSTALLED_APPS")
        return False
    
    # Check reCAPTCHA keys
    public_key = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '')
    private_key = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '')
    
    if public_key:
        print(f"✓ RECAPTCHA_PUBLIC_KEY is set: {public_key[:20]}...")
    else:
        print("✗ RECAPTCHA_PUBLIC_KEY is not set")
        return False
    
    if private_key:
        print(f"✓ RECAPTCHA_PRIVATE_KEY is set: {private_key[:20]}...")
    else:
        print("✗ RECAPTCHA_PRIVATE_KEY is not set")
        return False
    
    # Test importing reCAPTCHA field
    try:
        from django_recaptcha.fields import ReCaptchaField
        from django_recaptcha.widgets import ReCaptchaV2Checkbox
        print("✓ Successfully imported reCAPTCHA components")
    except ImportError as e:
        print(f"✗ Failed to import reCAPTCHA components: {e}")
        return False
    
    # Test form creation
    try:
        from django import forms
        
        class TestForm(forms.Form):
            captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
        
        form = TestForm()
        print("✓ Successfully created test form with reCAPTCHA field")
    except Exception as e:
        print(f"✗ Failed to create test form: {e}")
        return False
    
    print("=" * 50)
    print("✓ All reCAPTCHA tests passed!")
    return True

def test_forms_and_serializers():
    """Test that forms and serializers can be imported without errors"""
    print("\nTesting Forms and Serializers...")
    print("=" * 50)
    
    try:
        from public.forms import AdmissionApplicationForm, UserRegistrationForm
        print("✓ Successfully imported public forms")
    except Exception as e:
        print(f"✗ Failed to import public forms: {e}")
        return False
    
    try:
        from public.serializers import AdmissionApplicationCreateSerializer, UserRegistrationSerializer
        print("✓ Successfully imported public serializers")
    except Exception as e:
        print(f"✗ Failed to import public serializers: {e}")
        return False
    
    # Test form instantiation
    try:
        admission_form = AdmissionApplicationForm()
        registration_form = UserRegistrationForm()
        print("✓ Successfully instantiated forms")
    except Exception as e:
        print(f"✗ Failed to instantiate forms: {e}")
        return False
    
    print("=" * 50)
    print("✓ All form and serializer tests passed!")
    return True

if __name__ == "__main__":
    success = True
    success &= test_recaptcha_config()
    success &= test_forms_and_serializers()
    
    if success:
        print("\n🎉 All tests passed! reCAPTCHA is properly configured.")
    else:
        print("\n❌ Some tests failed. Please check the configuration.")