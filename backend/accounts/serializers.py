from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, Role, Permission, UserActivity
import re

class PasswordValidator:
    """Custom password validator for strong passwords"""
    def validate(self, password):
        errors = []
        if len(password) < 12:
            errors.append('Password must be at least 12 characters long.')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter.')
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter.')
        if not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one digit.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character.')
        if errors:
            raise serializers.ValidationError(errors)
        return password

class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True, min_length=12)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        # Validate password strength
        validator = PasswordValidator()
        validator.validate(data['password'])
        
        return data
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered.")
        return value
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password'],
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    """User login serializer (username/email/phone)"""
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone_number')
        password = data.get('password')
        
        if not any([username, email, phone]):
            raise serializers.ValidationError("Username, email, or phone number required.")
        
        # Try to authenticate with username, email, or phone
        user = None
        if username:
            user = authenticate(username=username, password=password)
        elif email:
            try:
                user_obj = CustomUser.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                pass
        elif phone:
            try:
                user_obj = CustomUser.objects.get(phone_number=phone)
                user = authenticate(username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        
        if user.is_locked:
            raise serializers.ValidationError("Account is locked. Please contact administrator.")
        
        data['user'] = user
        return data

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with user info"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role.name if user.role else None
        token['is_verified'] = user.is_verified
        return token

class TokenRefreshSerializer(serializers.Serializer):
    """Token refresh serializer"""
    refresh = serializers.CharField()

class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        
        validator = PasswordValidator()
        validator.validate(data['new_password'])
        
        return data

class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            CustomUser.objects.get(email=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12)
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        
        validator = PasswordValidator()
        validator.validate(data['new_password'])
        
        return data

class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    token = serializers.CharField()

class OTPVerificationSerializer(serializers.Serializer):
    """OTP verification serializer"""
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6, min_length=6)

class OTPRequestSerializer(serializers.Serializer):
    """OTP request serializer"""
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    
    def validate(self, data):
        if not data.get('email') and not data.get('phone_number'):
            raise serializers.ValidationError("Email or phone number required.")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 
                  'role', 'role_name', 'is_verified', 'is_active', 'is_locked', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'role']

class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number']

class RoleSerializer(serializers.ModelSerializer):
    """Role serializer"""
    permissions_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permissions_list', 'is_active']
    
    def get_permissions_list(self, obj):
        return [p.get_name_display() for p in obj.permissions.all()]

class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer"""
    class Meta:
        model = Permission
        fields = ['id', 'name', 'description', 'is_active']

class UserActivitySerializer(serializers.ModelSerializer):
    """User activity serializer"""
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity_type', 'activity_type_display', 'description', 
                  'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['created_at']

class SessionSerializer(serializers.Serializer):
    """Session management serializer"""
    session_id = serializers.CharField()
    device_info = serializers.CharField()
    ip_address = serializers.IPAddressField()
    login_time = serializers.DateTimeField()
    last_activity = serializers.DateTimeField()
    is_current = serializers.BooleanField()
