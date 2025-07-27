# public/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import validate_bangladeshi_phone, BangladeshiPhoneNumberField

User = get_user_model()


class NoticeManager(models.Manager):
    """Custom manager for Notice model with utility methods"""
    
    def published(self):
        """Return only published notices"""
        return self.filter(published=True)
    
    def recent_published(self, limit=5):
        """Return recent published notices"""
        return self.published().order_by('-date_created')[:limit]
    
    def search_published(self, query):
        """Search in published notices by title and content"""
        if not query:
            return self.published()
        
        return self.published().filter(
            models.Q(title__icontains=query) | 
            models.Q(content__icontains=query)
        )


class Notice(models.Model):
    """
    Notice model for managing school announcements and notices.
    Supports published/unpublished status and full audit trail.
    """
    title = models.CharField(
        max_length=200,
        help_text='Title of the notice (max 200 characters)'
    )
    content = models.TextField(
        help_text='Main content of the notice'
    )
    published = models.BooleanField(
        default=False,
        help_text='Whether this notice is visible to the public'
    )
    date_created = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the notice was created'
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when the notice was last updated'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notices',
        help_text='User who created this notice'
    )
    
    # Custom manager
    objects = NoticeManager()
    
    class Meta:
        ordering = ['-date_created']
        verbose_name = 'Notice'
        verbose_name_plural = 'Notices'
        indexes = [
            models.Index(fields=['published', '-date_created']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        status = "Published" if self.published else "Draft"
        return f"{self.title} ({status})"
    
    def clean(self):
        """Validate the notice data"""
        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'Title cannot be empty or whitespace only.'})
        
        if not self.content or not self.content.strip():
            raise ValidationError({'content': 'Content cannot be empty or whitespace only.'})
        
        # Clean whitespace
        if self.title:
            self.title = self.title.strip()
        if self.content:
            self.content = self.content.strip()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_published(self):
        """Check if the notice is published"""
        return self.published
    
    def publish(self):
        """Publish the notice"""
        self.published = True
        self.save()
    
    def unpublish(self):
        """Unpublish the notice"""
        self.published = False
        self.save()
    
    def get_status_display_color(self):
        """Get Bootstrap color class for status display"""
        return 'success' if self.published else 'secondary'
    
    def get_excerpt(self, length=150):
        """Get a truncated version of the content"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length].rsplit(' ', 1)[0] + '...'
    
    def can_be_edited_by(self, user):
        """Check if a user can edit this notice"""
        if not user or not user.is_authenticated:
            return False
        
        # SuperAdmin and Admin can edit any notice
        if user.is_admin_or_above():
            return True
        
        # Creator can edit their own notice
        return self.created_by == user
    
    def can_be_deleted_by(self, user):
        """Check if a user can delete this notice"""
        if not user or not user.is_authenticated:
            return False
        
        # SuperAdmin and Admin can delete any notice
        if user.is_admin_or_above():
            return True
        
        # Creator can delete their own notice
        return self.created_by == user


class AdmissionApplicationManager(models.Manager):
    """Custom manager for AdmissionApplication model with utility methods"""
    
    def pending(self):
        """Return only pending applications"""
        return self.filter(status='pending')
    
    def accepted(self):
        """Return only accepted applications"""
        return self.filter(status='accepted')
    
    def rejected(self):
        """Return only rejected applications"""
        return self.filter(status='rejected')
    
    def recent(self, limit=5):
        """Return recent applications"""
        return self.order_by('-date_submitted')[:limit]
    
    def search(self, query):
        """Search applications by student name, guardian name, or class"""
        if not query:
            return self.all()
        
        return self.filter(
            models.Q(student_name__icontains=query) |
            models.Q(guardian_name__icontains=query) |
            models.Q(enrolled_class__icontains=query)
        )


class AdmissionApplication(models.Model):
    """
    AdmissionApplication model for managing student admission applications.
    Supports status tracking and comprehensive student/guardian information.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    # Student Information
    student_name = models.CharField(
        max_length=100,
        help_text='Full name of the student applying for admission'
    )
    student_dob = models.DateField(
        help_text='Date of birth of the student'
    )
    enrolled_class = models.CharField(
        max_length=50,
        help_text='Class/Grade the student wants to enroll in'
    )
    address = models.TextField(
        help_text='Complete address of the student'
    )
    
    # Guardian Information
    guardian_name = models.CharField(
        max_length=100,
        help_text='Full name of the student\'s guardian'
    )
    guardian_mobile = BangladeshiPhoneNumberField(
        unique=True,
        help_text='Guardian\'s mobile number (Bangladeshi format: 01xxxxxxxxx)'
    )
    guardian_email = models.EmailField(
        unique=True,
        help_text='Guardian\'s email address'
    )
    
    # Additional Information
    message = models.TextField(
        blank=True,
        help_text='Additional message or information from the guardian'
    )
    
    # Application Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the admission application'
    )
    date_submitted = models.DateTimeField(
        auto_now_add=True,
        help_text='Timestamp when the application was submitted'
    )
    date_updated = models.DateTimeField(
        auto_now=True,
        help_text='Timestamp when the application was last updated'
    )
    
    # Custom manager
    objects = AdmissionApplicationManager()
    
    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Admission Application'
        verbose_name_plural = 'Admission Applications'
        indexes = [
            models.Index(fields=['status', '-date_submitted']),
            models.Index(fields=['guardian_mobile']),
            models.Index(fields=['guardian_email']),
            models.Index(fields=['enrolled_class']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['guardian_mobile'],
                name='unique_guardian_mobile'
            ),
            models.UniqueConstraint(
                fields=['guardian_email'],
                name='unique_guardian_email'
            ),
        ]
    
    def __str__(self):
        return f"{self.student_name} - {self.enrolled_class} ({self.get_status_display()})"
    
    def clean(self):
        """Validate the admission application data"""
        errors = {}
        
        # Validate student name
        if not self.student_name or not self.student_name.strip():
            errors['student_name'] = 'Student name cannot be empty or whitespace only.'
        
        # Validate guardian name
        if not self.guardian_name or not self.guardian_name.strip():
            errors['guardian_name'] = 'Guardian name cannot be empty or whitespace only.'
        
        # Validate enrolled class
        if not self.enrolled_class or not self.enrolled_class.strip():
            errors['enrolled_class'] = 'Enrolled class cannot be empty or whitespace only.'
        
        # Validate address
        if not self.address or not self.address.strip():
            errors['address'] = 'Address cannot be empty or whitespace only.'
        
        # Validate guardian email
        if not self.guardian_email or not self.guardian_email.strip():
            errors['guardian_email'] = 'Guardian email cannot be empty or whitespace only.'
        
        # Validate date of birth (should not be in the future)
        if self.student_dob and self.student_dob > timezone.now().date():
            errors['student_dob'] = 'Date of birth cannot be in the future.'
        
        # Clean whitespace from text fields
        if self.student_name:
            self.student_name = self.student_name.strip()
        if self.guardian_name:
            self.guardian_name = self.guardian_name.strip()
        if self.enrolled_class:
            self.enrolled_class = self.enrolled_class.strip()
        if self.address:
            self.address = self.address.strip()
        if self.guardian_email:
            self.guardian_email = self.guardian_email.strip().lower()
        if self.message:
            self.message = self.message.strip()
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_pending(self):
        """Check if the application is pending"""
        return self.status == 'pending'
    
    def is_accepted(self):
        """Check if the application is accepted"""
        return self.status == 'accepted'
    
    def is_rejected(self):
        """Check if the application is rejected"""
        return self.status == 'rejected'
    
    def accept(self):
        """Accept the application"""
        self.status = 'accepted'
        self.save()
    
    def reject(self):
        """Reject the application"""
        self.status = 'rejected'
        self.save()
    
    def reset_to_pending(self):
        """Reset the application status to pending"""
        self.status = 'pending'
        self.save()
    
    def get_status_display_color(self):
        """Get Bootstrap color class for status display"""
        status_colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
        }
        return status_colors.get(self.status, 'secondary')
    
    def get_student_age(self):
        """Calculate and return the student's age"""
        if not self.student_dob:
            return None
        
        today = timezone.now().date()
        age = today.year - self.student_dob.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.student_dob.month or \
           (today.month == self.student_dob.month and today.day < self.student_dob.day):
            age -= 1
        
        return age
    
    def get_formatted_mobile(self):
        """Get formatted mobile number for display"""
        if not self.guardian_mobile:
            return ''
        
        # Format as: 01X-XXXX-XXXX
        mobile = str(self.guardian_mobile)
        if len(mobile) == 11:
            return f"{mobile[:3]}-{mobile[3:7]}-{mobile[7:]}"
        return mobile
    
    def can_be_updated_by(self, user):
        """Check if a user can update this application"""
        if not user or not user.is_authenticated:
            return False
        
        # Admin and SuperAdmin can update any application
        return user.is_admin_or_above()
    
    def can_be_deleted_by(self, user):
        """Check if a user can delete this application"""
        if not user or not user.is_authenticated:
            return False
        
        # Admin and SuperAdmin can delete any application
        return user.is_admin_or_above()
