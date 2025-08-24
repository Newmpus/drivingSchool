# TODO: Fix Django Driving School Application Issues

## Issues Identified:
1. `AttributeError: 'User' object has no attribute 'userprofile'` - Views trying to access non-existent userprofile
2. Database migration issues - Tables not created properly

## Plan of Action:

### Phase 1: Fix User Profile Access Issues
- [ ] Update `core/views/auth_views.py` to use `request.user` directly instead of `request.user.userprofile`
- [ ] Update `core/views/lesson_views.py` to use `request.user` directly instead of `request.user.userprofile`
- [ ] Check other views for similar issues

### Phase 2: Database Migration
- [ ] Run `python manage.py makemigrations` to create any missing migrations
- [ ] Run `python manage.py migrate` to apply all migrations
- [ ] Verify database tables are created correctly

### Phase 3: Testing
- [ ] Test the application to ensure fixes work
- [ ] Run `test_api_book_lesson.py` to verify API endpoint functionality

## Current Status: Starting Phase 1
