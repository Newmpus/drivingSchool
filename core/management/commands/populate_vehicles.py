#!/usr/bin/env python
"""Management command to populate sample vehicles for testing."""

from django.core.management.base import BaseCommand
from core.models import Vehicle

class Command(BaseCommand):
    help = 'Populate sample vehicles for different driving classes'

    def handle(self, *args, **options):
        vehicles = [
            {
                'registration_number': 'ABC123',
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2020,
                'vehicle_class': 'class1',
                'vehicle_type': 'sedan',
                'notes': 'Light vehicle for Class 1 learners'
            },
            {
                'registration_number': 'DEF456',
                'make': 'Honda',
                'model': 'Civic',
                'year': 2021,
                'vehicle_class': 'class1',
                'vehicle_type': 'sedan',
                'notes': 'Light vehicle for Class 1 learners'
            },
            {
                'registration_number': 'GHI789',
                'make': 'Ford',
                'model': 'Ranger',
                'year': 2019,
                'vehicle_class': 'class2',
                'vehicle_type': 'suv',
                'notes': 'Medium vehicle for Class 2 learners'
            },
            {
                'registration_number': 'JKL012',
                'make': 'Mercedes',
                'model': 'Sprinter',
                'year': 2020,
                'vehicle_class': 'class3',
                'vehicle_type': 'truck',
                'notes': 'Heavy vehicle for Class 3 learners'
            },
            {
                'registration_number': 'MNO345',
                'make': 'Toyota',
                'model': 'Hiace',
                'year': 2018,
                'vehicle_class': 'class4',
                'vehicle_type': 'bus',
                'notes': 'Public service vehicle for Class 4 learners'
            },
            {
                'registration_number': 'PQR678',
                'make': 'Yamaha',
                'model': 'FZ',
                'year': 2021,
                'vehicle_class': 'class5',
                'vehicle_type': 'motorcycle',
                'notes': 'Special vehicle for Class 5 learners'
            }
        ]
        
        created_count = 0
        for vehicle_data in vehicles:
            vehicle, created = Vehicle.objects.get_or_create(
                registration_number=vehicle_data['registration_number'],
                defaults=vehicle_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created vehicle: {vehicle}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Vehicle already exists: {vehicle}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully populated {created_count} new vehicles')
        )
