# public/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django_recaptcha.fields import ReCaptchaField
from .models import Notice, AdmissionApplication
from utils.validators import ValidationMixin

User = get_user_model()


class NoticeListSerializer(serializers.ModelSerializer):
    """Serializer for listing published notices."""

    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = [
            "id",
            "title",
            "content",
            "excerpt",
            "date_created",
            "date_updated",
            "created_by_name",
        ]
        read_only_fields = [
            "id",
            "date_created",
            "date_updated",
            "created_by_name",
            "excerpt",
        ]

    def get_excerpt(self, obj):
        """Get a truncated version of the content for listing view."""
        return obj.get_excerpt(length=200)


class AdmissionApplicationCreateSerializer(
    ValidationMixin, serializers.ModelSerializer
):
    """Serializer for creating admission applications with reCAPTCHA validation."""

    captcha = ReCaptchaField()

    class Meta:
        model = AdmissionApplication
        fields = [
            "student_name",
            "student_dob",
            "enrolled_class",
            "address",
            "guardian_name",
            "guardian_mobile",
            "guardian_email",
            "message",
            "captcha",
        ]

    def validate_student_name(self, value):
        return self.validate_name_field(value, "Student name")

    def validate_guardian_name(self, value):
        return self.validate_name_field(value, "Guardian name")

    def validate_student_dob(self, value):
        if not value:
            raise serializers.ValidationError("Student date of birth is required.")

        if value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        # Check age limits (3-25 years)
        today = timezone.now().date()
        max_age_date = today - timedelta(days=25 * 365)
        min_age_date = today - timedelta(days=3 * 365)

        if value < max_age_date:
            raise serializers.ValidationError(
                "Student age seems too high for school admission."
            )
        if value > min_age_date:
            raise serializers.ValidationError("Student must be at least 3 years old.")

        return value

    def validate_enrolled_class(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Enrolled class is required.")

        value = value.strip()
        valid_classes = [
            "Nursery",
            "KG",
            "Class 1",
            "Class 2",
            "Class 3",
            "Class 4",
            "Class 5",
            "Class 6",
            "Class 7",
            "Class 8",
            "Class 9",
            "Class 10",
            "Class 11",
            "Class 12",
        ]

        if not any(
            value.lower() == valid_class.lower() for valid_class in valid_classes
        ):
            raise serializers.ValidationError(
                f"Please select a valid class. Valid options: {', '.join(valid_classes)}"
            )
        return value

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Address is required.")

        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError(
                "Address must be at least 10 characters long."
            )
        if len(value) > 500:
            raise serializers.ValidationError("Address cannot exceed 500 characters.")

        return value

    def validate_guardian_mobile(self, value):
        return self.validate_phone_uniqueness(
            value, AdmissionApplication, field_name="guardian_mobile"
        )

    def validate_guardian_email(self, value):
        return self.validate_email_uniqueness(
            value, AdmissionApplication, field_name="guardian_email"
        )

    def validate_message(self, value):
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError("Message cannot exceed 1000 characters.")
        return value.strip() if value else ""

    def validate(self, attrs):
        # Use the validation mixin for age/class validation
        if "student_dob" in attrs and "enrolled_class" in attrs:
            self.validate_student_age_for_class(
                attrs["student_dob"], attrs["enrolled_class"]
            )
        return attrs


class UserRegistrationSerializer(ValidationMixin, serializers.ModelSerializer):
    """Serializer for public user registration with reCAPTCHA validation."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)
    captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
            "captcha",
        )

    def validate_username(self, value):
        return self.validate_username_uniqueness(value)

    def validate_email(self, value):
        return self.validate_email_uniqueness(value, User)

    def validate_first_name(self, value):
        return self.validate_name_field(value, "First name")

    def validate_last_name(self, value):
        return self.validate_name_field(value, "Last name")

    def validate_phone_number(self, value):
        return self.validate_phone_uniqueness(value, User)

    def validate_password(self, value):
        return self.validate_password_strength(value)

    def validate(self, attrs):
        # Check password confirmation
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Password confirmation does not match."}
            )

        attrs.pop("password_confirm", None)

        # Check if username is similar to email
        username = attrs.get("username", "")
        email = attrs.get("email", "")
        if username and email and username in email:
            raise serializers.ValidationError(
                {
                    "username": "Username should not be part of your email address for security reasons."
                }
            )

        return attrs
