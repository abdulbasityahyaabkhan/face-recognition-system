import secrets
import string
import smtplib
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class OTPGenerator:
    """Generate and manage One-Time Passwords"""
    
    @staticmethod
    def generate_otp(length=6):
        """Generate random OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def send_otp_email(email, otp, user=None):
        """Send OTP via email"""
        try:
            subject = 'Your One-Time Password (OTP)'
            context = {
                'otp': otp,
                'user': user,
                'valid_minutes': 5
            }
            html_message = render_to_string('emails/otp_email.html', context)
            
            send_mail(
                subject,
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"OTP sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP to {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_sms(phone_number, otp, user=None):
        """Send OTP via SMS (Mock implementation)"""
        try:
            # Mock SMS implementation - replace with Twilio/AWS SNS in production
            logger.info(f"SMS OTP sent to {phone_number}: {otp}")
            print(f"\n{'='*50}")
            print(f"SMS OTP for {phone_number}")
            print(f"OTP: {otp}")
            print(f"Valid for: 5 minutes")
            print(f"{'='*50}\n")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS OTP to {phone_number}: {str(e)}")
            return False

class EmailVerificationToken:
    """Manage email verification tokens"""
    
    @staticmethod
    def generate_token(user):
        """Generate email verification token"""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f"{uid}-{token}"
    
    @staticmethod
    def verify_token(uid_str, token_str):
        """Verify email verification token"""
        try:
            uid = force_str(urlsafe_base64_decode(uid_str))
            from accounts.models import CustomUser
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token_str):
                return user
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
        return None
    
    @staticmethod
    def send_verification_email(user, request):
        """Send email verification link"""
        try:
            token = EmailVerificationToken.generate_token(user)
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}/"
            
            subject = 'Verify Your Email Address'
            context = {
                'user': user,
                'verification_url': verification_url,
                'valid_hours': 24
            }
            html_message = render_to_string('emails/email_verification.html', context)
            
            send_mail(
                subject,
                f'Please verify your email: {verification_url}',
                settings.EMAIL_HOST_USER,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

class PasswordResetToken:
    """Manage password reset tokens"""
    
    @staticmethod
    def generate_token(user):
        """Generate password reset token"""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return f"{uid}-{token}"
    
    @staticmethod
    def verify_token(token_str):
        """Verify password reset token"""
        try:
            uid_str, token = token_str.split('-', 1)
            uid = force_str(urlsafe_base64_decode(uid_str))
            from accounts.models import CustomUser
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return user
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
        return None
    
    @staticmethod
    def send_reset_email(user):
        """Send password reset email"""
        try:
            token = PasswordResetToken.generate_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}/"
            
            subject = 'Reset Your Password'
            context = {
                'user': user,
                'reset_url': reset_url,
                'valid_hours': 1
            }
            html_message = render_to_string('emails/password_reset.html', context)
            
            send_mail(
                subject,
                f'Reset your password: {reset_url}',
                settings.EMAIL_HOST_USER,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f"Password reset email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send reset email to {user.email}: {str(e)}")
            return False

class LoginAttemptTracker:
    """Track login attempts for account lockout"""
    
    @staticmethod
    def get_failed_attempts(user):
        """Get failed login attempts for a user"""
        from django.core.cache import cache
        return cache.get(f"failed_login_{user.id}", 0)
    
    @staticmethod
    def increment_failed_attempts(user):
        """Increment failed login attempts"""
        from django.core.cache import cache
        key = f"failed_login_{user.id}"
        attempts = cache.get(key, 0)
        attempts += 1
        cache.set(key, attempts, 3600)  # 1 hour
        
        if attempts >= 5:
            user.is_locked = True
            user.save()
            logger.warning(f"Account locked for user {user.username} after 5 failed attempts")
        
        return attempts
    
    @staticmethod
    def reset_failed_attempts(user):
        """Reset failed login attempts after successful login"""
        from django.core.cache import cache
        cache.delete(f"failed_login_{user.id}")
        
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.save()

class SessionManager:
    """Manage user sessions"""
    
    @staticmethod
    def create_session(user, request):
        """Create user session record"""
        from django.core.cache import cache
        import uuid
        
        session_id = str(uuid.uuid4())
        session_data = {
            'user_id': user.id,
            'username': user.username,
            'ip_address': SessionManager.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'login_time': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
        }
        
        cache.set(f"session_{session_id}", session_data, 86400)  # 24 hours
        return session_id
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def get_active_sessions(user):
        """Get all active sessions for user"""
        from django.core.cache import cache
        sessions = []
        for key in cache.keys(f"session_*"):
            session = cache.get(key)
            if session and session.get('user_id') == user.id:
                sessions.append({
                    'session_id': key.replace('session_', ''),
                    'ip_address': session.get('ip_address'),
                    'user_agent': session.get('user_agent'),
                    'login_time': session.get('login_time'),
                })
        return sessions
    
    @staticmethod
    def logout_all_sessions(user):
        """Logout all sessions for a user"""
        from django.core.cache import cache
        for key in cache.keys(f"session_*"):
            session = cache.get(key)
            if session and session.get('user_id') == user.id:
                cache.delete(key)
        logger.info(f"All sessions logged out for user {user.username}")

class AuditLogger:
    """Log user actions for audit trail"""
    
    @staticmethod
    def log_action(user, action, description, request=None, object_type=None, object_id=None):
        """Log user action"""
        from audit.models import AuditLog
        import uuid
        
        try:
            ip_address = SessionManager.get_client_ip(request) if request else None
            user_agent = request.META.get('HTTP_USER_AGENT', '') if request else ''
            
            AuditLog.objects.create(
                log_id=str(uuid.uuid4()),
                user=user,
                action=action,
                object_type=object_type or 'system',
                object_id=object_id or 'N/A',
                object_repr=description,
                ip_address=ip_address,
                user_agent=user_agent,
                description=description
            )
        except Exception as e:
            logger.error(f"Failed to log action: {str(e)}")
