from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _

class CustomJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication with enhanced error handling"""
    
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except AuthenticationFailed as e:
            raise AuthenticationFailed({
                'detail': 'Invalid or expired token.',
                'code': 'token_not_valid'
            })
