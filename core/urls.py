"""
URL patterns for the core app.
"""
from django.urls import path
from .views import payment_views

urlpatterns = [
    # Payment URLs
    path('upload-payment/', payment_views.upload_payment_proof, name='upload_payment_proof'),
    path('payment-status/', payment_views.payment_status_view, name='payment_status'),
    path('admin/payments/', payment_views.admin_payment_list, name='admin_payment_list'),
    path('admin/payments/<int:user_id>/approve/', payment_views.admin_approve_payment, name='admin_approve_payment'),
]
