"""
Authentication related views for the core app.
"""
from typing import Dict, Any, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as DjangoUser  # Alias Django's User to avoid conflict
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from core.forms import UserRegistrationForm, UserProfileEditForm
from core.models import User, Notification, Lesson # Import your custom User model

def get_user_profile(user: User) -> Optional[User]:
    """
    Get the UserProfile instance for a given user.

    Args:
        user (User): The user instance to get the profile for.

    Returns:
        Optional[User]: The user's profile if it exists, None otherwise.
    """
    # Since UserProfile is merged into User, we just return the user object itself
    return user

def register(request: HttpRequest) -> HttpResponse:
    """
    Handle user registration.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response, either the registration form or a redirect.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set user as active to allow immediate login
            user.is_active = True
            # Handle invitation code validation
            invitation_code = form.cleaned_data.get('invitation_code')
            if invitation_code:
                # Here you would validate the invitation code against your system
                user.is_invited = True
                user.invitation_code = invitation_code
            else:
                user.is_invited = False
            # Payment verification flag set to False initially
            user.payment_verified = False
            user.save()
            # The UserProfile fields are now directly on the User model,
            # so no separate UserProfile.objects.create() is needed.
            # The form.save() already handled saving the user object with these fields.

            # Notify admin for approval (implement admin notification logic)
            # For now, just create a notification record
            Notification.objects.create(
                user=user,
                message='New user registration completed.'
            )
            messages.success(request, 'Registration successful. You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """
    Display the user's dashboard.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered dashboard template.
    """
    user_profile = get_user_profile(request.user) # This will now return the User object
    context: Dict[str, Any] = {'user_profile': user_profile}

    # Get unread notifications
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')
    context['notifications'] = notifications

    from core.forms import PaymentProofUploadForm

    if request.method == 'POST':
        form = PaymentProofUploadForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            user_profile.payment_verified = False  # Reset payment verification on new upload
            user_profile.save()
            messages.success(request, 'Payment proof uploaded successfully. Awaiting verification.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Failed to upload payment proof. Please try again.')
    else:
        form = PaymentProofUploadForm(instance=user_profile)

    context['payment_form'] = form

    if user_profile: # user_profile is now the User object
        current_date = timezone.now().date()
        if user_profile.role == 'student':
            lessons = user_profile.student_lessons.filter(
                date__gte=current_date
            ).select_related('tutor').order_by('date', 'start_time') # tutor__user is not needed if tutor is a User object
            
            # Add progress tracking
            from core.models import StudentProgress
            progress = StudentProgress.objects.filter(
                student=user_profile
            ).select_related('lesson').order_by('-created_at')
            
            # Add AI analysis for student progress
            from core.ai_helper import ai_helper
            ai_analysis = ai_helper.analyze_student_progress(user_profile.id)
            
            context.update({
                'lessons': lessons,
                'progress': progress,
                'ai_analysis': ai_analysis,
            })
        elif user_profile.role == 'tutor':
            lessons = user_profile.tutor_lessons.filter(
                date__gte=current_date
            ).select_related('student').order_by('date', 'start_time') # student__user is not needed if student is a User object
            students = User.objects.filter( # Changed from UserProfile.objects.filter
                role='student',
                student_lessons__tutor=user_profile
            ).distinct()

            # Get lessons without progress comments for this tutor
            from core.models import StudentProgress
            lessons_without_progress = user_profile.tutor_lessons.filter(
                date__lte=current_date
            ).exclude(
                id__in=StudentProgress.objects.values_list('lesson_id', flat=True)
            ).select_related('student').order_by('-date')[:10]

            # Add AI insights for tutor dashboard
            from core.ai_helper import ai_helper
            context.update({
                'lessons': lessons,
                'students': students,
                'lessons_without_progress': lessons_without_progress,
                'ai_helper': ai_helper
            })
        elif user_profile.role == 'admin':
            user_count = User.objects.count()
            student_count = User.objects.filter(role='student').count() # Changed from UserProfile.objects.filter
            tutor_count = User.objects.filter(role='tutor').count() # Changed from UserProfile.objects.filter
            all_lessons = Lesson.objects.select_related(
                'student', # Changed from student__user
                'tutor' # Changed from tutor__user
            ).order_by('-date', '-start_time')[:10]
            
            # Add AI vehicle utilization report for admin
            from core.ai_helper import ai_helper
            vehicle_report = ai_helper.get_vehicle_utilization_report()
            
            context.update({
                'user_count': user_count,
                'student_count': student_count,
                'tutor_count': tutor_count,
                'lesson_count': Lesson.objects.count(),
                'recent_lessons': all_lessons,
                'vehicle_report': vehicle_report,
            })

    return render(request, 'dashboard.html', context)

@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    """
    Handle user profile editing.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response, either the edit form or a redirect.
    """
    user_profile = get_user_profile(request.user) # This will now return the User object
    if request.method == 'POST':
        form = UserProfileEditForm(
            request.POST,
            instance=user_profile, # instance is now the User object
        )
        if form.is_valid():
            profile = form.save() # profile is now the User object
            # The email is already handled by the form.save() if it's part of the form
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard')
    else:
        form = UserProfileEditForm(instance=user_profile)
    return render(request, 'edit_profile.html', {'form': form})
