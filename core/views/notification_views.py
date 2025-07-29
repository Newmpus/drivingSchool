"""
Notification related views for the core app.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from ..models import Notification

logger = logging.getLogger(__name__)

@login_required
def mark_notification_read(request: HttpRequest, notification_id: int) -> HttpResponse:
    """
    Mark a notification as read.
    
    Args:
        request (HttpRequest): The HTTP request object.
        notification_id (int): The ID of the notification to mark as read.
    
    Returns:
        HttpResponse: Redirect to dashboard.
    """
    notification = Notification.objects.filter(
        id=notification_id,
        user=request.user
    ).first()
    
    if notification:
        notification.is_read = True
        notification.save()
        logger.info(f"Notification {notification_id} marked as read by {request.user.username}")
    
    return redirect('dashboard')
