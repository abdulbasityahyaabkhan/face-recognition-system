from rest_framework import status, viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import CustomUser, Role, Permission, UserActivity
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    OTPVerificationSerializer,
    OTPRequestSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserActivitySerializer,
)
from .permissions import (
    IsVerifiedUser,
    IsNotLocked,
    CanManageUsers,
    CanViewReports,
)
from .utils import (
    OTPGenerator,
    EmailVerificationToken,
    PasswordResetToken,
    LoginAttemptTracker,
    SessionManager,
    AuditLogger,
)
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send email verification
        EmailVerificationToken.send_verification_email(user, request)
        
        # Log registration
        AuditLogger.log_action(
            user=user,
            action='create',
            description=f'User registered: {user.username}',
            request=request,
            object_type='user',
            object_id=user.id
        )
        
        return Response({
            'message': 'User registered successfully. Please verify your email.',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class UserLoginView(generics.GenericAPIView):
    """User login endpoint"""
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data.get('user')
        
        # Check if user is locked
        if user.is_locked:
            return Response({
                'error': 'Account is locked. Please contact administrator.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Reset failed attempts
        LoginAttemptTracker.reset_failed_attempts(user)
        
        # Create session
        session_id = SessionManager.create_session(user, request)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Log login
        AuditLogger.log_action(
            user=user,
            action='login',
            description=f'User logged in from {SessionManager.get_client_ip(request)}',
            request=request,
            object_type='user',
            object_id=user.id
        )
        
        # Update last login
        user.last_login_ip = SessionManager.get_client_ip(request)
        user.save()
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'session_id': session_id,
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)

class UserLogoutView(generics.GenericAPIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        
        # Log logout
        AuditLogger.log_action(
            user=user,
            action='logout',
            description='User logged out',
            request=request,
            object_type='user',
            object_id=user.id
        )
        
        return Response({
            'message': 'Logged out successfully.'
        }, status=status.HTTP_200_OK)

class PasswordChangeView(generics.GenericAPIView):
    """Password change endpoint"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated, IsNotLocked]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Old password is incorrect.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log password change
        AuditLogger.log_action(
            user=user,
            action='update',
            description='User changed password',
            request=request,
            object_type='user',
            object_id=user.id
        )
        
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)

class PasswordResetRequestView(generics.GenericAPIView):
    """Password reset request endpoint"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        
        # Send reset email
        PasswordResetToken.send_reset_email(user)
        
        return Response({
            'message': 'Password reset link sent to your email.'
        }, status=status.HTTP_200_OK)

class PasswordResetConfirmView(generics.GenericAPIView):
    """Password reset confirmation endpoint"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        # Verify token and get user
        user = PasswordResetToken.verify_token(token)
        if not user:
            return Response({
                'error': 'Invalid or expired token.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Log password reset
        AuditLogger.log_action(
            user=user,
            action='update',
            description='User reset password',
            request=request,
            object_type='user',
            object_id=user.id
        )
        
        return Response({
            'message': 'Password reset successfully.'
        }, status=status.HTTP_200_OK)

class EmailVerificationView(generics.GenericAPIView):
    """Email verification endpoint"""
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        try:
            uid_str, token_str = token.split('-', 1)
            user = EmailVerificationToken.verify_token(uid_str, token_str)
            
            if not user:
                return Response({
                    'error': 'Invalid or expired token.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_verified = True
            user.save()
            
            # Log email verification
            AuditLogger.log_action(
                user=user,
                action='update',
                description='User verified email',
                request=request,
                object_type='user',
                object_id=user.id
            )
            
            return Response({
                'message': 'Email verified successfully.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Email verification failed: {str(e)}")
            return Response({
                'error': 'Email verification failed.'
            }, status=status.HTTP_400_BAD_REQUEST)

class OTPRequestView(generics.GenericAPIView):
    """OTP request endpoint"""
    serializer_class = OTPRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone_number')
        
        # Generate OTP
        otp = OTPGenerator.generate_otp()
        
        # Cache OTP for 5 minutes
        if email:
            cache.set(f"otp_email_{email}", otp, 300)
            user = CustomUser.objects.filter(email=email).first()
            OTPGenerator.send_otp_email(email, otp, user)
        elif phone:
            cache.set(f"otp_phone_{phone}", otp, 300)
            user = CustomUser.objects.filter(phone_number=phone).first()
            OTPGenerator.send_otp_sms(phone, otp, user)
        
        return Response({
            'message': 'OTP sent successfully.',
            'delivery_method': 'email' if email else 'sms'
        }, status=status.HTTP_200_OK)

class OTPVerificationView(generics.GenericAPIView):
    """OTP verification endpoint"""
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone_number')
        otp = serializer.validated_data.get('otp')
        
        # Verify OTP
        if email:
            cached_otp = cache.get(f"otp_email_{email}")
            if not cached_otp or cached_otp != otp:
                return Response({
                    'error': 'Invalid or expired OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            cache.delete(f"otp_email_{email}")
        elif phone:
            cached_otp = cache.get(f"otp_phone_{phone}")
            if not cached_otp or cached_otp != otp:
                return Response({
                    'error': 'Invalid or expired OTP.'
                }, status=status.HTTP_400_BAD_REQUEST)
            cache.delete(f"otp_phone_{phone}")
        
        return Response({
            'message': 'OTP verified successfully.',
            'verified': True
        }, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsNotLocked]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserProfileSerializer
        return UserUpdateSerializer
    
    def perform_update(self, serializer):
        user = serializer.save()
        
        # Log profile update
        AuditLogger.log_action(
            user=user,
            action='update',
            description='User updated profile',
            request=self.request,
            object_type='user',
            object_id=user.id
        )

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Role viewset"""
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Permission viewset"""
    queryset = Permission.objects.filter(is_active=True)
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]

class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """User activity viewset"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role and user.role.permissions.filter(name='manage_system').exists():
            return UserActivity.objects.all().order_by('-created_at')
        return UserActivity.objects.filter(user=user).order_by('-created_at')

class SessionManagementView(generics.GenericAPIView):
    """Session management endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get all active sessions"""
        sessions = SessionManager.get_active_sessions(request.user)
        return Response({
            'active_sessions': sessions
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, *args, **kwargs):
        """Logout all sessions"""
        SessionManager.logout_all_sessions(request.user)
        return Response({
            'message': 'All sessions logged out.'
        }, status=status.HTTP_200_OK)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token obtain pair view"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]
