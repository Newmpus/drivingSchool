"""
Views package for the core app.
"""

from .auth_views import register, dashboard, edit_profile
from .lesson_views import (
    book_lesson, lesson_detail, cancel_lesson, reschedule_lesson,
    generate_timetable, api_book_lesson
)
from .notification_views import mark_notification_read

__all__ = [
    'register', 'dashboard', 'edit_profile',
    'book_lesson', 'lesson_detail', 'cancel_lesson', 'reschedule_lesson',
    'generate_timetable', 'api_book_lesson', 'mark_notification_read'
]
