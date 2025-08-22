"""
Lesson related views for the core app.
"""
import logging
import random
from datetime import timedelta, date, time, datetime
from typing import Dict, Any, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from ..forms import LessonBookingForm, ProgressCommentForm, QuickProgressForm
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

def allocate_vehicle_to_lesson(lesson: Lesson, student_class: str = 'class1') -> Tuple[VehicleAllocation, Dict[str, Any]]:
    """
    Automatically allocate an appropriate vehicle to a lesson based on student class using AI suggestions.
    
    Args:
        lesson (Lesson): The lesson to allocate a vehicle for.
        student_class (str): The driving class of the student.
    
    Returns:
        Tuple[VehicleAllocation, Dict]: The created vehicle allocation and allocation info.
    """
    from ..ai_helper import ai_helper
    
    # Get AI suggestions for vehicle allocation
    suggestions = ai_helper.suggest_available_vehicles(
        lesson.date, lesson.start_time, lesson.end_time, student_class
    )
    
    allocation_info = {
        'success': False,
        'message': 'No vehicle available for this time slot.',
        'vehicle_info': None,
        'suggestions_count': len(suggestions),
        'recommendation': None
    }
    
    if suggestions:
        # Use the best suggestion (first in the sorted list)
        best_suggestion = suggestions[0]
        vehicle = best_suggestion['vehicle']
        
        try:
            allocation = VehicleAllocation.objects.create(
                lesson=lesson,
                vehicle=vehicle
            )
            
            allocation_info.update({
                'success': True,
                'message': f"Vehicle {vehicle.registration_number} allocated successfully!",
                'vehicle_info': {
                    'registration_number': vehicle.registration_number,
                    'make': vehicle.make,
                    'model': vehicle.model,
                    'vehicle_class': vehicle.get_vehicle_class_display(),
                    'vehicle_type': vehicle.get_vehicle_type_display()
                },
                'recommendation': best_suggestion['recommendation'],
                'confidence': best_suggestion['confidence']
            })
            
            logger.info(f"AI-suggested vehicle {vehicle.registration_number} allocated to lesson {lesson.id} "
                       f"(confidence: {best_suggestion['confidence']}%)")
            return allocation, allocation_info
            
        except Exception as e:
            logger.error(f"Error creating vehicle allocation: {str(e)}")
            allocation_info['message'] = f"Error allocating vehicle: {str(e)}"
    
    # If no suggestions or allocation failed
    logger.warning(f"No suitable vehicle available for lesson {lesson.id} on {lesson.date} "
                  f"{lesson.start_time}-{lesson.end_time} (class: {student_class})")
    
    # Provide helpful suggestions for alternative times
    if not suggestions:
        # Check if there are vehicles available at different times
        all_vehicles = Vehicle.objects.filter(vehicle_class=student_class, is_available=True)
        if all_vehicles.exists():
            allocation_info['message'] = (
                f"No {Vehicle.objects.filter(vehicle_class=student_class).first().get_vehicle_class_display()} "
                f"vehicles available at this time. Try a different time slot or contact admin."
            )
        else:
            allocation_info['message'] = (
                f"No {student_class} vehicles are currently available. "
                f"Please contact admin or try a different vehicle class."
            )
    
    return None, allocation_info

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
        print(f"DEBUG: Form data received: {request.POST}")
        print(f"DEBUG: Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG: Form errors: {form.errors}")
        
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
                vehicle_allocation, allocation_info = allocate_vehicle_to_lesson(lesson, student_class)
                
                vehicle_message = allocation_info['message']
                if allocation_info['recommendation']:
                    vehicle_message += f" ({allocation_info['recommendation']})"
                
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

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def api_book_lesson(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for booking lessons via HTTP POST requests.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        JsonResponse: JSON response with booking status and details.
    """
    user_profile = get_user_profile(request.user)
    if not user_profile or user_profile.role != 'student':
        return JsonResponse({
            'success': False,
            'error': 'Only students can book lessons.'
        }, status=403)

    try:
        # Parse form data
        tutor_id = request.POST.get('tutor')
        date_str = request.POST.get('date')
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        location = request.POST.get('location', 'Driving School HQ')
        student_class = request.POST.get('student_class', 'class1')

        # Validate required fields
        if not all([tutor_id, date_str, start_time_str, end_time_str]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields: tutor, date, start_time, end_time'
            }, status=400)

        # Parse date and time
        try:
            lesson_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = timezone.datetime.strptime(start_time_str, '%H:%M').time()
            end_time = timezone.datetime.strptime(end_time_str, '%H:%M').time()
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid date/time format: {str(e)}'
            }, status=400)

        # Validate date
        if lesson_date < timezone.now().date():
            return JsonResponse({
                'success': False,
                'error': 'Cannot book lessons in the past.'
            }, status=400)

        if lesson_date > timezone.now().date() + timedelta(days=90):
            return JsonResponse({
                'success': False,
                'error': 'Cannot book lessons more than 90 days in advance.'
            }, status=400)

        # Validate time
        if start_time >= end_time:
            return JsonResponse({
                'success': False,
                'error': 'End time must be after start time.'
            }, status=400)

        duration = datetime.combine(lesson_date, end_time) - datetime.combine(lesson_date, start_time)
        if duration.total_seconds() < 1800:  # 30 minutes
            return JsonResponse({
                'success': False,
                'error': 'Lesson must be at least 30 minutes long.'
            }, status=400)

        if duration.total_seconds() > 10800:  # 3 hours
            return JsonResponse({
                'success': False,
                'error': 'Lesson cannot be longer than 3 hours.'
            }, status=400)

        if start_time < time(8, 0) or end_time > time(18, 0):
            return JsonResponse({
                'success': False,
                'error': 'Lessons must be between 8:00 AM and 6:00 PM.'
            }, status=400)

        # Get tutor
        try:
            tutor = User.objects.get(id=tutor_id, role='tutor')
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid tutor ID or tutor not found.'
            }, status=400)

        # Check for scheduling conflicts
        tutor_conflict = Lesson.objects.filter(
            tutor=tutor,
            date=lesson_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        student_conflict = Lesson.objects.filter(
            student=user_profile,
            date=lesson_date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if tutor_conflict or student_conflict:
            return JsonResponse({
                'success': False,
                'error': 'This time slot is already booked for you or the tutor.'
            }, status=409)

        # Create lesson
        lesson = Lesson.objects.create(
            student=user_profile,
            tutor=tutor,
            date=lesson_date,
            start_time=start_time,
            end_time=end_time,
            location=location
        )

        # Allocate vehicle
        vehicle_allocation, allocation_info = allocate_vehicle_to_lesson(lesson, student_class)
        
        vehicle_message = allocation_info['message']
        vehicle_info = allocation_info['vehicle_info']
        
        if allocation_info['recommendation']:
            vehicle_message += f" ({allocation_info['recommendation']})"

        # Send notifications
        send_notification(
            tutor,
            f'New lesson booked by {request.user.username} '
            f'on {lesson.date} at {lesson.start_time}. {vehicle_message}'
        )
        send_notification(
            request.user,
            f'Lesson booked with {tutor.username} '
            f'on {lesson.date} at {lesson.start_time}. {vehicle_message}'
        )

        logger.info(
            f"API lesson booked: {lesson.student.username} "
            f"with {lesson.tutor.username} on {lesson.date}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Lesson booked successfully! {vehicle_message}',
            'lesson': {
                'id': lesson.id,
                'date': lesson.date.isoformat(),
                'start_time': lesson.start_time.strftime('%H:%M'),
                'end_time': lesson.end_time.strftime('%H:%M'),
                'location': lesson.location,
                'tutor': {
                    'id': tutor.id,
                    'username': tutor.username,
                    'full_name': tutor.get_full_name() or tutor.username
                },
                'vehicle': vehicle_info
            }
        })

    except Exception as e:
        logger.error(f"Error in API book lesson: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }, status=500)

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

@login_required
def generate_report(request: HttpRequest) -> HttpResponse:
    """
    Generate progress report for a student.
    
    Args:
        request (HttpRequest): The HTTP request object.
    
    Returns:
        HttpResponse: JSON response with progress report data.
    """
    user_profile = get_user_profile(request.user)
    
    if not user_profile or user_profile.role != 'student':
        messages.error(request, 'Only students can generate progress reports.')
        return redirect('dashboard')
    
    # Get all progress records for the student
    progress_records = StudentProgress.objects.filter(
        student=user_profile
    ).select_related('lesson', 'lesson__tutor').order_by('-created_at')
    
    # Prepare report data
    report_data = []
    for record in progress_records:
        report_data.append({
            'lesson_id': record.lesson.id,
            'lesson_date': record.lesson.date.strftime('%Y-%m-%d'),
            'lesson_time': f"{record.lesson.start_time.strftime('%H:%M')} - {record.lesson.end_time.strftime('%H:%M')}",
            'tutor': record.lesson.tutor.get_full_name() or record.lesson.tutor.username,
            'skills_covered': record.skills_covered,
            'progress_notes': record.progress_notes,
            'instructor_feedback': record.instructor_feedback,
            'next_lesson_focus': record.next_lesson_focus,
            'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    # Return JSON response
    return JsonResponse({
        'student_name': user_profile.get_full_name() or user_profile.username,
        'total_lessons': progress_records.count(),
        'progress_report': report_data
    })

@login_required
def add_progress_comment(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """
    Add progress comment for a lesson (tutors and admins only).
    
    Args:
        request (HttpRequest): The HTTP request object.
        lesson_id (int): The ID of the lesson to add progress for.
    
    Returns:
        HttpResponse: The HTTP response, either the form or a redirect.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user_profile = get_user_profile(request.user)
    
    # Check permissions - only tutors and admins can add progress comments
    if not user_profile or user_profile.role not in ['tutor', 'admin']:
        messages.error(request, 'You do not have permission to add progress comments.')
        return redirect('dashboard')
    
    # Check if progress already exists for this lesson
    existing_progress = StudentProgress.objects.filter(lesson=lesson).first()
    
    if request.method == 'POST':
        form = ProgressCommentForm(request.POST, instance=existing_progress, lesson=lesson)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.lesson = lesson
            progress.student = lesson.student
            progress.save()
            
            # Send progress email to student
            progress_data = {
                'skills_covered': progress.skills_covered,
                'progress_notes': progress.progress_notes,
                'instructor_feedback': progress.instructor_feedback,
                'next_lesson_focus': progress.next_lesson_focus
            }
            send_progress_email(lesson.student, lesson, progress_data)
            
            # Send notification to student
            send_notification(
                lesson.student,
                f'Progress report added for your lesson on {lesson.date}. Check your email for details!'
            )
            
            messages.success(request, 'Progress comment added successfully and email sent to student!')
            logger.info(f"Progress comment added for lesson {lesson.id} by {user_profile.username}")
            return redirect(reverse('lesson_detail', args=[lesson.id]))
    else:
        form = ProgressCommentForm(instance=existing_progress, lesson=lesson)
    
    context = {
        'form': form,
        'lesson': lesson,
        'existing_progress': existing_progress,
        'is_edit': existing_progress is not None
    }
    return render(request, 'add_progress_comment.html', context)

@login_required
def quick_progress_comment(request: HttpRequest, lesson_id: int) -> HttpResponse:
    """
    Add quick progress comment for a lesson (tutors and admins only).
    
    Args:
        request (HttpRequest): The HTTP request object.
        lesson_id (int): The ID of the lesson to add progress for.
    
    Returns:
        HttpResponse: The HTTP response, either the form or a redirect.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    user_profile = get_user_profile(request.user)
    
    # Check permissions - only tutors and admins can add progress comments
    if not user_profile or user_profile.role not in ['tutor', 'admin']:
        messages.error(request, 'You do not have permission to add progress comments.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = QuickProgressForm(request.POST)
        if form.is_valid():
            # Create or update progress record
            progress, created = StudentProgress.objects.get_or_create(
                lesson=lesson,
                student=lesson.student,
                defaults={
                    'progress_notes': form.cleaned_data['quick_notes'],
                    'skills_covered': 'General driving skills practice',
                    'instructor_feedback': f"Overall performance: {form.cleaned_data['overall_rating']}",
                    'next_lesson_focus': 'Continue practicing and improving'
                }
            )
            
            if not created:
                # Update existing record
                progress.progress_notes = form.cleaned_data['quick_notes']
                progress.instructor_feedback = f"Overall performance: {form.cleaned_data['overall_rating']}"
                progress.save()
            
            # Send email if requested
            if form.cleaned_data['send_email']:
                progress_data = {
                    'skills_covered': progress.skills_covered,
                    'progress_notes': progress.progress_notes,
                    'instructor_feedback': progress.instructor_feedback,
                    'next_lesson_focus': progress.next_lesson_focus
                }
                send_progress_email(lesson.student, lesson, progress_data)
                
                # Send notification
                send_notification(
                    lesson.student,
                    f'Quick progress update for your lesson on {lesson.date}. Check your email!'
                )
                email_message = " Email sent to student."
            else:
                email_message = ""
            
            messages.success(request, f'Quick progress comment added successfully!{email_message}')
            logger.info(f"Quick progress comment added for lesson {lesson.id} by {user_profile.username}")
            return redirect(reverse('lesson_detail', args=[lesson.id]))
    else:
        form = QuickProgressForm()
    
    context = {
        'form': form,
        'lesson': lesson
    }
    return render(request, 'quick_progress_comment.html', context)

@login_required
def student_progress_analysis(request: HttpRequest, student_id: int) -> HttpResponse:
    """
    Display AI-powered progress analysis for a student.
    
    Args:
        request (HttpRequest): The HTTP request object.
        student_id (int): The ID of the student to analyze.
    
    Returns:
        HttpResponse: The rendered progress analysis template.
    """
    user_profile = get_user_profile(request.user)
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Check permissions
    if not user_profile or (
        user_profile.role not in ['tutor', 'admin'] and
        user_profile != student
    ):
        messages.error(request, 'You do not have permission to view this progress analysis.')
        return redirect('dashboard')
    
    # Get AI analysis
    from ..ai_helper import ai_helper
    analysis = ai_helper.analyze_student_progress(student_id)
    
    # Get recent progress records
    progress_records = StudentProgress.objects.filter(
        student=student
    ).select_related('lesson', 'lesson__tutor').order_by('-created_at')[:10]
    
    # Get lessons without progress records
    lessons_without_progress = Lesson.objects.filter(
        student=student
    ).exclude(
        id__in=progress_records.values_list('lesson_id', flat=True)
    ).order_by('-date')[:5]
    
    context = {
        'student': student,
        'analysis': analysis,
        'progress_records': progress_records,
        'lessons_without_progress': lessons_without_progress,
        'can_add_progress': user_profile.role in ['tutor', 'admin']
    }
    
    return render(request, 'student_progress_analysis.html', context)

@login_required
def student_progress_detail(request: HttpRequest, student_id: int) -> HttpResponse:
    """
    Display student progress with AI suggestions and tutor/admin comments.
    
    Args:
        request (HttpRequest): The HTTP request object.
        student_id (int): The ID of the student.
    
    Returns:
        HttpResponse: The rendered progress detail template.
    """
    user_profile = get_user_profile(request.user)
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Check permissions
    if not user_profile or (
        user_profile.role not in ['tutor', 'admin'] and
        user_profile != student
    ):
        messages.error(request, 'You do not have permission to view this progress.')
        return redirect('dashboard')
    
    # Get lessons and progress records
    lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')
    progress_records = StudentProgress.objects.filter(
        student=student
    ).select_related('lesson', 'lesson__tutor').order_by('-created_at')
    
    # Generate AI feedback (not stored, just displayed)
    from ..ai_helper import ai_helper
    ai_feedback = ai_helper.generate_progress_feedback(list(lessons), list(progress_records))
    
    # Handle comment submission
    if request.method == 'POST' and user_profile.role in ['tutor', 'admin']:
        comment = request.POST.get('comment', '').strip()
        lesson_id = request.POST.get('lesson_id')
        
        if comment and lesson_id:
            try:
                lesson = get_object_or_404(Lesson, id=lesson_id, student=student)
                
                # Create or update progress record
                progress, created = StudentProgress.objects.get_or_create(
                    lesson=lesson,
                    student=student,
                    defaults={
                        'progress_notes': comment,
                        'skills_covered': 'General driving practice',
                        'instructor_feedback': 'Progress comment added',
                        'next_lesson_focus': 'Continue practicing'
                    }
                )
                
                if not created:
                    # Update existing record
                    progress.progress_notes = comment
                    progress.save()
                
                # Send notification to student
                send_notification(
                    student,
                    f'New progress comment added for your lesson on {lesson.date}'
                )
                
                messages.success(request, 'Progress comment added successfully!')
                logger.info(f"Progress comment added by {user_profile.username} for student {student.username}")
                
            except Exception as e:
                logger.error(f"Error adding progress comment: {str(e)}")
                messages.error(request, 'Error adding progress comment. Please try again.')
        
        return redirect('student_progress_detail', student_id=student_id)
    
    context = {
        'student': student,
        'lessons': lessons,
        'progress_records': progress_records,
        'ai_feedback': ai_feedback,
        'can_add_comments': user_profile.role in ['tutor', 'admin'],
        'user_profile': user_profile
    }
    
    return render(request, 'progress_detail.html', context)

@login_required
def export_progress_report(request: HttpRequest, student_id: int) -> HttpResponse:
    """
    Export comprehensive progress report as PDF or CSV.
    
    Args:
        request (HttpRequest): The HTTP request object.
        student_id (int): The ID of the student.
    
    Returns:
        HttpResponse: PDF or CSV file download.
    """
    user_profile = get_user_profile(request.user)
    student = get_object_or_404(User, id=student_id, role='student')
    
    # Check permissions
    if not user_profile or (
        user_profile.role not in ['tutor', 'admin'] and
        user_profile != student
    ):
        messages.error(request, 'You do not have permission to export this report.')
        return redirect('dashboard')
    
    # Get export format
    export_format = request.GET.get('format', 'pdf').lower()
    
    try:
        # Generate comprehensive report data
        from ..ai_helper import ai_helper
        report_data = ai_helper.generate_comprehensive_report_data(student_id)
        
        if 'error' in report_data:
            messages.error(request, report_data['error'])
            return redirect('student_progress_detail', student_id=student_id)
        
        if export_format == 'csv':
            return _export_csv_report(report_data)
        else:
            return _export_pdf_report(report_data)
            
    except Exception as e:
        logger.error(f"Error exporting progress report: {str(e)}")
        messages.error(request, 'Error generating report. Please try again.')
        return redirect('student_progress_detail', student_id=student_id)

def _export_csv_report(report_data: Dict[str, Any]) -> HttpResponse:
    """
    Export report data as CSV.
    
    Args:
        report_data: Dictionary containing report data.
    
    Returns:
        HttpResponse: CSV file download.
    """
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="progress_report_{report_data["student_info"]["name"].replace(" ", "_")}.csv"'
    
    writer = csv.writer(response)
    
    # Student Information
    writer.writerow(['STUDENT PROGRESS REPORT'])
    writer.writerow(['Generated:', report_data['generated_at']])
    writer.writerow([])
    
    writer.writerow(['STUDENT INFORMATION'])
    for key, value in report_data['student_info'].items():
        writer.writerow([key.replace('_', ' ').title(), value])
    writer.writerow([])
    
    # Statistics
    writer.writerow(['STATISTICS'])
    for key, value in report_data['statistics'].items():
        writer.writerow([key.replace('_', ' ').title(), value])
    writer.writerow([])
    
    # AI Insights
    writer.writerow(['AI INSIGHTS'])
    writer.writerow(['Analysis', report_data['ai_insights']['analysis']])
    writer.writerow(['Feedback', report_data['ai_insights']['feedback']])
    writer.writerow(['Progress Score', f"{report_data['ai_insights']['progress_score']}%"])
    writer.writerow([])
    
    # Recommendations
    writer.writerow(['RECOMMENDATIONS'])
    for rec in report_data['ai_insights']['recommendations']:
        writer.writerow(['', rec])
    writer.writerow([])
    
    # Lesson History
    writer.writerow(['LESSON HISTORY'])
    writer.writerow(['Date', 'Time', 'Duration (min)', 'Tutor', 'Location', 'Skills Covered', 'Progress Notes', 'Instructor Feedback', 'Next Focus'])
    
    for lesson in report_data['lesson_history']:
        writer.writerow([
            lesson['date'],
            lesson['time'],
            lesson['duration'],
            lesson['tutor'],
            lesson['location'],
            lesson['skills_covered'],
            lesson['progress_notes'],
            lesson['instructor_feedback'],
            lesson['next_focus']
        ])
    
    return response

def _export_pdf_report(report_data: Dict[str, Any]) -> HttpResponse:
    """
    Export report data as PDF.
    
    Args:
        report_data: Dictionary containing report data.
    
    Returns:
        HttpResponse: PDF file download.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from django.http import HttpResponse
    import io
    
    # Create PDF buffer
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#34495e')
    )
    
    # Title
    elements.append(Paragraph("Student Progress Report", title_style))
    elements.append(Paragraph(f"Generated: {report_data['generated_at']}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Student Information
    elements.append(Paragraph("Student Information", heading_style))
    student_data = [
        ['Name', report_data['student_info']['name']],
        ['Email', report_data['student_info']['email']],
        ['Phone', report_data['student_info']['phone']],
        ['Registration Date', report_data['student_info']['registration_date']]
    ]
    
    student_table = Table(student_data, colWidths=[2*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(student_table)
    elements.append(Spacer(1, 20))
    
    # Statistics
    elements.append(Paragraph("Statistics", heading_style))
    stats_data = [
        ['Total Lessons', str(report_data['statistics']['total_lessons'])],
        ['Total Hours', f"{report_data['statistics']['total_hours']} hours"],
        ['Lessons with Progress', str(report_data['statistics']['lessons_with_progress'])],
        ['Completion Rate', f"{report_data['statistics']['completion_rate']}%"],
        ['Recent Lessons (30 days)', str(report_data['statistics']['recent_lessons_30_days'])],
        ['Progress Score', f"{report_data['statistics']['progress_score']}%"]
    ]
    
    stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # AI Insights
    elements.append(Paragraph("AI Insights", heading_style))
    elements.append(Paragraph(f"<b>Analysis:</b> {report_data['ai_insights']['analysis']}", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>AI Feedback:</b> {report_data['ai_insights']['feedback']}", styles['Normal']))
    elements.append(Spacer(1, 10))
    
    if report_data['ai_insights']['recommendations']:
        elements.append(Paragraph("<b>Recommendations:</b>", styles['Normal']))
        for rec in report_data['ai_insights']['recommendations']:
            elements.append(Paragraph(f"• {rec}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Lesson History
    if report_data['lesson_history']:
        elements.append(Paragraph("Lesson History", heading_style))
        
        # Create lesson history table
        lesson_headers = ['Date', 'Time', 'Duration', 'Tutor', 'Skills Covered']
        lesson_data = [lesson_headers]
        
        for lesson in report_data['lesson_history'][:10]:  # Limit to first 10 lessons for PDF
            lesson_data.append([
                str(lesson['date']),
                lesson['time'],
                f"{lesson['duration']}min",
                lesson['tutor'],
                lesson['skills_covered'][:50] + '...' if len(lesson['skills_covered']) > 50 else lesson['skills_covered']
            ])
        
        lesson_table = Table(lesson_data, colWidths=[1*inch, 1*inch, 0.8*inch, 1.2*inch, 2*inch])
        lesson_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(lesson_table)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="progress_report_{report_data["student_info"]["name"].replace(" ", "_")}.pdf"'
    response.write(pdf_data)
    
    return response
