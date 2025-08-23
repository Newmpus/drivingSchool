"""
Views for vehicle management in the driving school system.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Vehicle
from ..forms import VehicleForm

def is_admin(user):
    """Check if user is an admin."""
    return user.is_authenticated and user.role == 'admin'

@login_required
@user_passes_test(is_admin)
def vehicle_list(request):
    """Display list of all vehicles."""
    vehicles = Vehicle.objects.all().order_by('vehicle_class', 'registration_number')
    
    context = {
        'vehicles': vehicles,
        'title': 'Vehicle Management'
    }
    return render(request, 'vehicle_list.html', context)

@login_required
@user_passes_test(is_admin)
def add_vehicle(request):
    """Add a new vehicle to the system."""
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.registration_number} added successfully!')
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    
    context = {
        'form': form,
        'title': 'Add New Vehicle'
    }
    return render(request, 'vehicle_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_vehicle(request, vehicle_id):
    """Edit an existing vehicle."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            messages.success(request, f'Vehicle {vehicle.registration_number} updated successfully!')
            return redirect('vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)
    
    context = {
        'form': form,
        'vehicle': vehicle,
        'title': f'Edit Vehicle - {vehicle.registration_number}'
    }
    return render(request, 'vehicle_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_vehicle(request, vehicle_id):
    """Delete a vehicle from the system."""
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    if request.method == 'POST':
        registration_number = vehicle.registration_number
        vehicle.delete()
        messages.success(request, f'Vehicle {registration_number} deleted successfully!')
        return redirect('vehicle_list')
    
    context = {
        'vehicle': vehicle,
        'title': f'Delete Vehicle - {vehicle.registration_number}'
    }
    return render(request, 'vehicle_confirm_delete.html', context)
