"""
Management command to populate sample data for testing the driving school system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Vehicle, Lesson, StudentProgress
from datetime import date, time, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Populate sample data for testing the driving school system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vehicles-only',
            action='store_true',
            help='Only create sample vehicles',
        )
        parser.add_argument(
            '--lessons-only',
            action='store_true',
            help='Only create sample lessons',
        )

    def handle(self, *args, **options):
        if options['vehicles_only']:
            self.create_sample_vehicles()
        elif options['lessons_only']:
            self.create_sample_lessons()
        else:
            self.create_sample_vehicles()
            self.create_sample_lessons()
            self.create_sample_progress()

    def create_sample_vehicles(self):
        """Create sample vehicles for testing."""
        vehicles_data = [
            {
                'registration_number': 'DS001',
                'make': 'Toyota',
                'model': 'Corolla',
                'year': 2022,
                'vehicle_class': 'class1',
                'vehicle_type': 'sedan',
                'notes': 'Excellent condition, perfect for beginners'
            },
            {
                'registration_number': 'DS002',
                'make': 'Honda',
                'model': 'Civic',
                'year': 2021,
                'vehicle_class': 'class1',
                'vehicle_type': 'sedan',
                'notes': 'Reliable and fuel-efficient'
            },
            {
                'registration_number': 'DS003',
                'make': 'Ford',
                'model': 'Focus',
                'year': 2020,
                'vehicle_class': 'class1',
                'vehicle_type': 'hatchback',
                'notes': 'Compact and easy to maneuver'
            },
            {
                'registration_number': 'DS004',
                'make': 'Volkswagen',
                'model': 'Golf',
                'year': 2023,
                'vehicle_class': 'class1',
                'vehicle_type': 'hatchback',
                'notes': 'Latest model with advanced safety features'
            },
            {
                'registration_number': 'DS005',
                'make': 'Nissan',
                'model': 'X-Trail',
                'year': 2022,
                'vehicle_class': 'class2',
                'vehicle_type': 'suv',
                'notes': 'Good for learning SUV handling'
            },
            {
                'registration_number': 'DS006',
                'make': 'Ford',
                'model': 'Transit',
                'year': 2021,
                'vehicle_class': 'class3',
                'vehicle_type': 'truck',
                'notes': 'Commercial vehicle training'
            }
        ]

        created_count = 0
        for vehicle_data in vehicles_data:
            vehicle, created = Vehicle.objects.get_or_create(
                registration_number=vehicle_data['registration_number'],
                defaults=vehicle_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created vehicle: {vehicle.registration_number}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Vehicle already exists: {vehicle.registration_number}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} vehicles')
        )

    def create_sample_lessons(self):
        """Create sample lessons for testing."""
        # Get users
        students = User.objects.filter(role='student')[:3]
        tutors = User.objects.filter(role='tutor')[:2]

        if not students.exists():
            self.stdout.write(
                self.style.WARNING('No students found. Please create some student users first.')
            )
            return

        if not tutors.exists():
            self.stdout.write(
                self.style.WARNING('No tutors found. Please create some tutor users first.')
            )
            return

        # Create lessons for the next few days
        created_count = 0
        today = date.today()
        
        for i in range(5):  # Create lessons for next 5 days
            lesson_date = today + timedelta(days=i+1)
            
            # Skip weekends
            if lesson_date.weekday() >= 5:
                continue
                
            for student in students:
                for hour in [9, 11, 14, 16]:  # Different time slots
                    if random.choice([True, False]):  # Randomly create some lessons
                        start_time = time(hour, 0)
                        end_time = time(hour + 1, 0)
                        tutor = random.choice(tutors)
                        
                        # Check if lesson already exists
                        if not Lesson.objects.filter(
                            student=student,
                            tutor=tutor,
                            date=lesson_date,
                            start_time=start_time
                        ).exists():
                            lesson = Lesson.objects.create(
                                student=student,
                                tutor=tutor,
                                date=lesson_date,
                                start_time=start_time,
                                end_time=end_time,
                                location='Driving School HQ'
                            )
                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Created lesson: {student.username} with {tutor.username} on {lesson_date}'
                                )
                            )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} lessons')
        )

    def create_sample_progress(self):
        """Create sample progress records for existing lessons."""
        # Get some completed lessons (past lessons)
        past_lessons = Lesson.objects.filter(date__lt=date.today())[:5]
        
        if not past_lessons.exists():
            self.stdout.write(
                self.style.WARNING('No past lessons found to add progress records.')
            )
            return

        progress_samples = [
            {
                'skills_covered': 'Parallel parking, three-point turns, highway merging',
                'progress_notes': 'Student showed excellent improvement in parallel parking. Confidence has increased significantly.',
                'instructor_feedback': 'Great progress today! Keep practicing the techniques we covered.',
                'next_lesson_focus': 'Focus on night driving and adverse weather conditions'
            },
            {
                'skills_covered': 'Basic vehicle controls, steering, braking',
                'progress_notes': 'First lesson went well. Student is eager to learn and follows instructions carefully.',
                'instructor_feedback': 'Good foundation established. Student shows natural aptitude for driving.',
                'next_lesson_focus': 'Introduction to traffic rules and road signs'
            },
            {
                'skills_covered': 'Roundabouts, lane changing, defensive driving',
                'progress_notes': 'Student handled roundabouts well but needs more practice with lane changing timing.',
                'instructor_feedback': 'Improvement needed in checking blind spots before lane changes.',
                'next_lesson_focus': 'More practice with complex intersections and lane changes'
            }
        ]

        created_count = 0
        for lesson in past_lessons:
            if not StudentProgress.objects.filter(lesson=lesson).exists():
                progress_data = random.choice(progress_samples)
                StudentProgress.objects.create(
                    student=lesson.student,
                    lesson=lesson,
                    **progress_data
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created progress record for lesson {lesson.id}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} progress records')
        )
