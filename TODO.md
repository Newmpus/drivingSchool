# TODO: Modify Student Lesson Tracking and Eligibility Logic

## Steps to Complete

- [x] Update core/models.py: Change get_level() to use self.student_lessons.count() instead of self.lessons_taken
- [x] Update core/models.py: Change eligible_for_vid to use self.student_lessons.count() >= 10 and self.instructor_approved
- [x] Update core/models.py: Change clean() to use self.student_lessons.count() > 30
- [x] Update core/models.py: Add @property total_lessons returning self.student_lessons.count()
- [x] Update core/models.py: Add Django signals on Lesson post_save and post_delete to update student.lessons_taken
- [x] Update core/admin.py: Add total_lessons to list_display
- [x] Update core/admin.py: Add 'mark_instructor_approved' action
- [x] Update core/admin.py: Update list_display to ('username', 'role', 'total_lessons', 'get_level', 'instructor_approved', 'eligible_for_vid')
- [ ] Test the changes in Django admin

# TODO: Create System Functionality Test for Documentation Evidence

## Steps to Complete

- [x] Create core/tests/test_system_functionality.py with test for user registration, login, and dashboard access
- [x] Run the test to verify it works and provide screenshot evidence

# TODO: Fix Admin Panel Issues

## Steps to Complete

- [x] Restore missing columns in admin users table (email, first_name, last_name, is_staff, is_approved, payment_status, payment_verified, payment_proof)
- [x] Update eligible_for_vid to include admins and instructors (they already have licenses)
- [x] Add payment_proof_display method to admin list_display
- [x] Add payment proof display to student detail template
- [ ] Test admin panel functionality
