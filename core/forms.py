import re
from datetime import datetime, time, timedelta

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User, Lesson, StudentProgress, Vehicle

class UserRegistrationForm(forms.ModelForm):
    """Form for user registration with enhanced validation."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}), label='Confirm Password')
    role = forms.ChoiceField(choices=[('student', 'Student'), ('tutor', 'Tutor'), ('admin', 'Admin')], widget=forms.Select(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}))
    address = forms.CharField(max_length=255, required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}))
    invitation_code = forms.CharField(max_length=64, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter invitation code if you have one'}))
    payment_proof = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'phone', 'address', 'invitation_code', 'payment_proof']

    def clean_username(self):
        """Validate username."""
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Username already exists.')
        return username

    def clean_email(self):
        """Validate email."""
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered.')
        return email

    def clean_password(self):
        """Validate password strength."""
        password = self.cleaned_data['password']
        validate_password(password)
        return password

    def clean_password_confirm(self):
        """Validate password confirmation."""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match.')
        return password_confirm

    def clean_phone(self):
        """Validate phone number format."""
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[\d\s\-\(\)]+$', phone):
            raise ValidationError('Invalid phone number format.')
        return phone

    def save(self, commit=True):
        """Save the user with hashed password and payment proof."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        payment_proof_file = self.cleaned_data.get('payment_proof')
        if payment_proof_file:
            user.payment_proof = payment_proof_file
        if commit:
            user.save()
        return user

class UserProfileEditForm(forms.ModelForm):
    """Form for editing user profile."""
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    class Meta:
        model = User
        fields = ['email', 'phone', 'address', 'profile_picture']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
        }

class PaymentProofUploadForm(forms.ModelForm):
    """Form for uploading payment proof with validation."""
    payment_proof = forms.FileField(required=True, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file', 'accept': '.jpg,.jpeg,.png,.gif,.bmp,.pdf,.doc,.docx,.txt'}))

    class Meta:
        model = User
        fields = ['payment_proof']

    def clean_payment_proof(self):
        """Validate the uploaded payment proof file with enhanced validation."""
        file = self.cleaned_data.get('payment_proof')
        if not file:
            raise ValidationError('Please select a file to upload.')
        
        # File size validation (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            raise ValidationError(f'File size must be under 5MB. Your file is {file.size / (1024*1024):.1f}MB.')
        
        # File type validation
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/bmp',
            'application/pdf', 
            'application/msword', 
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain'
        ]
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf', '.doc', '.docx', '.txt']
        
        # Check content type
        if file.content_type not in allowed_types:
            raise ValidationError('Invalid file type. Please upload images (JPG, PNG, GIF, BMP), PDF, Word documents, or text files.')
        
        # Check file extension
        import os
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            raise ValidationError('Invalid file extension. Please upload files with extensions: .jpg, .jpeg, .png, .gif, .bmp, .pdf, .doc, .docx, .txt.')
        
        # Check for executable files
        executable_extensions = ['.exe', '.bat', '.cmd', '.sh', '.msi', '.dll']
        if file_extension in executable_extensions:
            raise ValidationError('Executable files are not allowed for security reasons.')
        
        return file

class LessonBookingForm(forms.ModelForm):
    """Form for booking lessons with enhanced validation."""
    tutor = forms.ModelChoiceField(queryset=User.objects.filter(role='tutor'), widget=forms.Select(attrs={'class': 'form-control'}), empty_label="Select a tutor")
    date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))
    location = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter lesson location'}))
    student_class = forms.ChoiceField(choices=[('class1', 'Class 1 - Light Vehicles'), ('class2', 'Class 2 - Medium Vehicles'), ('class3', 'Class 3 - Heavy Vehicles'), ('class4', 'Class 4 - Public Service Vehicles'), ('class5', 'Class 5 - Special Vehicles')], widget=forms.Select(attrs={'class': 'form-control'}), label='Learner Class')

    class Meta:
        model = Lesson
        fields = ['tutor', 'date', 'start_time', 'end_time', 'location', 'student_class']

    def clean_date(self):
        """Validate lesson date."""
        date = self.cleaned_data['date']
        if date < timezone.now().date():
            raise ValidationError('Cannot book lessons in the past.')
        if date > timezone.now().date() + timedelta(days=90):
            raise ValidationError('Cannot book lessons more than 90 days in advance.')
        return date

    def clean(self):
        """Validate lesson time constraints."""
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('End time must be after start time.')
            
            # Check minimum lesson duration (30 minutes)
            duration = datetime.combine(timezone.now().date(), end_time) - datetime.combine(timezone.now().date(), start_time)
            if duration.total_seconds() < 1800:  # 30 minutes
                raise ValidationError('Lesson must be at least 30 minutes long.')
            
            # Check maximum lesson duration (3 hours)
            if duration.total_seconds() > 10800:  # 3 hours
                raise ValidationError('Lesson cannot be longer than 3 hours.')
            
            # Check business hours (8 AM to 6 PM)
            if start_time < time(8, 0) or end_time > time(18, 0):
                raise ValidationError('Lessons must be between 8:00 AM and 6:00 PM.')
        
        return cleaned_data

class ProgressCommentForm(forms.ModelForm):
    """Form for tutors to add progress comments for students."""
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter detailed progress comment...'}))
    rating = forms.ChoiceField(choices=[(1, '1 - Needs Improvement'), (2, '2 - Below Average'), (3, '3 - Average'), (4, '4 - Good'), (5, '5 - Excellent')], widget=forms.Select(attrs={'class': 'form-control'}))
    skills_improved = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Skills improved (comma separated)'}))
    areas_to_work_on = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Areas to work on (comma separated)'}))

    class Meta:
        model = StudentProgress
        fields = ['comment', 'rating', 'skills_improved', 'areas_to_work_on']

class QuickProgressForm(forms.Form):
    """Quick form for adding basic progress comments."""
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter quick progress note...'}))
    rating = forms.ChoiceField(choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), (4, '4 - Very Good'), (5, '5 - Excellent')], widget=forms.Select(attrs={'class': 'form-control'}))

class VehicleForm(forms.ModelForm):
    """Form for adding and editing vehicles."""
    
    class Meta:
        model = Vehicle
        fields = ['registration_number', 'make', 'model', 'year', 'vehicle_class', 'vehicle_type', 'is_available', 'notes']
        widgets = {
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter registration number'}),
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle make'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle model'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter vehicle year'}),
            'vehicle_class': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_type': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter any additional notes'}),
        }
