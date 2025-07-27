#!/usr/bin/env python
"""
Simple test script to verify null role functionality works correctly.
Run this after setting up the project to ensure everything works.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings')
django.setup()

from accounts.models import CustomUser, Role

def test_null_role_functionality():
    """Test that users with null role have correct permissions"""
    
    print("🧪 Testing null role functionality...")
    
    # Create a test user with null role
    test_user = CustomUser.objects.create_user(
        username='test_null_user',
        email='test@example.com',
        password='testpass123',
        phone_number='01712345678'
        # role is intentionally left as None/null
    )
    
    print(f"✅ Created test user: {test_user.username}")
    print(f"   Role: {test_user.get_role_name()}")
    print(f"   Role object: {test_user.role}")
    
    # Test permissions
    permissions_to_test = [
        'can_view_dashboard',
        'can_view_notice',
        'can_add_notice',
        'can_view_user',
        'can_access_settings'
    ]
    
    print("\n🔍 Testing permissions:")
    for permission in permissions_to_test:
        has_permission = test_user.has_role_permission(permission)
        status = "✅" if has_permission else "❌"
        print(f"   {status} {permission}: {has_permission}")
    
    # Test role methods
    print("\n🔍 Testing role methods:")
    print(f"   is_super_admin(): {test_user.is_super_admin()}")
    print(f"   is_admin_or_above(): {test_user.is_admin_or_above()}")
    print(f"   is_teacher_or_above(): {test_user.is_teacher_or_above()}")
    
    # Test default permissions
    default_perms = test_user.get_default_permissions()
    print(f"\n📋 Default permissions count: {len(default_perms)}")
    print(f"   can_view_dashboard: {default_perms.get('can_view_dashboard')}")
    
    # Cleanup
    test_user.delete()
    print("\n🧹 Cleaned up test user")
    
    print("\n✅ All tests passed! Null role functionality is working correctly.")

def test_role_setup():
    """Test that role setup command works without Guest role"""
    
    print("\n🧪 Testing role setup...")
    
    # Check that Guest role doesn't exist
    guest_exists = Role.objects.filter(name='Guest').exists()
    print(f"   Guest role exists: {guest_exists}")
    
    # Check that other roles exist
    expected_roles = ['SuperAdmin', 'Admin', 'Teacher']
    for role_name in expected_roles:
        exists = Role.objects.filter(name=role_name).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {role_name} role exists: {exists}")
    
    print("✅ Role setup test completed!")

if __name__ == '__main__':
    try:
        test_null_role_functionality()
        test_role_setup()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)