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
