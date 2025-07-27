from django.contrib import admin
from .models import Notice, AdmissionApplication


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    """Admin interface for Notice model"""
    list_display = ['title', 'published', 'created_by', 'date_created', 'date_updated']
    list_filter = ['published', 'date_created', 'created_by']
    search_fields = ['title', 'content']
    readonly_fields = ['date_created', 'date_updated']
    list_editable = ['published']
    
    fieldsets = (
        ('Notice Information', {'fields': ('title', 'content', 'published')}),
        ('Audit Information', {'fields': ('created_by', 'date_created', 'date_updated'), 'classes': ('collapse',)}),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if creating new notice"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    """Admin interface for AdmissionApplication model"""
    list_display = ['student_name', 'enrolled_class', 'guardian_name', 'guardian_mobile', 'status', 'date_submitted']
    list_filter = ['status', 'enrolled_class', 'date_submitted']
    search_fields = ['student_name', 'guardian_name', 'guardian_mobile', 'guardian_email', 'enrolled_class']
    readonly_fields = ['date_submitted', 'date_updated']
    list_editable = ['status']
    
    fieldsets = (
        ('Student Information', {'fields': ('student_name', 'student_dob', 'enrolled_class', 'address')}),
        ('Guardian Information', {'fields': ('guardian_name', 'guardian_mobile', 'guardian_email')}),
        ('Application Details', {'fields': ('message', 'status')}),
        ('Audit Information', {'fields': ('date_submitted', 'date_updated'), 'classes': ('collapse',)}),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['student_name', 'student_dob', 'enrolled_class', 'address',
                           'guardian_name', 'guardian_mobile', 'guardian_email', 'message'])
        return readonly