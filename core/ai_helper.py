"""
AI Helper module for driving school system.
Provides intelligent suggestions for vehicle allocation, lesson scheduling, and student progress analysis.
Works completely offline using local database data.
"""
import logging
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count
from django.utils import timezone

logger = logging.getLogger(__name__)

class DrivingSchoolAI:
    """AI helper class for driving school management."""
    
    def __init__(self):
        """Initialize the AI helper."""
        self.logger = logging.getLogger(__name__)
    
    def suggest_available_vehicles(self, lesson_date: date, start_time: time, end_time: time, 
                                 student_class: str = 'class1') -> List[Dict[str, Any]]:
        """
        Suggest available vehicles for a lesson based on date, time, and student class.
        
        Args:
            lesson_date: The date of the lesson
            start_time: Start time of the lesson
            end_time: End time of the lesson
            student_class: The driving class (class1, class2, etc.)
        
        Returns:
            List of available vehicles with suggestions
        """
        from .models import Vehicle, VehicleAllocation, Lesson
        
        try:
            # Get vehicles that match the student class
            preferred_vehicles = Vehicle.objects.filter(
                vehicle_class=student_class,
                is_available=True
            ).exclude(
                vehicleallocation__lesson__date=lesson_date,
                vehicleallocation__lesson__start_time__lt=end_time,
                vehicleallocation__lesson__end_time__gt=start_time
            )
            
            # Get any available vehicles as fallback
            fallback_vehicles = Vehicle.objects.filter(
                is_available=True
            ).exclude(
                vehicleallocation__lesson__date=lesson_date,
                vehicleallocation__lesson__start_time__lt=end_time,
                vehicleallocation__lesson__end_time__gt=start_time
            ).exclude(
                id__in=preferred_vehicles.values_list('id', flat=True)
            )
            
            suggestions = []
            
            # Add preferred vehicles
            for vehicle in preferred_vehicles:
                suggestions.append({
                    'vehicle': vehicle,
                    'recommendation': 'Perfect Match',
                    'reason': f'Ideal for {vehicle.get_vehicle_class_display()}',
                    'priority': 1,
                    'confidence': 95
                })
            
            # Add fallback vehicles
            for vehicle in fallback_vehicles:
                suggestions.append({
                    'vehicle': vehicle,
                    'recommendation': 'Alternative Option',
                    'reason': f'Available {vehicle.get_vehicle_class_display()} vehicle',
                    'priority': 2,
                    'confidence': 75
                })
            
            # Sort by priority and confidence
            suggestions.sort(key=lambda x: (x['priority'], -x['confidence']))
            
            self.logger.info(f"Found {len(suggestions)} vehicle suggestions for {lesson_date} {start_time}-{end_time}")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting vehicles: {str(e)}")
            return []
    
    def suggest_optimal_lesson_times(self, tutor_id: int, student_id: int, 
                                   preferred_date: date = None) -> List[Dict[str, Any]]:
        """
        Suggest optimal lesson times based on tutor availability, student history, and vehicle availability.
        
        Args:
            tutor_id: ID of the tutor
            student_id: ID of the student
            preferred_date: Preferred date (optional)
        
        Returns:
            List of suggested time slots
        """
        from .models import User, Lesson, Vehicle
        
        try:
            if not preferred_date:
                preferred_date = timezone.now().date() + timedelta(days=1)
            
            # Get tutor and student
            tutor = User.objects.get(id=tutor_id, role='tutor')
            student = User.objects.get(id=student_id, role='student')
            
            # Define possible time slots (8 AM to 6 PM, 1-hour slots)
            time_slots = []
            for hour in range(8, 18):
                start_time = time(hour, 0)
                end_time = time(hour + 1, 0)
                time_slots.append((start_time, end_time))
            
            suggestions = []
            
            for start_time, end_time in time_slots:
                # Check tutor availability
                tutor_busy = Lesson.objects.filter(
                    tutor=tutor,
                    date=preferred_date,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exists()
                
                # Check student availability
                student_busy = Lesson.objects.filter(
                    student=student,
                    date=preferred_date,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).exists()
                
                if not tutor_busy and not student_busy:
                    # Check vehicle availability
                    available_vehicles = Vehicle.objects.filter(
                        is_available=True
                    ).exclude(
                        vehicleallocation__lesson__date=preferred_date,
                        vehicleallocation__lesson__start_time__lt=end_time,
                        vehicleallocation__lesson__end_time__gt=start_time
                    ).count()
                    
                    if available_vehicles > 0:
                        # Calculate confidence based on various factors
                        confidence = 80
                        
                        # Prefer morning slots (higher confidence)
                        if start_time.hour < 12:
                            confidence += 10
                        
                        # Prefer slots with more vehicle options
                        if available_vehicles > 2:
                            confidence += 5
                        
                        suggestions.append({
                            'date': preferred_date,
                            'start_time': start_time,
                            'end_time': end_time,
                            'available_vehicles': available_vehicles,
                            'confidence': min(confidence, 100),
                            'recommendation': 'Available Slot',
                            'reason': f'{available_vehicles} vehicles available'
                        })
            
            # Sort by confidence
            suggestions.sort(key=lambda x: -x['confidence'])
            
            self.logger.info(f"Found {len(suggestions)} time slot suggestions for {preferred_date}")
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting lesson times: {str(e)}")
            return []
    
    def analyze_student_progress(self, student_id: int) -> Dict[str, Any]:
        """
        Analyze student progress and provide insights.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Dictionary with progress analysis
        """
        from .models import User, Lesson, StudentProgress
        
        try:
            student = User.objects.get(id=student_id, role='student')
            
            # Get all lessons for the student
            lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')
            progress_records = StudentProgress.objects.filter(student=student).order_by('-created_at')
            
            total_lessons = lessons.count()
            total_progress_records = progress_records.count()
            
            if total_lessons == 0:
                return {
                    'student_name': student.get_full_name() or student.username,
                    'total_lessons': 0,
                    'analysis': 'No lessons completed yet',
                    'recommendations': ['Book your first lesson to get started!'],
                    'progress_score': 0
                }
            
            # Calculate progress metrics
            recent_lessons = lessons.filter(
                date__gte=timezone.now().date() - timedelta(days=30)
            ).count()
            
            # Analyze progress trends
            recommendations = []
            progress_score = 50  # Base score
            
            # Lesson frequency analysis
            if recent_lessons >= 4:
                recommendations.append("Great consistency! Keep up the regular practice.")
                progress_score += 20
            elif recent_lessons >= 2:
                recommendations.append("Good progress. Consider booking more frequent lessons.")
                progress_score += 10
            else:
                recommendations.append("Consider booking more regular lessons for better progress.")
                progress_score -= 10
            
            # Progress record analysis
            if total_progress_records > 0:
                latest_progress = progress_records.first()
                if 'excellent' in latest_progress.instructor_feedback.lower():
                    recommendations.append("Excellent feedback from instructor! You're doing great.")
                    progress_score += 15
                elif 'good' in latest_progress.instructor_feedback.lower():
                    recommendations.append("Good progress noted by instructor.")
                    progress_score += 10
                
                # Check for areas needing improvement
                if 'practice' in latest_progress.next_lesson_focus.lower():
                    recommendations.append("Focus on practicing the areas mentioned by your instructor.")
            
            # Ensure score is within bounds
            progress_score = max(0, min(100, progress_score))
            
            analysis = f"Completed {total_lessons} lessons with {total_progress_records} progress records. "
            if progress_score >= 80:
                analysis += "Excellent progress!"
            elif progress_score >= 60:
                analysis += "Good progress, keep it up!"
            elif progress_score >= 40:
                analysis += "Steady progress, consider more frequent lessons."
            else:
                analysis += "Getting started, book more lessons for better progress."
            
            return {
                'student_name': student.get_full_name() or student.username,
                'total_lessons': total_lessons,
                'recent_lessons': recent_lessons,
                'progress_records': total_progress_records,
                'analysis': analysis,
                'recommendations': recommendations,
                'progress_score': progress_score
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing student progress: {str(e)}")
            return {
                'student_name': 'Unknown',
                'total_lessons': 0,
                'analysis': 'Error analyzing progress',
                'recommendations': ['Please try again later'],
                'progress_score': 0
            }
    
    def generate_progress_comment_suggestion(self, lesson_id: int) -> str:
        """
        Generate a suggested progress comment for a lesson.
        
        Args:
            lesson_id: ID of the lesson
        
        Returns:
            Suggested comment text
        """
        from .models import Lesson, StudentProgress
        
        try:
            lesson = Lesson.objects.get(id=lesson_id)
            student = lesson.student
            
            # Get previous progress records
            previous_records = StudentProgress.objects.filter(
                student=student
            ).order_by('-created_at')[:3]
            
            # Base comment templates
            base_comments = [
                f"Good lesson with {student.get_full_name() or student.username} today.",
                f"Productive session with {student.get_full_name() or student.username}.",
                f"Made progress in today's lesson with {student.get_full_name() or student.username}."
            ]
            
            # Skills suggestions based on lesson count
            total_lessons = Lesson.objects.filter(student=student).count()
            
            if total_lessons <= 3:
                skills = "Basic vehicle controls, steering, and observation"
                focus = "Continue practicing basic controls and road awareness"
            elif total_lessons <= 6:
                skills = "Traffic rules, signaling, and lane positioning"
                focus = "Practice more complex maneuvers and traffic situations"
            elif total_lessons <= 10:
                skills = "Parking, reversing, and advanced maneuvers"
                focus = "Prepare for driving test with mock examinations"
            else:
                skills = "Test preparation and advanced driving techniques"
                focus = "Final preparation for driving test"
            
            # Generate comment
            comment = f"{base_comments[lesson_id % len(base_comments)]} "
            comment += f"Covered: {skills}. "
            comment += f"Next focus: {focus}."
            
            return comment
            
        except Exception as e:
            self.logger.error(f"Error generating progress comment: {str(e)}")
            return "Good lesson today. Student showed improvement in driving skills."
    
    def generate_progress_feedback(self, lessons: list, progress_records: list = None) -> str:
        """
        Generate AI feedback based on lessons and performance data.
        
        Args:
            lessons: List of lesson objects for the student
            progress_records: List of progress record objects (optional)
        
        Returns:
            AI-generated feedback string
        """
        try:
            if not lessons:
                return "No lessons completed yet. Book your first lesson to get started with personalized AI feedback!"
            
            total_lessons = len(lessons)
            recent_lessons = [l for l in lessons if l.date >= timezone.now().date() - timedelta(days=30)]
            
            # Analyze lesson frequency
            feedback_parts = []
            
            if len(recent_lessons) >= 4:
                feedback_parts.append("🎯 Excellent lesson frequency! Your consistent practice is key to rapid improvement.")
            elif len(recent_lessons) >= 2:
                feedback_parts.append("📈 Good progress with regular lessons. Consider booking more frequent sessions for faster improvement.")
            else:
                feedback_parts.append("⏰ Consider booking more regular lessons. Consistent practice leads to better skill retention.")
            
            # Analyze progress records if available
            if progress_records:
                recent_progress = [p for p in progress_records if p.created_at >= timezone.now() - timedelta(days=30)]
                
                if recent_progress:
                    latest_progress = recent_progress[0]
                    
                    # Analyze feedback sentiment
                    feedback_text = latest_progress.instructor_feedback.lower()
                    if any(word in feedback_text for word in ['excellent', 'outstanding', 'great', 'superb']):
                        feedback_parts.append("🌟 Your instructor's recent feedback is very positive! You're demonstrating excellent driving skills.")
                    elif any(word in feedback_text for word in ['good', 'well', 'improved', 'better']):
                        feedback_parts.append("✅ Good progress noted by your instructor. Keep building on these improvements!")
                    elif any(word in feedback_text for word in ['practice', 'work on', 'focus', 'improve']):
                        feedback_parts.append("🎯 Your instructor has identified specific areas for improvement. Focus on these during practice.")
                    
                    # Analyze skills progression
                    skills_mentioned = []
                    for record in recent_progress[:3]:  # Last 3 records
                        skills_mentioned.extend(record.skills_covered.lower().split())
                    
                    common_skills = ['parking', 'reversing', 'signaling', 'observation', 'steering', 'braking']
                    covered_skills = [skill for skill in common_skills if skill in ' '.join(skills_mentioned)]
                    
                    if len(covered_skills) >= 4:
                        feedback_parts.append("🚗 You're covering a wide range of driving skills. This comprehensive approach will prepare you well for your test.")
                    elif len(covered_skills) >= 2:
                        feedback_parts.append("📚 You're building a solid foundation with multiple driving skills. Continue expanding your skill set.")
            
            # Provide recommendations based on lesson count
            if total_lessons <= 5:
                feedback_parts.append("🔰 As a beginner, focus on mastering basic vehicle controls and road awareness. Every lesson builds important muscle memory.")
            elif total_lessons <= 15:
                feedback_parts.append("🚦 You're in the skill-building phase. Practice complex maneuvers and traffic situations to build confidence.")
            elif total_lessons <= 25:
                feedback_parts.append("🎓 You're approaching test readiness! Focus on test routes and practice mock examinations.")
            else:
                feedback_parts.append("🏆 With extensive practice, you should be well-prepared for your driving test. Consider booking your test soon!")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating progress feedback: {str(e)}")
            return "Unable to generate AI feedback at this time. Please try again later."
    
    def generate_comprehensive_report_data(self, student_id: int) -> Dict[str, Any]:
        """
        Generate comprehensive report data for PDF/CSV export.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Dictionary with comprehensive report data
        """
        from .models import User, Lesson, StudentProgress
        
        try:
            student = User.objects.get(id=student_id, role='student')
            lessons = Lesson.objects.filter(student=student).order_by('date', 'start_time')
            progress_records = StudentProgress.objects.filter(student=student).order_by('-created_at')
            
            # Generate AI analysis
            ai_analysis = self.analyze_student_progress(student_id)
            ai_feedback = self.generate_progress_feedback(list(lessons), list(progress_records))
            
            # Calculate statistics
            total_hours = sum(lesson.get_duration() for lesson in lessons) / 60.0
            lessons_with_progress = progress_records.count()
            completion_rate = (lessons_with_progress / lessons.count() * 100) if lessons.count() > 0 else 0
            
            # Get recent activity
            recent_lessons = lessons.filter(date__gte=timezone.now().date() - timedelta(days=30))
            
            # Prepare lesson data
            lesson_data = []
            for lesson in lessons:
                progress = progress_records.filter(lesson=lesson).first()
                lesson_data.append({
                    'date': lesson.date,
                    'time': f"{lesson.start_time.strftime('%H:%M')} - {lesson.end_time.strftime('%H:%M')}",
                    'duration': lesson.get_duration(),
                    'tutor': lesson.tutor.get_full_name() or lesson.tutor.username,
                    'location': lesson.location,
                    'skills_covered': progress.skills_covered if progress else 'Not recorded',
                    'progress_notes': progress.progress_notes if progress else 'Not recorded',
                    'instructor_feedback': progress.instructor_feedback if progress else 'Not recorded',
                    'next_focus': progress.next_lesson_focus if progress else 'Not recorded'
                })
            
            return {
                'student_info': {
                    'name': student.get_full_name() or student.username,
                    'email': student.email,
                    'phone': student.phone or 'Not provided',
                    'address': student.address or 'Not provided',
                    'registration_date': student.date_joined.strftime('%Y-%m-%d')
                },
                'statistics': {
                    'total_lessons': lessons.count(),
                    'total_hours': round(total_hours, 1),
                    'lessons_with_progress': lessons_with_progress,
                    'completion_rate': round(completion_rate, 1),
                    'recent_lessons_30_days': recent_lessons.count(),
                    'progress_score': ai_analysis.get('progress_score', 0)
                },
                'ai_insights': {
                    'analysis': ai_analysis.get('analysis', 'No analysis available'),
                    'feedback': ai_feedback,
                    'recommendations': ai_analysis.get('recommendations', []),
                    'progress_score': ai_analysis.get('progress_score', 0)
                },
                'lesson_history': lesson_data,
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report data: {str(e)}")
            return {
                'error': f'Error generating report: {str(e)}',
                'student_info': {'name': 'Unknown'},
                'statistics': {},
                'ai_insights': {},
                'lesson_history': [],
                'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def get_vehicle_utilization_report(self) -> Dict[str, Any]:
        """
        Generate vehicle utilization report for admin dashboard.
        
        Returns:
            Dictionary with vehicle utilization data
        """
        from .models import Vehicle, VehicleAllocation, Lesson
        
        try:
            vehicles = Vehicle.objects.all()
            report_data = []
            
            for vehicle in vehicles:
                # Count lessons in the last 30 days
                recent_lessons = VehicleAllocation.objects.filter(
                    vehicle=vehicle,
                    lesson__date__gte=timezone.now().date() - timedelta(days=30)
                ).count()
                
                # Calculate utilization percentage (assuming max 8 lessons per day)
                max_possible_lessons = 30 * 8  # 30 days * 8 possible lessons per day
                utilization = (recent_lessons / max_possible_lessons) * 100 if max_possible_lessons > 0 else 0
                
                report_data.append({
                    'vehicle': vehicle,
                    'recent_lessons': recent_lessons,
                    'utilization_percentage': round(utilization, 1),
                    'status': 'High' if utilization > 50 else 'Medium' if utilization > 20 else 'Low'
                })
            
            # Sort by utilization
            report_data.sort(key=lambda x: -x['utilization_percentage'])
            
            return {
                'vehicles': report_data,
                'total_vehicles': len(report_data),
                'average_utilization': round(sum(v['utilization_percentage'] for v in report_data) / len(report_data), 1) if report_data else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating vehicle utilization report: {str(e)}")
            return {'vehicles': [], 'total_vehicles': 0, 'average_utilization': 0}

# Global AI helper instance
ai_helper = DrivingSchoolAI()
