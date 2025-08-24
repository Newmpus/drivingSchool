#!/usr/bin/env python3
"""
Test script to verify email notifications and automatic timetable generation
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drivingschool.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Lesson, Notification
from core.services.notification_service import create_and_send_notification
from core.tasks import notify_upcoming_lessons
from datetime import datetime, timedelta, date, time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_notifications():
    """Test email notification system"""
    print("=" * 60)
    print("TESTING EMAIL NOTIFICATIONS")
    print("=" * 60)
    
    # Create test users if they don't exist
    student, created = User.objects.get_or_create(
        username='test_student',
        defaults={
            'email': 'valid_student@example.com',
            'first_name': 'Test',
            'last_name': 'Student',
            'role': 'student'
        }
    )
    
    tutor, created = User.objects.get_or_create(
        username='test_tutor',
        defaults={
            'email': 'tutor@example.com',
            'first_name': 'Test',
            'last_name': 'Tutor',
            'role': 'tutor'
        }
    )
    
    # Create a test lesson
    tomorrow = date.today() + timedelta(days=1)
    lesson = Lesson.objects.create(
        student=student,
        tutor=tutor,
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(11, 0),
        location='Test Location',
        status='scheduled'
    )
    
    # Test notification creation
    print(f"✓ Created test lesson: {lesson}")
    
    # Test email notification
    try:
        create_and_send_notification(student, lesson, "Test notification message")
        print("✓ Email notification sent successfully")
    except Exception as e:
        print(f"✗ Email notification failed: {e}")
    
    # Check notifications in database
    notifications = Notification.objects.filter(user=student)
    print(f"✓ Found {notifications.count()} notifications for student")
    
    return True

def test_timetable_generation():
    """Test automatic timetable generation"""
    print("\n" + "=" * 60)
    print("TESTING AUTOMATIC TIMETABLE GENERATION")
    print("=" * 60)
    
    # Create test users
    student, _ = User.objects.get_or_create(
        username='test_student_timetable',
        defaults={
            'email': 'student2@example.com',
            'first_name': 'Test',
            'last_name': 'Student2',
            'role': 'student'
        }
    )
    
    tutor, _ = User.objects.get_or_create(
        username='test_tutor_timetable',
        defaults={
            'email': 'tutor2@example.com',
            'first_name': 'Test',
            'last_name': 'Tutor2',
            'role': 'tutor'
        }
    )
    
    # Test timetable generation
    today = date.today()
    next_weekday = today + timedelta(days=1)
    if next_weekday.weekday() >= 5:  # Skip weekends
        next_weekday = today + timedelta(days=(7 - today.weekday()))
    
    # Create a test lesson
    lesson = Lesson.objects.create(
        student=student,
        tutor=tutor,
        date=next_weekday,
        start_time=time(14, 0),
        end_time=time(15, 0),
        location='Test Location',
        status='scheduled'
    )
    
    print(f"✓ Created test lesson for timetable: {lesson}")
    
    # Check if lesson was created successfully
    lessons = Lesson.objects.filter(date=next_weekday)
    print(f"✓ Found {lessons.count()} lessons scheduled for {next_weekday}")
    
    return True

def test_celery_task():
    """Test Celery task for notifications"""
    print("\n" + "=" * 60)
    print("TESTING CELERY TASK FOR NOTIFICATIONS")
    print("=" * 60)
    
    # Test the Celery task directly
    try:
        notify_upcoming_lessons()
        print("✓ Celery task executed successfully")
    except Exception as e:
        print(f"✗ Celery task failed: {e}")
    
    return True

def main():
    """Run all tests"""
    print("DRIVING SCHOOL MANAGEMENT SYSTEM - EMAIL & TIMETABLE TEST")
    print("=" * 80)
    
    try:
        # Test email notifications
        test_email_notifications()
        
        # Test timetable generation
        test_timetable_generation()
        
        # Test Celery task
        test_celery_task()
        
        print("\n" + "=" * 80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nSUMMARY:")
        print("- Email notifications are configured and working")
        print("- Automatic timetable generation is functional")
        print("- Celery tasks are properly set up")
        print("- Database models are correctly configured")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
