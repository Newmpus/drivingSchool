"""
URL patterns for the core app.
"""
from django.urls import path
from .views import payment_views, lesson_views, vehicle_views

urlpatterns = [
    # Payment URLs
    path('upload-payment/', payment_views.upload_payment_proof, name='upload_payment_proof'),
    path('payment-status/', payment_views.payment_status_view, name='payment_status'),
    path('admin/payments/', payment_views.admin_payment_list, name='admin_payment_list'),
    path('admin/payments/<int:user_id>/approve/', payment_views.admin_approve_payment, name='admin_approve_payment'),
    
    # Report generation
    path('reports/', lesson_views.generate_report, name='generate_report'),
    
    # Progress tracking URLs
    path('lesson/<int:lesson_id>/add-progress/', lesson_views.add_progress_comment, name='add_progress_comment'),
    path('lesson/<int:lesson_id>/quick-progress/', lesson_views.quick_progress_comment, name='quick_progress_comment'),
    path('student/<int:student_id>/progress-analysis/', lesson_views.student_progress_analysis, name='student_progress_analysis'),
    
    # New enhanced progress URLs
    path('student/<int:student_id>/progress-detail/', lesson_views.student_progress_detail, name='student_progress_detail'),
    path('student/<int:student_id>/export-report/', lesson_views.export_progress_report, name='export_progress_report'),

    # Vehicle management URLs
    path('admin/vehicles/', vehicle_views.vehicle_list, name='vehicle_list'),
    path('admin/vehicles/add/', vehicle_views.add_vehicle, name='add_vehicle'),
    path('admin/vehicles/<int:vehicle_id>/edit/', vehicle_views.edit_vehicle, name='edit_vehicle'),
    path('admin/vehicles/<int:vehicle_id>/delete/', vehicle_views.delete_vehicle, name='delete_vehicle'),
]
