from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import re


def validate_bangladeshi_phone(phone_number):
    """
    Validate Bangladeshi phone number format.
    Must start with 01 and be exactly 11 digits.
    """
    if not phone_number:
        raise ValidationError('Phone number is required.')
    
    # Remove any spaces or special characters
    cleaned_phone = re.sub(r'[^\d]', '', phone_number)
    
    # Check if it matches Bangladeshi format with valid operator codes
    # Valid operator codes: 013, 014, 015, 016, 017, 018, 019
    if not re.match(r'^01[3-9]\d{8}$', cleaned_phone):
        raise ValidationError(
            'Phone number must be a valid Bangladeshi number (01xxxxxxxxx) with a valid operator code.'
        )
    
    return cleaned_phone


class BangladeshiPhoneNumberField(models.CharField):
    """Custom field for Bangladeshi phone numbers with automatic cleaning"""
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 11
        super().__init__(*args, **kwargs)
    
    def to_python(self, value):
        """Convert the value to a Python object"""
        if value is None:
            return value
        
        # Clean the phone number
        if isinstance(value, str):
            cleaned_value = re.sub(r'[^\d]', '', value)
            return cleaned_value
        
        return str(value)
    
    def validate(self, value, model_instance):
        """Validate the field value"""
        super().validate(value, model_instance)
        if value:
            validate_bangladeshi_phone(value)


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.JSONField(default=dict, blank=True, null=True, help_text="JSON field to store role-specific permissions")
    description = models.TextField(blank=True, help_text="Description of the role and its responsibilities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.name

    def clean(self):
        """Validate role name"""
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({'name': 'Role name cannot be empty or whitespace only.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def has_permission(self, permission_key):
        """Check if role has a specific permission"""
        if self.permissions is None:
            return False
        return self.permissions.get(permission_key, False)

    def add_permission(self, permission_key, value=True):
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission_key] = value
        self.save()

    def remove_permission(self, permission_key):
        if self.permissions is not None and permission_key in self.permissions:
            del self.permissions[permission_key]
            self.save()


class CustomUser(AbstractUser):
    phone_number = BangladeshiPhoneNumberField(
        null=True,
        blank=True,
        help_text='Bangladeshi phone number starting with 01 (11 digits)'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        # Allow the role to be null and set the default to None.
        null=True,
        blank=True,
        default=None,
        help_text='User role determining access permissions'
    )
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_role_name(self):
        """Get the name of the user's role"""
        # Django superusers are displayed as SuperAdmin
        if self.is_superuser:
            return 'SuperAdmin (Django Superuser)'
            
        try:
            return self.role.name if self.role else 'Guest'
        except Role.DoesNotExist:
            return 'Guest'

    def has_role_permission(self, permission_key):
        """Check if user has a specific permission through their role or default permissions for null role"""
        # Django superusers have all permissions
        if self.is_superuser:
            return True
            
        try:
            if not self.role:
                # Use default permissions for users without a role (equivalent to old Guest role)
                default_permissions = self.get_default_permissions()
                return default_permissions.get(permission_key, False)
            return self.role.has_permission(permission_key)
        except Role.DoesNotExist:
            return False

    def is_super_admin(self):
        """Check if user is a SuperAdmin"""
        # Django superusers are considered super admins
        if self.is_superuser:
            return True
            
        try:
            return self.role and self.role.name == 'SuperAdmin'
        except Role.DoesNotExist:
            return False

    def is_admin_or_above(self):
        """Check if user is Admin or SuperAdmin"""
        # Django superusers are considered admin or above
        if self.is_superuser:
            return True
            
        try:
            return self.role and self.role.name in ['Admin', 'SuperAdmin']
        except Role.DoesNotExist:
            return False

    def is_teacher_or_above(self):
        """Check if user is Teacher, Admin, or SuperAdmin"""
        # Django superusers are considered teacher or above
        if self.is_superuser:
            return True
            
        try:
            return self.role and self.role.name in ['Teacher', 'Admin', 'SuperAdmin']
        except Role.DoesNotExist:
            return False

    def get_default_permissions(self):
        """Get default permissions for users without a role"""
        return {
            'can_view_dashboard': True,
            'can_view_notice': True,
            'can_add_notice': False,
            'can_update_notice': False,
            'can_delete_notice': False,
            'can_view_application': False,
            'can_add_application': False,
            'can_update_application': False,
            'can_delete_application': False,
            'can_view_user': False,
            'can_add_user': False,
            'can_update_user': False,
            'can_delete_user': False,
            'can_view_role': False,
            'can_add_role': False,
            'can_update_role': False,
            'can_delete_role': False,
            'can_export_data': False,
            'can_view_reports': False,
            'can_moderate_content': False,
            'can_access_settings': False,
        }