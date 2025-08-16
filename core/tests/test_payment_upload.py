"""
Tests for payment proof upload functionality.
"""
import os
import tempfile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

User = get_user_model()

class PaymentUploadTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            role='student'
        )
        self.client.login(username='teststudent', password='testpass123')
        
    def test_upload_payment_proof_success(self):
        """Test successful payment proof upload."""
        # Create a test file
        test_file = SimpleUploadedFile(
            "test_payment.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        
        response = self.client.post('/upload-payment/', {
            'payment_proof': test_file,
        })
        
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Check file was uploaded
        self.student.refresh_from_db()
        self.assertIsNotNone(self.student.payment_proof)
        
    def test_upload_large_file_rejection(self):
        """Test rejection of large files."""
        # Create a large test file (6MB)
        large_content = b"x" * (6 * 1024 * 1024)
        test_file = SimpleUploadedFile(
            "large_payment.jpg",
            large_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post('/upload-payment/', {
            'payment_proof': test_file,
        })
        
        self.assertEqual(response.status_code, 200)  # Should show form with error
        
    def test_upload_invalid_file_type(self):
        """Test rejection of invalid file types."""
        test_file = SimpleUploadedFile(
            "test_payment.exe",
            b"executable_content",
            content_type="application/x-msdownload"
        )
        
        response = self.client.post('/upload-payment/', {
            'payment_proof': test_file,
        })
        
        self.assertEqual(response.status_code, 200)  # Should show form with error
