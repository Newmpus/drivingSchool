from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from core.models import User, Lesson
from core.forms import UserProfileEditForm
import csv
from django.utils import timezone

@login_required
def student_status_dashboard(request):
    """
    Display the aggregated status of all students.
    """
    students = User.objects.filter(role='student')
    student_count = students.count()
    lesson_count = Lesson.objects.count()

    # Fetch additional data as needed for the dashboard
    student_progress = {
        student.username: student.progress_records.count() for student in students
    }

    # Prepare data for Progress Distribution chart
    progress_distribution = {
        'Beginner': 0,
        'Intermediate': 0,
        'Advanced': 0
    }

    for student in students:
        progress_count = student.progress_records.count()
        if progress_count <= 2:
            progress_distribution['Beginner'] += 1
        elif progress_count <= 5:
            progress_distribution['Intermediate'] += 1
        else:
            progress_distribution['Advanced'] += 1

    # Prepare data for Lesson Frequency chart (lessons per day of week)
    lesson_frequency = {
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0,
        'Sunday': 0
    }

    lessons = Lesson.objects.all()
    for lesson in lessons:
        day_name = lesson.date.strftime('%A')
        lesson_frequency[day_name] += 1

    context = {
        'student_count': student_count,
        'lesson_count': lesson_count,
        'student_progress': student_progress,
        'progress_distribution': progress_distribution,
        'lesson_frequency': lesson_frequency,
    }

    # Debug logging
    print("Progress distribution:", progress_distribution)
    print("Lesson frequency:", lesson_frequency)

    return render(request, 'admin/student_status_dashboard.html', context)

@login_required
def export_student_status(request):
    """
    Export student status data to CSV format.
    """
    students = User.objects.filter(role='student')

    # Get export timestamp once for consistency
    export_timestamp = timezone.now()
    export_date_str = export_timestamp.strftime('%Y-%m-%d %H:%M:%S')

    # Create the HttpResponse object with the appropriate CSV header for Excel compatibility
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="student_status_export_{export_timestamp.strftime("%Y%m%d_%H%M%S")}.csv"'

    # Add UTF-8 BOM for Excel compatibility
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['Student Username', 'Progress Records Count', 'Status', 'Export Date'])

    for student in students:
        progress_count = student.progress_records.count()

        # Determine status based on progress count
        if progress_count > 5:
            status = 'Advanced'
        elif progress_count > 2:
            status = 'Intermediate'
        else:
            status = 'Beginner'

        writer.writerow([
            student.username,
            progress_count,
            status,
            f'"{export_date_str}"'  # Wrap in quotes to force Excel to treat as text
        ])

    return response

@login_required
def student_detail(request, username):
    student = get_object_or_404(User, username=username, role='student')
    progress_records = student.progress_records.all()
    context = {
        'student': student,
        'progress_records': progress_records,
    }
    return render(request, 'admin/student_detail.html', context)

@login_required
def student_edit(request, username):
    student = get_object_or_404(User, username=username, role='student')
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_detail', username=student.username)
    else:
        form = UserProfileEditForm(instance=student)
    context = {
        'form': form,
        'student': student,
    }
    return render(request, 'admin/student_edit.html', context)
