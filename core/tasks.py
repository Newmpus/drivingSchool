from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from core.models import Lesson
from core.services.notification_service import create_and_send_notification

@shared_task
def notify_upcoming_lessons():
    now = timezone.now()
    notify_time = (now + timedelta(minutes=10)).replace(second=0, microsecond=0)
    lessons = Lesson.objects.filter(
        date=notify_time.date(),
        start_time__hour=notify_time.hour,
        start_time__minute=notify_time.minute
    )
    for lesson in lessons:
        user = lesson.student
        message = f"Reminder: Your driving lesson with {lesson.tutor.get_full_name()} starts at {lesson.start_time.strftime('%H:%M')}."
        create_and_send_notification(user, lesson, message)
