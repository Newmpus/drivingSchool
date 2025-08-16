"""
Lesson related views for the core app.
"""
import logging
import random
from datetime import timedelta, date, time
from typing import Dict, Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from ..forms import LessonBookingForm
from ..models import User, Lesson, Notification, Vehicle, VehicleAllocation, StudentProgress
from .auth_views import get_user_profile

logger = logging.getLogger(__name__)

def send_notification(user, message: str) -> None:
    """
    Send a notification to a user via database and email.
    
    Args:
        user: The user to send the notification to.
        message (str): The notification message.
    """
    Notification.objects.create(user=user, message=message)
    if user.email:
        try:
            send_mail(
                subject='Driving School Notification',
                message=message,
                from_email=None,
                recipient_list=[user.email],
                fail_silently=True,
            )
            logger.info(f"Email notification sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")

def allocate_vehicle_to_lesson(lesson: Lesson, student_class: str = 'class1') -> VehicleAllocation:
    """
    Automatically allocate an appropriate vehicle to a lesson based on student class.
    
    Args:
        lesson (Lesson): The lesson to allocate a vehicle for.
        student_class (str): The driving class of the student.
    
    Returns:
        VehicleAllocation: The created vehicle allocation.
    """
    # Get available vehicles for the student's class
    available_vehicles = Vehicle.objects.filter(
        vehicle_class=student_class,
        is_available=True
    ).exclude(
        vehicleallocation__lesson__date=lesson.date,
        vehicleallocation__lesson__start_time__lt=lesson.end_time,
        vehicleallocation__lesson__end_time__gt=lesson.start_time
    )
    
    if available_vehicles.exists():
        vehicle = available_vehicles.first()
        allocation = VehicleAllocation.objects.create(
            lesson=lesson,
            vehicle=vehicle
        )
        logger.info(f"Vehicle {vehicle.registration_number} allocated to lesson {lesson.id}")
        return allocation
    
    # If no specific class vehicle available, try any available vehicle
    any_available = Vehicle.objects.filter(
        is_available=True
    ).exclude(
        vehicleallocation__lesson__date=lesson.date,
        vehicleallocation__lesson__start_time__lt=lesson.end_time,
        vehicleallocation__lesson__end_time__gt=lesson.start_time
    )
    
    if any_available.exists():
        vehicle = any_available.first()
        allocation = VehicleAllocation.objects.create(
            lesson=lesson,
            vehicle=vehicle
        )
        logger.info(f"Fallback vehicle {vehicle.registration_number} allocated to lesson {lesson.id}")
        return allocation
    
    logger.warning(f"No vehicle available for lesson {lesson.id}")
    return None

def send_progress_email(student: User, lesson: Lesson, progress_data: dict) -> None:
    """
    Send progress email to student after lesson completion.
    
    Args:
        student (User): The student to send the email to.
        lesson (Lesson): The completed lesson.
        progress_data (dict): Progress information including skills covered and feedback.
    """
    if not student.email:
        logger.warning(f"Student {student.username} has no email address")
        return
    
    subject = f"Lesson Progress Update - {lesson.date}"
    
    # Create email content
    message = f"""
    Dear {student.first_name or student.username},
    
    Great job on your driving lesson today! Here are the details:
    
    Lesson Date: {lesson.date}
    Time: {lesson.start_time} - {lesson.end_time}
    Instructor: {lesson.tutor.get_full_name() or lesson.tutor.username}
    
    Skills Covered:
    {progress_data.get('skills_covered', 'Basic driving techniques')}
    
    Progress Notes:
    {progress_data.get('progress_notes', 'Good progress made today')}
    
    Instructor Feedback:
    {progress_data.get('instructor_feedback', 'Keep up the good work!')}
    
    Next Lesson Focus:
    {progress_data.get('next_lesson_focus', 'Continue practicing current skills')}
    
    Vehicle Used:
    {lesson.vehicle_allocation.vehicle.registration_number if hasattr(lesson, 'vehicle_allocation') else 'Not specified'}
    
    Keep practicing and stay safe on the roads!
    
    Best regards,
    Smart Driving School Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info(f"Progress email sent to {student.email}")
    except Exception as e:
        logger.error(f"Failed to send progress email to {student.email}: {e}")

@login_required
def book_lesson(request: HttpRequest) -> HttpResponse:
    """
    Handle lesson booking for students.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: The HTTP response, either the booking form or a redirect.
    """
    user_profile = get_user_profile(request.user)
    if not user_profile or user_profile.role != 'student':
        messages.error(request, 'Only students can book lessons.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = LessonBookingForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            
            # Check for scheduling conflicts
            tutor_conflict = Lesson.objects.filter(
                tutor=lesson.tutor,
                date=lesson.date,
                start_time__lt=lesson.end_time,
                end_time__gt=lesson.start_time
            ).exists()
            
            student_conflict = Lesson.objects.filter(
                student=user_profile,
                date=lesson.date,
                start_time__lt=lesson.end_time,
                end_time__gt=lesson.start_time
            ).exists()
            
            if tutor_conflict or student_conflict:
                messages.error(
                    request,
                    'This time slot is already booked for you or the tutor.'
                )
            else:
                lesson.student = user_profile
                lesson.save()
                
                # Allocate vehicle based on student class
                student_class = request.POST.get('student_class', 'class1')
                vehicle_allocation = allocate_vehicle_to_lesson(lesson, student_class)
                
                if vehicle_allocation:
                    vehicle_message = f"Vehicle {vehicle_allocation.vehicle.registration_number} allocated."
                else:
                    vehicle_message = "No vehicle available for this time slot."
                
                # Send notifications
                send_notification(
                    lesson.tutor,
                    f'New lesson booked by {request.user.username} '
                    f'on {lesson.date} at {lesson.start_time}. {vehicle_message}'
                )
                send_notification(
                    request.user,
                    f'Lesson booked with {lesson.tutor.username} '
                    f'on {lesson.date} at {lesson.start_time}. {vehicle_message}'
                )
                
                messages.success(request, f'Lesson booked successfully! {vehicle_message}')
                logger.info(
                    f"Lesson booked: {lesson.student.username} "
                    f"with {lesson.tutor.username} on {lesson.date}"
                )
                return redirect('dashboard')
    else:
        form = LessonBookingForm()
    
    return render(request, 'book_lesson.html', {'form': form})

@login_required
def lesson_detail(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """
    Display lesson details.
    
    Args:
        request (HttpRequest): The HTTP request object.
        lesson_id (int): The ID of the lesson to display.
    
    Returns:
        HttpResponse: The rendered lesson detail template.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user_profile = get_user_profile(request.user)
    
    # Check permissions
    if not user_profile or (
        user_profile.role != 'admin' and
        lesson.student != user_profile and
        lesson.tutor != user_profile
    ):
        messages.error(request, 'You do not have permission to view this lesson.')
        return redirect('dashboard')
    
    return render(request, 'lesson_detail.html', {'lesson': lesson})

@login_required
def cancel_lesson(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """
    Handle lesson cancellation.
    
    Args:
        request (HttpRequest): The HTTP request object.
        lesson_id (int): The ID of the lesson to cancel.
    
    Returns:
        HttpResponse: The HTTP response, either the cancel form or a redirect.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user_profile = get_user_profile(request.user)
    
    # Check permissions
    if not user_profile or (
        user_profile.role != 'admin' and
        lesson.student != user_profile and
        lesson.tutor != user_profile
    ):
        messages.error(request, 'You do not have permission to cancel this lesson.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        send_notification(
            lesson.student,
            f'Lesson on {lesson.date} at {lesson.start_time} has been cancelled.'
        )
        send_notification(
            lesson.tutor,
            f'Lesson on {lesson.date} at {lesson.start_time} has been cancelled.'
        )
        
        logger.info(
            f"Lesson cancelled: {lesson.student.username} "
            f"with {lesson.tutor.username} on {lesson.date}"
        )
        lesson.delete()
        messages.success(request, 'Lesson cancelled.')
        return redirect('dashboard')
    
    return render(request, 'cancel_lesson.html', {'lesson': lesson})

class LessonRescheduleForm(LessonBookingForm):
    """Form for rescheduling lessons."""
    class Meta(LessonBookingForm.Meta):
        fields = ['date', 'start_time', 'end_time', 'location']

@login_required
def reschedule_lesson(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """
    Handle lesson rescheduling.
    
    Args:
        request (HttpRequest): The HTTP request object.
        lesson_id (int): The ID of the lesson to reschedule.
    
    Returns:
        HttpResponse: The HTTP response, either the reschedule form or a redirect.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user_profile = get_user_profile(request.user)
    
    # Check permissions
    if not user_profile or (
        user_profile.role != 'admin' and
        lesson.student != user_profile and
        lesson.tutor != user_profile
    ):
        messages.error(request, 'You do not have permission to reschedule this lesson.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LessonRescheduleForm(request.POST, instance=lesson)
        if form.is_valid():
            new_lesson = form.save(commit=False)
            
            # Check for conflicts (excluding current lesson)
            tutor_conflict = Lesson.objects.filter(
                tutor=new_lesson.tutor,
                date=new_lesson.date,
                start_time__lt=new_lesson.end_time,
                end_time__gt=new_lesson.start_time
            ).exclude(id=lesson.id).exists()
            
            student_conflict = Lesson.objects.filter(
                student=new_lesson.student,
                date=new_lesson.date,
                start_time__lt=new_lesson.end_time,
                end_time__gt=new_lesson.start_time
            ).exclude(id=lesson.id).exists()
            
            if tutor_conflict or student_conflict:
                messages.error(
                    request,
                    'This time slot is already booked for you or the tutor.'
                )
            else:
                form.save()
                send_notification(
                    lesson.student,
                    f'Lesson has been rescheduled to {lesson.date} at {lesson.start_time}.'
                )
                send_notification(
                    lesson.tutor,
                    f'Lesson has been rescheduled to {lesson.date} at {lesson.start_time}.'
                )
                
                logger.info(
                    f"Lesson rescheduled: {lesson.student.username} "
                    f"with {lesson.tutor.username} to {lesson.date}"
                )
                messages.success(request, 'Lesson rescheduled.')
                return redirect(reverse('lesson_detail', args=[lesson.id]))
    else:
        form = LessonRescheduleForm(instance=lesson)
    
    return render(request, 'reschedule_lesson.html', {'form': form, 'lesson': lesson})

@login_required
def generate_timetable(request: HttpRequest) -> HttpResponse:
    """
    Generate automatic timetable for the next 5 weekdays (admin only).
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: Redirect to dashboard with success/error message.
    """
    user_profile = get_user_profile(request.user)
    if not user_profile or user_profile.role != 'admin':
        messages.error(request, 'Only admins can generate timetables.')
        return redirect('dashboard')
    
    # Generate timetable for the next 5 weekdays
    today = date.today()
    weekdays = [
        today + timedelta(days=i)
        for i in range(5)
        if (today + timedelta(days=i)).weekday() < 5
    ]
    
    from ..models import User  # ensure User is imported for this scope if needed
    students = list(User.objects.filter(role='student'))
    tutors = list(User.objects.filter(role='tutor'))
    slot_start = time(10, 0)
    slot_end = time(11, 0)
    created_count = 0
    
    for lesson_date in weekdays:
        for student in students:
            # Skip if student already has a lesson at this time
            if Lesson.objects.filter(
                student=student,
                date=lesson_date,
                start_time=slot_start
            ).exists():
                continue
            
            # Find available tutors
            available_tutors = [
                t for t in tutors
                if not Lesson.objects.filter(
                    tutor=t,
                    date=lesson_date,
                    start_time=slot_start
                ).exists()
            ]
            
            if available_tutors:
                tutor = random.choice(available_tutors)
                lesson = Lesson.objects.create(
                    student=student,
                    tutor=tutor,
                    date=lesson_date,
                    start_time=slot_start,
                    end_time=slot_end,
                    location='Driving School HQ'
                )
                
                send_notification(
                    student,
                    f'Lesson scheduled with {tutor.username} '
                    f'on {lesson_date} at {slot_start}.'
                )
                send_notification(
                    tutor,
                    f'Lesson scheduled with {student.username} '
                    f'on {lesson_date} at {slot_start}.'
                )
                created_count += 1
    
    logger.info(f"Generated {created_count} lessons for the week")
    messages.success(request, f'Generated {created_count} lessons for the week.')
    return redirect('dashboard')
