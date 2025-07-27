import re
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from accounts.models import validate_bangladeshi_phone

User = get_user_model()


class ValidationMixin:
    """Mixin with common validation methods to reduce code duplication."""

    @staticmethod
    def validate_name_field(value, field_name="Name"):
        """Common validation for name fields (student_name, guardian_name, etc.)"""
        if not value or not value.strip():
            raise ValidationError(f"{field_name} is required.")

        value = value.strip()

        if len(value) < 2:
            raise ValidationError(f"{field_name} must be at least 2 characters long.")

        if not re.match(r"^[a-zA-Z\s\-'\.]+$", value):
            raise ValidationError(f"{field_name} can only contain letters, spaces, hyphens, and apostrophes.")

        return value

    @staticmethod
    def validate_email_uniqueness(value, model_class, instance=None, field_name="email"):
        """Common email uniqueness validation"""
        value = value.strip().lower()

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError("Please enter a valid email address.")

        query = model_class.objects.filter(**{field_name: value})
        if instance:
            query = query.exclude(id=instance.id)

        if query.exists():
            raise ValidationError(f"A record with this {field_name} already exists.")

        return value

    @staticmethod
    def validate_phone_uniqueness(value, model_class, instance=None, field_name="phone_number"):
        """Common phone number validation and uniqueness check"""
        if not value or not value.strip():
            raise ValidationError("Phone number is required.")

        try:
            cleaned_phone = validate_bangladeshi_phone(value.strip())
        except ValidationError:
            raise ValidationError("Please enter a valid Bangladeshi mobile number (01xxxxxxxxx).")

        query = model_class.objects.filter(**{field_name: cleaned_phone})
        if instance:
            query = query.exclude(id=instance.id)

        if query.exists():
            raise ValidationError(f"A record with this {field_name} already exists.")

        return cleaned_phone

    @staticmethod
    def validate_username_uniqueness(value, instance=None):
        """Common username validation"""
        if not value or not value.strip():
            raise ValidationError("Username is required.")

        value = value.strip().lower()

        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

        if len(value) > 30:
            raise ValidationError("Username cannot exceed 30 characters.")

        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")

        query = User.objects.filter(username=value)
        if instance:
            query = query.exclude(id=instance.id)

        if query.exists():
            raise ValidationError("A user with this username already exists.")

        return value

    @staticmethod
    def validate_password_strength(value):
        """Common password validation"""
        if not value:
            raise ValidationError("Password is required.")

        if len(value) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[A-Za-z]', value):
            raise ValidationError("Password must contain at least one letter.")

        if not re.search(r'\d', value):
            raise ValidationError("Password must contain at least one number.")

        common_passwords = ['password', '12345678', 'qwerty123', 'abc12345']
        if value.lower() in common_passwords:
            raise ValidationError("This password is too common. Please choose a more secure password.")

        return value

    @staticmethod
    def validate_date_range(date_from, date_to, from_field="date_from", to_field="date_to"):
        """Common date range validation"""
        if date_from and date_to and date_from > date_to:
            raise ValidationError({
                to_field: "End date must be after start date."
            })

    @staticmethod
    def validate_student_age_for_class(student_dob, enrolled_class):
        """Validate if student age is appropriate for the enrolled class"""
        from django.utils import timezone

        if not student_dob or not enrolled_class:
            return

        today = timezone.now().date()
        age = today.year - student_dob.year
        if today.month < student_dob.month or (today.month == student_dob.month and today.day < student_dob.day):
            age -= 1

        class_age_ranges = {
            'nursery': (3, 4), 'kg': (4, 5), 'class 1': (5, 7), 'class 2': (6, 8),
            'class 3': (7, 9), 'class 4': (8, 10), 'class 5': (9, 11), 'class 6': (10, 12),
            'class 7': (11, 13), 'class 8': (12, 14), 'class 9': (13, 15), 'class 10': (14, 16),
            'class 11': (15, 17), 'class 12': (16, 18),
        }

        class_key = enrolled_class.lower()
        if class_key in class_age_ranges:
            min_age, max_age = class_age_ranges[class_key]
            if age < min_age - 1 or age > max_age + 2:
                raise ValidationError(
                    f"Student age ({age}) seems inappropriate for {enrolled_class}. Please verify the date of birth and class selection."
                )