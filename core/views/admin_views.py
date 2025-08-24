from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from core.models import User, Lesson
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

    context = {
        'student_count': student_count,
        'lesson_count': lesson_count,
        'student_progress': student_progress,
    }
    
    return render(request, 'admin/student_status_dashboard.html', context)

@login_required
def export_student_status(request):
    """
    Export student status data to CSV format.
    """
    students = User.objects.filter(role='student')
    
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="student_status_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
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
            timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response
