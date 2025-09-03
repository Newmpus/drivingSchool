"""
Test for system functionality as described in documentation.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class SystemFunctionalityTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_registration_login_and_dashboard_access(self):
        """
        Test the complete user journey: registration, login, and dashboard access.
        This verifies core system functionality as per documentation.
        """
        # Step 1: Register a new user
        registration_data = {
            'username': 'testuser_functional',
            'email': 'testuser_functional@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'student',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890'
        }
        response = self.client.post(reverse('register'), registration_data)
        self.assertEqual(response.status_code, 302)  # Should redirect to login

        # Verify user was created
        user = User.objects.get(username='testuser_functional')
        self.assertEqual(user.email, 'testuser_functional@example.com')
        self.assertTrue(user.is_active)

        # Step 2: Login with the new user
        login_data = {
            'username': 'testuser_functional',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('login'), login_data)
        self.assertEqual(response.status_code, 302)  # Should redirect after login

        # Step 3: Access dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)  # Dashboard should load successfully
        self.assertContains(response, 'Dashboard')  # Check if dashboard content is present
