from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
        ('admin', 'Admin'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_invited = models.BooleanField(default=False)
    invitation_code = models.CharField(max_length=64, blank=True, null=True)
    payment_verified = models.BooleanField(default=False)
    payment_proof = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_submitted_at = models.DateTimeField(blank=True, null=True)
    payment_approved_at = models.DateTimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.username

    def can_access_services(self):
        """Check if user can access driving school services."""
        return self.role == 'student' and self.payment_status == 'approved'

class Lesson(models.Model):
    student = models.ForeignKey(User, related_name='student_lessons', on_delete=models.CASCADE)
    tutor = models.ForeignKey(User, related_name='tutor_lessons', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_duration(self):
        start = timezone.datetime.combine(self.date, self.start_time)
        end = timezone.datetime.combine(self.date, self.end_time)
        duration = end - start
        return int(duration.total_seconds() / 60)

    def __str__(self):
        return f"Lesson for {self.student.username} with {self.tutor.username} on {self.date}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}"
