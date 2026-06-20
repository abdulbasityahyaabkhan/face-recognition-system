from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import CustomUser, Role, Permission
import json

class UserRegistrationTestCase(APITestCase):
    """Test user registration"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
    
    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass@123456',
            'password_confirm': 'TestPass@123456'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_password_mismatch(self):
        """Test password mismatch"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass@123456',
            'password_confirm': 'DifferentPass@123456'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_weak_password(self):
        """Test weak password validation"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'weak',
            'password_confirm': 'weak'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_duplicate_username(self):
        """Test duplicate username"""
        CustomUser.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='TestPass@123456'
        )
        data = {
            'username': 'testuser',
            'email': 'new@example.com',
            'password': 'TestPass@123456',
            'password_confirm': 'TestPass@123456'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserLoginTestCase(APITestCase):
    """Test user login"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass@123456'
        )
        self.user.is_verified = True
        self.user.save()
    
    def test_login_with_username(self):
        """Test login with username"""
        data = {
            'username': 'testuser',
            'password': 'TestPass@123456'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_with_email(self):
        """Test login with email"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass@123456'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_credentials(self):
        """Test invalid credentials"""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_locked_account(self):
        """Test locked account"""
        self.user.is_locked = True
        self.user.save()
        data = {
            'username': 'testuser',
            'password': 'TestPass@123456'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class PasswordChangeTestCase(APITestCase):
    """Test password change"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass@123456'
        )
        self.client.force_authenticate(user=self.user)
        self.password_change_url = reverse('password_change')
    
    def test_successful_password_change(self):
        """Test successful password change"""
        data = {
            'old_password': 'OldPass@123456',
            'new_password': 'NewPass@654321',
            'new_password_confirm': 'NewPass@654321'
        }
        response = self.client.post(self.password_change_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_wrong_old_password(self):
        """Test wrong old password"""
        data = {
            'old_password': 'WrongPass@123456',
            'new_password': 'NewPass@654321',
            'new_password_confirm': 'NewPass@654321'
        }
        response = self.client.post(self.password_change_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class OTPTestCase(APITestCase):
    """Test OTP functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.otp_request_url = reverse('otp_request')
        self.otp_verify_url = reverse('otp_verify')
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone_number='1234567890',
            password='TestPass@123456'
        )
    
    def test_otp_request_email(self):
        """Test OTP request via email"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_otp_request_phone(self):
        """Test OTP request via phone"""
        data = {'phone_number': '1234567890'}
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_no_delivery_method(self):
        """Test OTP request without delivery method"""
        data = {}
        response = self.client.post(self.otp_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class PasswordResetTestCase(APITestCase):
    """Test password reset"""
    
    def setUp(self):
        self.client = APIClient()
        self.reset_request_url = reverse('password_reset')
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass@123456'
        )
    
    def test_password_reset_request(self):
        """Test password reset request"""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.reset_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_email(self):
        """Test reset with invalid email"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.reset_request_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class PermissionTestCase(APITestCase):
    """Test permission system"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create roles and permissions
        self.perm = Permission.objects.create(
            name='view_students',
            description='Can view students'
        )
        self.role = Role.objects.create(
            name='admin',
            description='Administrator'
        )
        self.role.permissions.add(self.perm)
        
        # Create user with role
        self.user = CustomUser.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='AdminPass@123456'
        )
        self.user.role = self.role
        self.user.is_verified = True
        self.user.save()
    
    def test_user_has_permission(self):
        """Test user has permission"""
        self.assertTrue(
            self.user.role.permissions.filter(name='view_students').exists()
        )
    
    def test_user_no_permission(self):
        """Test user does not have permission"""
        self.assertFalse(
            self.user.role.permissions.filter(name='delete_students').exists()
        )
