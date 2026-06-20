from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerificationView,
    OTPRequestView,
    OTPVerificationView,
    UserProfileView,
    RoleViewSet,
    PermissionViewSet,
    UserActivityViewSet,
    SessionManagementView,
    CustomTokenObtainPairView,
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'activities', UserActivityViewSet, basename='activity')

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/obtain/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Management
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Verification
    path('verify/email/', EmailVerificationView.as_view(), name='email_verification'),
    path('otp/request/', OTPRequestView.as_view(), name='otp_request'),
    path('otp/verify/', OTPVerificationView.as_view(), name='otp_verify'),
    
    # User Management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('sessions/', SessionManagementView.as_view(), name='sessions'),
    
    # Routers
    path('', include(router.urls)),
]
