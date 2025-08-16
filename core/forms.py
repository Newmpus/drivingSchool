"""
Forms for the core app.
"""
import re
from datetime import datetime, time, timedelta

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User, Lesson # Import your custom User model

class UserRegistrationForm(forms.ModelForm):
    """Form for user registration with enhanced validation."""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )
    role = forms.ChoiceField(
        choices=[('student', 'Student'), ('tutor', 'Tutor'), ('admin', 'Admin')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter address'
        })
    )
    invitation_code = forms.CharField(
        max_length=64,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter invitation code if you have one'
        })
    )
    payment_proof = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        })
    )

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

    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'phone', 'address', 'profile_picture']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter address'
            }),
        }

class PaymentProofUploadForm(forms.ModelForm):
    """Form for uploading payment proof with validation."""
    
    payment_proof = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file',
            'accept': '.jpg,.jpeg,.png,.gif,.bmp,.pdf,.doc,.docx,.txt'
        })
    )

    class Meta:
        model = User
        fields = ['payment_proof']

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.pop('user', None)
        if user_instance and 'instance' not in kwargs:
            kwargs['instance'] = user_instance
        super().__init__(*args, **kwargs)

    def clean_payment_proof(self):
        """Validate the uploaded payment proof file with enhanced validation."""
        file = self.cleaned_data.get('payment_proof')
        
        if not file:
            raise ValidationError('Please select a file to upload.')
        
        try:
            # Get file size with multiple fallback methods
            file_size = None
            if hasattr(file, 'size') and file.size is not None:
                file_size = file.size
            elif hasattr(file, '_size') and file._size is not None:
                file_size = file._size
            else:
                try:
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                except (AttributeError, IOError):
                    # If we can't determine size, skip size check but log it
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not determine file size for {getattr(file, 'name', 'unknown')}")
            
            if file_size and file_size > 5 * 1024 * 1024:
                raise ValidationError('File size must be under 5MB.')
            
            # Enhanced file extension validation
            filename = str(getattr(file, 'name', '')).strip()
            if not filename:
                raise ValidationError('Invalid file name.')
            
            # Extract extension safely
            if '.' not in filename:
                raise ValidationError('File must have an extension.')
            
            ext = filename.rsplit('.', 1)[-1].lower()
            valid_extensions = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'pdf', 'doc', 'docx', 'txt'}
            if ext not in valid_extensions:
                raise ValidationError(
                    f'Invalid file type (.{ext}). Allowed types: {", ".join(sorted(valid_extensions))}'
                )
            
            # Enhanced MIME type validation
            content_type = str(getattr(file, 'content_type', '')).lower()
            if content_type:
                allowed_content_types = {
                    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
                    'application/pdf', 'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'text/plain', 'application/octet-stream'
                }
                
                # Check if content type is valid for the extension
                extension_to_mime = {
                    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                    'gif': 'image/gif', 'bmp': 'image/bmp', 'pdf': 'application/pdf',
                    'doc': 'application/msword', 'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'txt': 'text/plain'
                }
                
                expected_mime = extension_to_mime.get(ext)
                if expected_mime and content_type not in {expected_mime, 'application/octet-stream'}:
                    # Allow octet-stream as fallback for unknown uploads
                    if content_type != 'application/octet-stream':
                        logger = logging.getLogger(__name__)
                        logger.warning(f"MIME type mismatch: expected {expected_mime}, got {content_type}")
            
            # Basic file content validation - check if file is readable
            try:
                chunk = file.read(1024)  # Read first 1KB
                if not chunk or len(chunk) == 0:
                    raise ValidationError('File appears to be empty.')
                file.seek(0)  # Reset position
            except Exception as e:
                raise ValidationError(f'Cannot read file: {str(e)}')
                
        except ValidationError:
            # Re-raise Django validation errors
            raise
        except Exception as e:
            # Log unexpected errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error validating payment proof: {str(e)}", exc_info=True)
            raise ValidationError('Error processing file. Please try uploading again.')
        
        return file

    def save(self, commit=True):
        """Save the payment proof and update status."""
        user = super().save(commit=False)
        user.payment_status = 'pending'
        user.payment_submitted_at = timezone.now()
        if commit:
            user.save()
        return user

class LessonBookingForm(forms.ModelForm):
    """Form for booking lessons with enhanced validation."""
    
    tutor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='tutor'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a tutor"
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )
    location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter lesson location'
        })
    )
    student_class = forms.ChoiceField(
        choices=[
            ('class1', 'Class 1 - Light Vehicles'),
            ('class2', 'Class 2 - Medium Vehicles'),
            ('class3', 'Class 3 - Heavy Vehicles'),
            ('class4', 'Class 4 - Public Service Vehicles'),
            ('class5', 'Class 5 - Special Vehicles'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Learner Class'
    )

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
            duration = datetime.combine(timezone.now().date(), end_time) - \
                      datetime.combine(timezone.now().date(), start_time)
            if duration.total_seconds() < 1800:  # 30 minutes
                raise ValidationError('Lesson must be at least 30 minutes long.')
            
            # Check maximum lesson duration (3 hours)
            if duration.total_seconds() > 10800:  # 3 hours
                raise ValidationError('Lesson cannot be longer than 3 hours.')
            
            # Check business hours (8 AM to 6 PM)
            if start_time < time(8, 0) or end_time > time(18, 0):
                raise ValidationError('Lessons must be between 8:00 AM and 6:00 PM.')
        
        return cleaned_data
