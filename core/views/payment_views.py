"""
Views for handling payment proof uploads and management.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from ..models import User
from ..forms import PaymentProofUploadForm

logger = logging.getLogger(__name__)

@login_required
def upload_payment_proof(request):
    """View for students to upload payment proof with enhanced validation and error handling."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can upload payment proof.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PaymentProofUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            try:
                # Get the uploaded file
                uploaded_file = request.FILES.get('payment_proof')
                if not uploaded_file:
                    messages.error(request, 'No file was uploaded.')
                    return render(request, 'upload_payment.html', {
                        'form': form,
                        'payment_status': request.user.payment_status,
                        'max_file_size': 5 * 1024 * 1024,
                    })
                
                # Validate file again (belt and suspenders approach)
                if uploaded_file.size > 5 * 1024 * 1024:
                    messages.error(request, 'File size must be under 5MB.')
                    return render(request, 'upload_payment.html', {
                        'form': form,
                        'payment_status': request.user.payment_status,
                        'max_file_size': 5 * 1024 * 1024,
                    })
                
                # Save the form
                user = form.save()
                
                # Log the upload with file details
                logger.info(
                    f"Payment proof uploaded by {request.user.username} - "
                    f"File: {uploaded_file.name}, Size: {uploaded_file.size} bytes"
                )
                
                messages.success(
                    request, 
                    'Payment proof uploaded successfully. Please wait for admin approval. '
                    f'Uploaded file: {uploaded_file.name}'
                )
                return redirect('dashboard')
                
            except Exception as e:
                logger.error(
                    f"Error uploading payment proof for {request.user.username}: {str(e)}",
                    exc_info=True
                )
                messages.error(
                    request, 
                    f'Error uploading payment proof: {str(e)}. Please try again with a different file.'
                )
        else:
            # Enhanced error logging
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(
                        f"Payment upload validation error for {request.user.username}: "
                        f"{field} - {error}"
                    )
                    
            # Add specific error messages for common issues
            if 'payment_proof' in form.errors:
                messages.error(
                    request, 
                    f'File upload error: {form.errors["payment_proof"][0]}'
                )
    else:
        form = PaymentProofUploadForm(instance=request.user)
    
    context = {
        'form': form,
        'payment_status': request.user.payment_status,
        'max_file_size': 5 * 1024 * 1024,  # 5MB in bytes
        'max_file_size_mb': 5,
    }
    return render(request, 'upload_payment.html', context)

@login_required
def payment_status_view(request):
    """View for students to check their payment status."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can view payment status.')
        return redirect('dashboard')
    
    context = {
        'payment_status': request.user.payment_status,
        'payment_submitted_at': request.user.payment_submitted_at,
        'payment_approved_at': request.user.payment_approved_at,
        'payment_proof': request.user.payment_proof,
    }
    return render(request, 'payment_status.html', context)

@staff_member_required
def admin_payment_list(request):
    """Admin view to list all pending payments."""
    pending_payments = User.objects.filter(
        role='student', 
        payment_proof__isnull=False
    ).exclude(payment_status='approved').order_by('-payment_submitted_at')
    
    context = {
        'pending_payments': pending_payments,
        'total_pending': pending_payments.count(),
    }
    return render(request, 'admin/payment_list.html', context)

@staff_member_required
def admin_approve_payment(request, user_id):
    """Admin view to approve or reject a payment."""
    user = get_object_or_404(User, id=user_id, role='student')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            if action == 'approve':
                user.payment_status = 'approved'
                user.payment_approved_at = timezone.now()
                user.payment_verified = True
                user.save()
                
                # Send notification to student
                from ..services.notification_service import NotificationService
                NotificationService.send_notification(
                    user,
                    f'Your payment has been approved. You can now book lessons.',
                    'payment_approved'
                )
                
                messages.success(request, f'Payment approved for {user.username}')
                logger.info(f"Payment approved for {user.username}")
                
            elif action == 'reject':
                user.payment_status = 'rejected'
                user.save()
                
                # Send notification to student
                rejection_reason = notes or 'Please contact admin for details'
                from ..services.notification_service import NotificationService
                NotificationService.send_notification(
                    user,
                    f'Your payment was rejected: {rejection_reason}',
                    'payment_rejected'
                )
                
                messages.warning(request, f'Payment rejected for {user.username}')
                logger.info(f"Payment rejected for {user.username}")
                
        except Exception as e:
            logger.error(f"Error processing payment approval: {str(e)}")
            messages.error(request, 'Error processing payment. Please try again.')
    
    return redirect('admin_payment_list')

def payment_required(view_func):
    """Decorator to check if student has approved payment."""
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'student':
            if request.user.payment_status != 'approved':
                if request.user.payment_status == 'pending':
                    messages.warning(request, 'Your payment is pending approval. Please wait for admin approval.')
                elif request.user.payment_status == 'rejected':
                    messages.error(request, 'Your payment was rejected. Please re-upload your payment proof.')
                elif not request.user.payment_proof:
                    messages.error(request, 'Please upload your payment proof to access this feature.')
                return redirect('upload_payment_proof')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
