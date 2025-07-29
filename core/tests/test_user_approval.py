import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import User, Notification

class UserApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
            is_active=True,
            is_approved=False,
            payment_verified=False
        )

    def test_user_can_login_after_registration(self):
        login = self.client.login(username='testuser', password='testpass')
        self.assertTrue(login)

    def test_payment_proof_upload_on_dashboard(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('dashboard')
        with tempfile.NamedTemporaryFile(suffix='.jpg') as tmpfile:
            tmpfile.write(b'Test image content')
            tmpfile.seek(0)
            response = self.client.post(url, {
                'payment_proof': SimpleUploadedFile(tmpfile.name, tmpfile.read(), content_type='image/jpeg')
            }, follow=True)
        self.assertContains(response, 'Payment proof uploaded successfully')
        user = User.objects.get(username='testuser')
        self.assertFalse(user.payment_verified)
        self.assertTrue(user.payment_proof.name.endswith('.jpg'))

    def test_admin_can_approve_users(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('admin:core_user_changelist')
        response = self.client.post(url, {
            'action': 'approve_users',
            '_selected_action': [self.user.pk],
        }, follow=True)
        self.assertContains(response, '1 user(s) successfully approved.')
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.is_approved)
        self.assertTrue(user.is_active)

    def test_notification_created_on_registration(self):
        user_count_before = Notification.objects.count()
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'role': 'student',
        }, follow=True)
        user_count_after = Notification.objects.count()
        self.assertEqual(user_count_after, user_count_before + 1)
        self.assertContains(response, 'Registration successful. You can now login.')
