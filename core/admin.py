"""
Admin configuration for the core app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
#from django.contrib.auth.models import User
from django.utils.html import format_html

from .models import User, Lesson, Notification, Vehicle

class CustomUserAdmin(UserAdmin):
    """Custom User admin."""
    list_display = ('username', 'role', 'total_lessons', 'get_level', 'instructor_approved', 'eligible_for_vid')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'is_approved')
    actions = ['approve_users', 'mark_instructor_approved']

    def payment_proof_display(self, obj):
        if obj.payment_proof:
            return format_html('<a href="{}" target="_blank">View Proof</a>', obj.payment_proof.url)
        return "No proof uploaded"
    payment_proof_display.short_description = 'Payment Proof'

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True, is_active=True)
        self.message_user(request, f"{updated} user(s) successfully approved.")
    approve_users.short_description = "Approve selected users"

    def mark_instructor_approved(self, request, queryset):
        updated = queryset.update(instructor_approved=True)
        self.message_user(request, f"{updated} user(s) marked as instructor-approved.")
    mark_instructor_approved.short_description = "Mark selected students as instructor-approved"

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin for Lesson model."""
    list_display = ('student', 'tutor', 'date', 'start_time', 'end_time', 'location')
    list_filter = ('date', 'location')
    search_fields = ('student__username', 'tutor__username', 'location')
    date_hierarchy = 'date'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model."""
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)

# Register the Vehicle model
@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    """Admin for Vehicle model."""
    list_display = ('registration_number', 'make', 'model', 'year', 'vehicle_class', 'is_available')
    list_filter = ('vehicle_class', 'is_available')
    search_fields = ('registration_number', 'make', 'model')

# Register the custom User model with CustomUserAdmin
admin.site.register(User, CustomUserAdmin)

# Customize admin site headers
admin.site.site_header = 'Smart Driving School Management'
admin.site.site_title = 'Driving School Admin'
admin.site.index_title = 'Welcome to Smart Driving School Administration'
