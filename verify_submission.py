#!/usr/bin/env python
"""
Verification script to diagnose and fix 'submitted_courses empty' issue
Run: python verify_submission.py
"""

from app import app, db
from models import (
    User, TeacherProfile, TeacherCourseAssignment, 
    Course, SemesterResultRelease
)
from datetime import datetime
import json

# Create Flask app context
with app.app_context():
    print("=" * 80)
    print("TEACHER VETTING SUBMISSION DIAGNOSTIC")
    print("=" * 80)

    # Find the teacher from logs (John Berniana Akwetey)
    print("\n1. FINDING TEACHER...")
    print("-" * 80)

    teacher_user = User.query.filter_by(first_name='John', last_name='Akwetey').first()

    if not teacher_user:
        print("❌ Teacher 'John Berniana Akwetey' not found!")
        print("   Showing all teachers:")
        teachers = User.query.filter_by(role='teacher').all()
        for t in teachers:
            print(f"   - {t.user_id}: {t.full_name}")
    else:
        print(f"✓ Found teacher: {teacher_user.user_id} - {teacher_user.full_name}")
        
        # Get teacher profile
        print("\n2. GETTING TEACHER PROFILE...")
        print("-" * 80)
        
        profile = TeacherProfile.query.filter_by(user_id=teacher_user.user_id).first()
        
        if not profile:
            print("❌ Teacher profile not found!")
        else:
            print(f"✓ Profile ID: {profile.id}")
            print(f"✓ Employee ID: {profile.employee_id}")
            
            # Check assigned courses
            print("\n3. CHECKING ASSIGNED COURSES...")
            print("-" * 80)
            
            assignments = TeacherCourseAssignment.query.filter_by(teacher_id=profile.id).all()
            
            if not assignments:
                print("❌ NO COURSES ASSIGNED TO THIS TEACHER!")
                print("   You need to assign courses in the admin panel")
                print("   OR manually insert with:")
                print(f"   INSERT INTO teacher_course_assignment (teacher_id, course_id)")
                print(f"   VALUES ({profile.id}, <course_id>);")
            else:
                print(f"✓ Found {len(assignments)} assigned course(s):")
                course_ids = []
                for i, a in enumerate(assignments, 1):
                    course = Course.query.get(a.course_id)
                    if course:
                        print(f"   {i}. Course ID {a.course_id}: {course.code} - {course.name}")
                        course_ids.append({
                            'id': course.id,
                            'code': course.code,
                            'name': course.name
                        })
                    else:
                        print(f"   {i}. Course ID {a.course_id}: (COURSE NOT FOUND)")
            
            # Check latest submission
            print("\n4. CHECKING LATEST SUBMISSION...")
            print("-" * 80)
            
            latest_submission = SemesterResultRelease.query.filter_by(
                is_locked=True
            ).order_by(SemesterResultRelease.created_at.desc()).first()
            
            if not latest_submission:
                print("❌ No submissions found yet")
            else:
                print(f"✓ Latest submission:")
                print(f"  - Academic Year: {latest_submission.academic_year}")
                print(f"  - Semester: {latest_submission.semester}")
                print(f"  - Locked At: {latest_submission.locked_at}")
                print(f"  - Is Locked: {latest_submission.is_locked}")
                print(f"  - Is Released: {latest_submission.is_released}")
                
                # Check submitted_courses
                print(f"\n  Submitted Courses:")
                if not latest_submission.submitted_courses:
                    print(f"  ❌ EMPTY! (This is the problem)")
                    print(f"\n  AUTOMATIC FIX:")
                    print(f"  ──────────────")
                    
                    if assignments:
                        # Fix by populating submitted_courses
                        submitted = json.dumps(course_ids)
                        latest_submission.submitted_courses = submitted
                        db.session.commit()
                        print(f"  ✓ Fixed! Updated submitted_courses with {len(course_ids)} course(s)")
                        print(f"  ✓ Changes committed to database")
                        print(f"\n  Now go to /admin/vetting/results and refresh")
                    else:
                        print(f"  ✗ Cannot auto-fix: No courses assigned to teacher")
                        print(f"  → Assign courses first, then try submitting again")
                else:
                    try:
                        courses = json.loads(latest_submission.submitted_courses)
                        print(f"  ✓ Contains {len(courses)} course(s):")
                        for c in courses:
                            print(f"    - {c.get('code', 'N/A')}: {c.get('name', 'N/A')}")
                    except Exception as e:
                        print(f"  ❌ Invalid JSON: {latest_submission.submitted_courses}")


    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if teacher_user and profile and assignments:
        latest = SemesterResultRelease.query.filter_by(is_locked=True).order_by(
            SemesterResultRelease.created_at.desc()
        ).first()
        
        if latest and latest.submitted_courses:
            try:
                courses = json.loads(latest.submitted_courses)
                if len(courses) > 0:
                    print("✓ EVERYTHING LOOKS GOOD!")
                    print(f"  Go to /admin/vetting/results to see {len(courses)} course(s)")
                else:
                    print("⚠ Submitted courses is empty")
            except:
                print("⚠ Submitted courses has invalid JSON")
        else:
            print("⚠ No submission found or submitted_courses is empty")
    elif teacher_user and profile:
        print("⚠ Teacher has no courses assigned")
        print("  Assign courses in admin panel or using database")
    else:
        print("❌ Teacher not found")

    print("=" * 80)
    