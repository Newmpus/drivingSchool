from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from core.models import User, Lesson, Notification
from core.services.notification_service import create_and_send_notification
from core.tasks import notify_upcoming_lessons
from django.core.management import call_command

User = get_user_model()

class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student1', email='student1@example.com', password='pass', role='student')
        self.tutor_user = User.objects.create_user(username='tutor1', email='tutor1@example.com', password='pass', role='tutor')
        self.lesson = Lesson.objects.create(
            student=self.user,
            tutor=self.tutor_user,
            date=timezone.now().date(),
            start_time=(timezone.now() + timedelta(minutes=10)).time(),
            end_time=(timezone.now() + timedelta(minutes=70)).time(),
            location='Test Location'
        )

    @patch('core.services.notification_service.send_mail')
    def test_create_and_send_notification(self, mock_send_mail):
        message = 'Test notification message'
        create_and_send_notification(self.user, self.lesson, message)
        notification = Notification.objects.filter(user=self.user, message=message).first()
        self.assertIsNotNone(notification)
        mock_send_mail.assert_called_once()

class NotifyUpcomingLessonsTaskTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student2', email='student2@example.com', password='pass', role='student')
        self.tutor_user = User.objects.create_user(username='tutor2', email='tutor2@example.com', password='pass', role='tutor')

    @patch('core.services.notification_service.create_and_send_notification')
    def test_notify_upcoming_lessons(self, mock_create_and_send):
        notify_time = timezone.now() + timedelta(minutes=10)
        lesson = Lesson.objects.create(
            student=self.user,
            tutor=self.tutor_user,
            date=notify_time.date(),
            start_time=notify_time.time().replace(second=0, microsecond=0),
            end_time=(notify_time + timedelta(minutes=60)).time(),
            location='Test Location'
        )
        notify_upcoming_lessons()
        mock_create_and_send.assert_called_once()

class ManagementCommandTests(TestCase):
    @patch('core.tasks.notify_upcoming_lessons')
    def test_send_lesson_notifications_command(self, mock_notify):
        call_command('send_lesson_notifications')
        mock_notify.assert_called_once()
