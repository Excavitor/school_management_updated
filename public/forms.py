# public/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from .models import AdmissionApplication
from accounts.models import CustomUser
from utils.validators import ValidationMixin


class BaseRecaptchaForm(ValidationMixin, forms.Form):
    """Base form with reCAPTCHA and required field indicators."""
    
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add required attributes to form fields
        for field_name, field in self.fields.items():
            if field.required and field_name != "captcha":
                field.widget.attrs["required"] = True


class AdmissionApplicationForm(BaseRecaptchaForm, forms.ModelForm):
    """Admission application form with validation."""

    class Meta:
        model = AdmissionApplication
        fields = ["student_name", "student_dob", "enrolled_class", "address",
                 "guardian_name", "guardian_mobile", "guardian_email", "message"]

    def clean_student_name(self):
        return self.validate_name_field(self.cleaned_data.get("student_name"), "Student name")

    def clean_student_dob(self):
        from django.utils import timezone
        student_dob = self.cleaned_data.get("student_dob")
        if not student_dob:
            raise ValidationError("Student date of birth is required.")
        if student_dob > timezone.now().date():
            raise ValidationError("Date of birth cannot be in the future.")
        
        # Check age limits (3-25 years)
        today = timezone.now().date()
        age = today.year - student_dob.year
        if today.month < student_dob.month or (today.month == student_dob.month and today.day < student_dob.day):
            age -= 1
        if not (3 <= age <= 25):
            raise ValidationError(f"Student age ({age}) must be between 3-25 years for school admission.")
        return student_dob

    def clean_enrolled_class(self):
        enrolled_class = self.cleaned_data.get("enrolled_class")
        if not enrolled_class:
            raise ValidationError("Please select a class.")
        return enrolled_class

    def clean_address(self):
        address = self.cleaned_data.get("address")
        if not address or not address.strip():
            raise ValidationError("Complete address is required.")
        address = address.strip()
        if len(address) < 10:
            raise ValidationError("Address must be at least 10 characters long.")
        return address

    def clean_guardian_name(self):
        return self.validate_name_field(self.cleaned_data.get("guardian_name"), "Guardian name")

    def clean_guardian_mobile(self):
        return self.validate_phone_uniqueness(self.cleaned_data.get("guardian_mobile"), 
                                            AdmissionApplication, field_name="guardian_mobile")

    def clean_guardian_email(self):
        return self.validate_email_uniqueness(self.cleaned_data.get("guardian_email"), 
                                            AdmissionApplication, field_name="guardian_email")

    def clean_message(self):
        message = self.cleaned_data.get("message", "").strip()
        if message and len(message) > 1000:
            raise ValidationError("Message cannot exceed 1000 characters.")
        return message

    def clean(self):
        cleaned_data = super().clean()
        student_dob = cleaned_data.get("student_dob")
        enrolled_class = cleaned_data.get("enrolled_class")
        if student_dob and enrolled_class:
            try:
                self.validate_student_age_for_class(student_dob, enrolled_class)
            except ValidationError as e:
                raise ValidationError({"student_dob": str(e)})
        return cleaned_data


class UserRegistrationForm(BaseRecaptchaForm, forms.ModelForm):
    """User registration form with password confirmation."""

    password1 = forms.CharField(label="Password *", widget=forms.PasswordInput(
        attrs={"class": "form-control", "placeholder": "Enter a strong password"}),
        help_text="Password must be at least 8 characters long and contain letters and numbers")
    password2 = forms.CharField(label="Confirm Password *", widget=forms.PasswordInput(
        attrs={"class": "form-control", "placeholder": "Confirm your password"}),
        help_text="Enter the same password as above for verification")

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "phone_number"]

    def clean_username(self):
        return self.validate_username_uniqueness(self.cleaned_data.get("username"))

    def clean_email(self):
        return self.validate_email_uniqueness(self.cleaned_data.get("email"), CustomUser)

    def clean_first_name(self):
        return self.validate_name_field(self.cleaned_data.get("first_name"), "First name")

    def clean_last_name(self):
        return self.validate_name_field(self.cleaned_data.get("last_name"), "Last name")

    def clean_phone_number(self):
        return self.validate_phone_uniqueness(self.cleaned_data.get("phone_number"), CustomUser)

    def clean_password1(self):
        return self.validate_password_strength(self.cleaned_data.get("password1"))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
