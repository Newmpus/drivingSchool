"""
URL configuration for drivingschool project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core.views.admin_views import student_status_dashboard, export_student_status, student_detail, student_edit
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from core import views as core_views

# Apply rate limiting to login view
login_view = ratelimit(key='ip', rate='5/m', method='POST')(auth_views.LoginView.as_view())

# Custom logout view that redirects to home
def custom_logout_view(request):
    """Custom logout view that redirects to home page"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('home')

urlpatterns = [
    # Custom admin URLs must come before the Django admin pattern
    path('admin/student-status/', student_status_dashboard, name='student_status_dashboard'),
    path('admin/student-status/export/', export_student_status, name='export_student_status'),
    path('admin/student/<str:username>/', student_detail, name='student_detail'),
    path('admin/student/<str:username>/edit/', student_edit, name='student_edit'),
    
    # Include core app URLs for admin vehicle management (must come before admin.site.urls)
    path('admin/', include('core.urls')),
    
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('register/', core_views.register, name='register'),
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('edit-profile/', core_views.edit_profile, name='edit_profile'),

    # Authentication URLs with rate limiting
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', custom_logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    # Lesson management
    path('book-lesson/', core_views.book_lesson, name='book_lesson'),
    path('api/book-lesson/', core_views.api_book_lesson, name='api_book_lesson'),
    path('lesson/<int:lesson_id>/', core_views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/cancel/', core_views.cancel_lesson, name='cancel_lesson'),
    path('lesson/<int:lesson_id>/reschedule/', core_views.reschedule_lesson, name='reschedule_lesson'),

    # Admin functions
    path('generate-timetable/', core_views.generate_timetable, name='generate_timetable'),

    # Notifications
    path('notification/read/<int:notification_id>/', core_views.notification_views.mark_notification_read, name='mark_notification_read'),
]

# Add debug toolbar URLs in development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
