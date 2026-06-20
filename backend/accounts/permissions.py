from rest_framework import permissions
from django.contrib.auth.models import Permission as DjangoPermission

class IsAuthenticated(permissions.IsAuthenticated):
    """Custom authenticated permission"""
    message = "Authentication required. Please log in."

class IsAdminUser(permissions.IsAdminUser):
    """Admin user permission"""
    message = "Admin access required."

class IsVerifiedUser(permissions.BasePermission):
    """Only verified users can access"""
    message = "Account verification required."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified

class IsNotLocked(permissions.BasePermission):
    """Account must not be locked"""
    message = "Your account is locked. Contact administrator."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and not request.user.is_locked

class HasRolePermission(permissions.BasePermission):
    """Check if user has specific role"""
    def has_permission(self, request, view):
        required_role = getattr(view, 'required_role', None)
        if not required_role:
            return True
        return request.user and request.user.is_authenticated and request.user.role and request.user.role.name == required_role

class HasCustomPermission(permissions.BasePermission):
    """Check if user has specific custom permission"""
    def has_permission(self, request, view):
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True
        
        if not (request.user and request.user.is_authenticated):
            return False
        
        if not request.user.role:
            return False
        
        return request.user.role.permissions.filter(name=required_permission).exists()

class CanManageUsers(permissions.BasePermission):
    """Permission to manage users"""
    message = "You do not have permission to manage users."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role and request.user.role.permissions.filter(name='manage_system').exists()

class CanViewReports(permissions.BasePermission):
    """Permission to view reports"""
    message = "You do not have permission to view reports."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role and request.user.role.permissions.filter(name='view_attendance').exists()

class CanManageCameras(permissions.BasePermission):
    """Permission to manage cameras"""
    message = "You do not have permission to manage cameras."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role and request.user.role.permissions.filter(name='manage_cameras').exists()

class CanViewAlerts(permissions.BasePermission):
    """Permission to view security alerts"""
    message = "You do not have permission to view alerts."
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role and request.user.role.permissions.filter(name='view_alerts').exists()
