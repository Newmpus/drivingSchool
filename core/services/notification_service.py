from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.models import Notification, Lesson
from django.contrib.auth.models import User
from django.utils.timezone import now

def send_lesson_notification_email(user: User, lesson: Lesson, message: str) -> None:
    subject = 'Upcoming Driving Lesson Reminder'
    html_message = render_to_string('email/lesson_notification.html', {
        'user': user,
        'lesson': lesson,
        'message': message,
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def create_and_send_notification(user: User, lesson: Lesson, message: str) -> None:
    # Create notification in DB
    Notification.objects.create(user=user, message=message)
    # Send email notification
    send_lesson_notification_email(user, lesson, message)
