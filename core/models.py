from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Instructor'),
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
    lessons_taken = models.IntegerField(default=0)
    instructor_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    def can_access_services(self):
        """Check if user can access driving school services."""
        return self.role == 'student' and self.payment_status == 'approved'

    def get_level(self):
        lessons = self.student_lessons.count()
        if lessons < 10:
            return "Not eligible"
        elif 10 <= lessons <= 14:
            return "Advanced"
        elif 15 <= lessons <= 19:
            return "Intermediate"
        elif 20 <= lessons <= 30:
            return "Beginner"
        else:
            return "Exceeded maximum lessons"

    @property
    def eligible_for_vid(self):
        # Admins and instructors are eligible since they already have licenses
        if self.role in ['admin', 'tutor']:
            return True
        # Students need 10+ lessons and instructor approval
        return self.student_lessons.count() >= 10 and self.instructor_approved

    @property
    def total_lessons(self):
        return self.student_lessons.count()

    def clean(self):
        super().clean()
        if self.pk and self.student_lessons.count() > 30:
            raise ValidationError("Exceeded maximum lessons: cannot have more than 30 lessons taken.")

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

class Vehicle(models.Model):
    VEHICLE_CLASS_CHOICES = (
        ('class1', 'Class 1 - Light Vehicles'),
        ('class2', 'Class 2 - Medium Vehicles'),
        ('class3', 'Class 3 - Heavy Vehicles'),
        ('class4', 'Class 4 - Public Service Vehicles'),
        ('class5', 'Class 5 - Special Vehicles'),
    )
    
    VEHICLE_TYPE_CHOICES = (
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('suv', 'SUV'),
        ('truck', 'Truck'),
        ('bus', 'Bus'),
        ('motorcycle', 'Motorcycle'),
    )
    
    registration_number = models.CharField(max_length=20, unique=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    vehicle_class = models.CharField(max_length=10, choices=VEHICLE_CLASS_CHOICES)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.registration_number} - {self.make} {self.model} ({self.get_vehicle_class_display()})"

    class Meta:
        ordering = ['vehicle_class', 'registration_number']

class VehicleAllocation(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='vehicle_allocation')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    allocated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.vehicle} allocated to {self.lesson}"

class StudentProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    progress_notes = models.TextField()
    skills_covered = models.TextField()
    next_lesson_focus = models.TextField()
    instructor_feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Progress for {self.student.username} - {self.lesson.date}"

@receiver(post_save, sender=Lesson)
def update_lessons_taken_on_save(sender, instance, **kwargs):
    instance.student.lessons_taken = instance.student.student_lessons.count()
    instance.student.save(update_fields=['lessons_taken'])

@receiver(post_delete, sender=Lesson)
def update_lessons_taken_on_delete(sender, instance, **kwargs):
    instance.student.lessons_taken = instance.student.student_lessons.count()
    instance.student.save(update_fields=['lessons_taken'])
