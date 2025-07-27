from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import validate_bangladeshi_phone, Role

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    phone_number = serializers.CharField(
        max_length=11,
        help_text='Bangladeshi phone number starting with 01 (11 digits)'
    )
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'password'
        )
    
    def validate_phone_number(self, value):
        try:
            cleaned_phone = validate_bangladeshi_phone(value)
            return cleaned_phone
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        return value
    
    def create(self, validated_data):
        # The role will be automatically set to None (null) for new users
        user = User.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(UserSerializer):
    # user profile information
    role_name = serializers.CharField(source='get_role_name', read_only=True)
    phone_number = serializers.CharField(max_length=11)
    
    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role_name', 'date_joined', 'is_active'
        )
        read_only_fields = ('id', 'username', 'date_joined', 'role_name')
    
    def validate_phone_number(self, value):
        try:
            cleaned_phone = validate_bangladeshi_phone(value)
            
            # Check if phone number is already taken by another user
            if self.instance:
                existing_user = User.objects.filter(phone_number=cleaned_phone).exclude(id=self.instance.id).first()
            else:
                existing_user = User.objects.filter(phone_number=cleaned_phone).first()
            
            if existing_user:
                raise serializers.ValidationError("A user with this phone number already exists.")
            
            return cleaned_phone
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        if self.instance:
            existing_user = User.objects.filter(email=value).exclude(id=self.instance.id).first()
        else:
            existing_user = User.objects.filter(email=value).first()
        
        if existing_user:
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def validate_name(self, value):
        if self.instance:
            existing_role = Role.objects.filter(name=value).exclude(id=self.instance.id).first()
        else:
            existing_role = Role.objects.filter(name=value).first()
        
        if existing_role:
            raise serializers.ValidationError("A role with this name already exists.")
        
        return value.strip()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'phone_number', 'password', 'password_confirm'
        )
    
    def validate_phone_number(self, value):
        try:
            cleaned_phone = validate_bangladeshi_phone(value)
            
            if User.objects.filter(phone_number=cleaned_phone).exists():
                raise serializers.ValidationError("A user with this phone number already exists.")
            
            return cleaned_phone
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        
        return value
    
    def validate(self, attrs):
        # Validate password confirmation
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match.'
            })
        
        # Remove password_confirm from validated data
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        # Create user with null role (equivalent to old Guest role)
        user = User.objects.create_user(**validated_data)
        return user