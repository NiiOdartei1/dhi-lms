"""
Generate test student grades for demonstration.
This creates realistic grade data for the first student.
"""

from app import app, db
from models import (
    User, StudentCourseGrade, StudentCourseRegistration, Course,
    GradingScale, CourseAssessmentScheme
)
from datetime import datetime

def generate_grades():
    """Generate test grades for the first student"""
    
    with app.app_context():
        # Get first student
        student = User.query.filter_by(role='student').first()
        if not student:
            print("❌ No student found!")
            return
        
        print(f"📚 Generating grades for: {student.full_name} ({student.user_id})")
        
        # Check what registrations exist
        all_regs = StudentCourseRegistration.query.all()
        print(f"\n📊 Total registrations in DB: {len(all_regs)}")
        if all_regs:
            # Show unique academic_year/semester combinations
            unique = set()
            for r in all_regs[:20]:
                unique.add((r.academic_year, r.semester))
            print("   Sample academic years/semesters in registrations:")
            for ay, sem in sorted(unique):
                print(f"      {ay} / {sem}")
        
        # Get registrations for first student in ANY semester
        student_regs = StudentCourseRegistration.query.filter_by(
            student_id=student.id
        ).all()
        
        if not student_regs:
            print(f"❌ No registrations for student {student.user_id}!")
            return
        
        # Use first registration's academic period
        first_reg = student_regs[0]
        academic_year = first_reg.academic_year  # This is just "2026", not "2026/2026"
        semester = first_reg.semester
        
        print(f"✓ Using {academic_year} {semester} (from registrations)")
        
        # Get registered courses for this student in this period
        registrations = StudentCourseRegistration.query.filter_by(
            student_id=student.id,
            academic_year=academic_year,
            semester=semester
        ).all()
        
        if not registrations:
            print("❌ No course registrations found for this semester!")
            return
        
        print(f"📖 Found {len(registrations)} course registrations")
        
        # For each course, create grades
        for reg in registrations:
            course = Course.query.get(reg.course_id)
            if not course:
                print(f"⚠️  Course {reg.course_id} not found, skipping")
                continue
            
            # Check if grade already exists
            existing = StudentCourseGrade.query.filter_by(
                student_id=student.id,
                course_id=course.id,
                academic_year=academic_year,
                semester=semester
            ).first()
            
            if existing:
                print(f"✓ Grade already exists for {course.code}, skipping")
                continue
            
            # Get assessment scheme for this course
            scheme = CourseAssessmentScheme.query.filter_by(
                course_id=course.id
            ).first()
            
            if not scheme:
                print(f"⚠️  No assessment scheme for {course.code}, using defaults")
                quiz_weight = 10.0
                assignment_weight = 30.0
                exam_weight = 60.0
            else:
                quiz_weight = scheme.quiz_weight
                assignment_weight = scheme.assignment_weight
                exam_weight = scheme.exam_weight
            
            # Generate sample scores (realistic)
            import random
            random.seed(student.id + course.id)  # Reproducible but varied
            
            quiz_score = random.uniform(70, 95)
            quiz_max = 100.0
            
            assignment_score = random.uniform(75, 98)
            assignment_max = 100.0
            
            exam_score = random.uniform(65, 92)
            exam_max = 100.0
            
            # Calculate percentages
            quiz_pct = (quiz_score / quiz_max) * 100
            assignment_pct = (assignment_score / assignment_max) * 100
            exam_pct = (exam_score / exam_max) * 100
            
            # Calculate weighted final score
            final_score = (
                (quiz_pct * quiz_weight / 100) +
                (assignment_pct * assignment_weight / 100) +
                (exam_pct * exam_weight / 100)
            )
            
            # Get grading scale to map score to letter
            grading_scale = GradingScale.query.filter(
                GradingScale.min_score <= final_score,
                GradingScale.max_score >= final_score
            ).first()
            
            if grading_scale:
                grade_letter = grading_scale.grade_letter
                grade_point = grading_scale.grade_point
                pass_fail = grading_scale.pass_fail
            else:
                # Fallback mapping
                if final_score >= 90:
                    grade_letter, grade_point, pass_fail = 'A', 4.0, 'PASS'
                elif final_score >= 80:
                    grade_letter, grade_point, pass_fail = 'B', 3.0, 'PASS'
                elif final_score >= 70:
                    grade_letter, grade_point, pass_fail = 'C', 2.0, 'PASS'
                elif final_score >= 60:
                    grade_letter, grade_point, pass_fail = 'D', 1.0, 'PASS'
                else:
                    grade_letter, grade_point, pass_fail = 'F', 0.0, 'FAIL'
            
            # Create grade record
            grade = StudentCourseGrade(
                student_id=student.id,
                course_id=course.id,
                academic_year=academic_year,
                semester=semester,
                # Component scores
                quiz_total_score=quiz_score,
                quiz_max_possible=quiz_max,
                assignment_total_score=assignment_score,
                assignment_max_possible=assignment_max,
                exam_total_score=exam_score,
                exam_max_possible=exam_max,
                # Final scores
                final_score=round(final_score, 2),
                grade_letter=grade_letter,
                grade_point=grade_point,
                pass_fail=pass_fail,
                last_updated=datetime.utcnow()
            )
            
            db.session.add(grade)
            print(f"✓ Created grade for {course.code}: {grade_letter} ({final_score:.1f}%)")
        
        # Commit all grades
        db.session.commit()
        print(f"\n✅ Successfully generated test grades!")
        
        # Show summary
        grades = StudentCourseGrade.query.filter_by(
            student_id=student.id,
            academic_year=academic_year,
            semester=semester
        ).all()
        
        if grades:
            total_points = sum(g.grade_point * (Course.query.get(g.course_id).credit_hours or 3) for g in grades)
            total_credits = sum(Course.query.get(g.course_id).credit_hours or 3 for g in grades)
            gpa = total_points / total_credits if total_credits > 0 else 0
            
            print(f"\n📊 Summary for {academic_year} {semester}:")
            print(f"   Courses: {len(grades)}")
            print(f"   Total Credits: {total_credits}")
            print(f"   GPA: {gpa:.2f}")

if __name__ == '__main__':
    generate_grades()
