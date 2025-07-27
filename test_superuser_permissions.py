#!/usr/bin/env python
"""
Test script to verify Django superuser permissions work correctly.
Run this after the fix to ensure superusers have full access.
"""

import os
import sys
import django

# Setup Django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings')
django.setup()

from accounts.models import CustomUser

def test_superuser_permissions():
    """Test that Django superusers have all permissions"""
    
    print("🧪 Testing Django superuser permissions...")
    
    # Find existing superusers
    superusers = CustomUser.objects.filter(is_superuser=True)
    
    if not superusers.exists():
        print("❌ No Django superusers found. Create one with: python manage.py createsuperuser")
        return False
    
    for user in superusers:
        print(f"\n👤 Testing user: {user.username}")
        print(f"   Role: {user.get_role_name()}")
        print(f"   is_superuser: {user.is_superuser}")
        print(f"   is_staff: {user.is_staff}")
        
        # Test critical permissions
        critical_permissions = [
            'can_view_dashboard',
            'can_view_user',
            'can_add_user',
            'can_update_user',
            'can_delete_user',
            'can_view_role',
            'can_add_role',
            'can_update_role',
            'can_delete_role',
            'can_view_notice',
            'can_add_notice',
            'can_update_notice',
            'can_delete_notice',
            'can_view_application',
            'can_add_application',
            'can_update_application',
            'can_delete_application',
            'can_export_data',
            'can_access_settings'
        ]
        
        print("\n🔍 Permission check:")
        all_passed = True
        for permission in critical_permissions:
            has_permission = user.has_role_permission(permission)
            status = "✅" if has_permission else "❌"
            print(f"   {status} {permission}")
            if not has_permission:
                all_passed = False
        
        # Test role methods
        print("\n🔍 Role method check:")
        role_methods = [
            ('is_super_admin()', user.is_super_admin()),
            ('is_admin_or_above()', user.is_admin_or_above()),
            ('is_teacher_or_above()', user.is_teacher_or_above()),
        ]
        
        for method_name, result in role_methods:
            status = "✅" if result else "❌"
            print(f"   {status} {method_name}: {result}")
            if not result:
                all_passed = False
        
        if all_passed:
            print(f"\n✅ All tests passed for {user.username}!")
        else:
            print(f"\n❌ Some tests failed for {user.username}")
            return False
    
    return True

if __name__ == '__main__':
    try:
        success = test_superuser_permissions()
        if success:
            print("\n🎉 All Django superuser tests passed! Your superusers now have full access.")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)