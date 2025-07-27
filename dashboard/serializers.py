from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
from public.models import Notice, AdmissionApplication
from accounts.models import Role, validate_bangladeshi_phone

User = get_user_model()


class NoticeManagementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display_color", read_only=True)
    excerpt = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'published', 'date_created', 'date_updated',
                 'created_by_name', 'status_display', 'excerpt']
        read_only_fields = ['id', 'date_created', 'date_updated', 'created_by_name', 'status_display', 'excerpt']

    def get_excerpt(self, obj):
        return obj.get_excerpt(length=100)

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return Notice.objects.create(**validated_data)


class AdmissionApplicationManagementSerializer(serializers.ModelSerializer):
    student_age = serializers.SerializerMethodField(read_only=True)
    formatted_mobile = serializers.SerializerMethodField(read_only=True)
    status_display_color = serializers.CharField(source="get_status_display_color", read_only=True)

    class Meta:
        model = AdmissionApplication
        fields = ['id', 'student_name', 'student_dob', 'enrolled_class', 'guardian_name',
                 'guardian_mobile', 'guardian_email', 'status', 'date_submitted',
                 'student_age', 'formatted_mobile', 'status_display_color']
        read_only_fields = ['id', 'date_submitted', 'student_age', 'formatted_mobile', 'status_display_color']

    def get_student_age(self, obj):
        return obj.get_student_age()

    def get_formatted_mobile(self, obj):
        return obj.get_formatted_mobile()


class UserManagementSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'role', 'role_name', 'is_active', 'date_joined', 'full_name']
        read_only_fields = ['id', 'date_joined', 'role_name', 'full_name']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'phone_number': {'required': False},
        }

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value:
            try:
                validate_bangladeshi_phone(value)
            except ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if value and self.instance:
            if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Validate username uniqueness."""
        if value and self.instance:
            if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A user with this username already exists.")
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    current_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'role_name', 'date_joined', 'password', 'current_password']
        read_only_fields = ['id', 'username', 'role_name', 'date_joined']

    def validate_current_password(self, value):
        if value and self.instance and not self.instance.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        current_password = attrs.get("current_password")
        
        if password and not current_password:
            raise serializers.ValidationError({"current_password": "Current password is required."})
        
        attrs.pop("current_password", None)
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RoleManagementSerializer(serializers.ModelSerializer):
    """Serializer for role management in dashboard (SuperAdmin only)."""
    
    user_count = serializers.SerializerMethodField(read_only=True)
    is_system_role = serializers.SerializerMethodField(read_only=True)
    permissions_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'created_at', 'updated_at',
                 'user_count', 'is_system_role', 'permissions_display']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count', 'is_system_role', 'permissions_display']

    def get_user_count(self, obj):
        """Get the number of users with this role."""
        return obj.customuser_set.count()

    def get_is_system_role(self, obj):
        """Check if this is a system role that shouldn't be deleted."""
        system_roles = ['SuperAdmin', 'Admin', 'Teacher', 'Guest']
        return obj.name in system_roles

    def get_permissions_display(self, obj):
        """Get a formatted display of permissions."""
        if not obj.permissions:
            return "No permissions"
        
        permission_count = len([k for k, v in obj.permissions.items() if v])
        return f"{permission_count} permissions"

    def validate_name(self, value):
        """Validate role name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Role name cannot be empty.")
        
        value = value.strip()
        
        # Check for uniqueness
        if self.instance:
            if Role.objects.filter(name=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A role with this name already exists.")
        else:
            if Role.objects.filter(name=value).exists():
                raise serializers.ValidationError("A role with this name already exists.")
        
        return value

    def validate_permissions(self, value):
        """Validate permissions JSON structure."""
        if value is None:
            return {}
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Permissions must be a valid JSON object.")
        
        # Validate that all values are boolean
        for key, val in value.items():
            if not isinstance(val, bool):
                raise serializers.ValidationError(f"Permission '{key}' must be a boolean value.")
        
        return value


class BulkActionSerializer(serializers.Serializer):
    """Generic serializer for bulk operations."""
    
    ids = serializers.ListField(child=serializers.IntegerField(), min_length=1, max_length=100)
    action = serializers.CharField(max_length=50)

    def validate_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one ID is required.")
        return value