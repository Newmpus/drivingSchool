"""
Views for handling payment proof uploads and management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required

from ..models import User
from ..forms import PaymentProofUploadForm

@login_required
def upload_payment_proof(request):
    """View for students to upload payment proof."""
    if request.user.role != 'student':
        messages.error(request, 'Only students can upload payment proof.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PaymentProofUploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment proof uploaded successfully. Please wait for admin approval.')
            return redirect('dashboard')
    else:
        form = PaymentProofUploadForm(user=request.user)
    
    context = {
        'form': form,
        'payment_status': request.user.payment_status,
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
    }
    return render(request, 'payment_status.html', context)

@staff_member_required
def admin_payment_list(request):
    """Admin view to list all pending payments."""
    pending_payments = User.objects.filter(
        role='student', 
        payment_proof__isnull=False
    ).exclude(payment_status='approved')
    
    context = {
        'pending_payments': pending_payments,
    }
    return render(request, 'admin/payment_list.html', context)

@staff_member_required
def admin_approve_payment(request, user_id):
    """Admin view to approve a payment."""
    user = get_object_or_404(User, id=user_id, role='student')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            user.payment_status = 'approved'
            user.payment_approved_at = timezone.now()
            user.payment_verified = True
            user.save()
            messages.success(request, f'Payment approved for {user.username}')
        elif action == 'reject':
            user.payment_status = 'rejected'
            user.save()
            messages.warning(request, f'Payment rejected for {user.username}')
    
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
                return redirect('upload_payment_proof')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
