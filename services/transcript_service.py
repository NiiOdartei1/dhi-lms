# services/transcript_service.py
"""
Service for generating student transcripts - both semester and full academic history.
"""

from collections import defaultdict
from datetime import datetime
from models import (
    StudentCourseGrade, User, Course, SemesterResultRelease, db
)
from services.grading_calculation_engine import GradingCalculationEngine


class TranscriptService:
    """
    Service for generating and managing student transcripts.
    Provides semester-specific and full academic history views.
    """
    
    @staticmethod
    def generate_semester_transcript(student_id, academic_year, semester):
        """
        Generate transcript data for a specific semester.
        
        Args:
            student_id (int): User.id
            academic_year (str): e.g., "2024/2025"
            semester (str): e.g., "1" or "2"
            
        Returns:
            dict: Structured transcript data including:
                - student: User object
                - academic_year: Year
                - semester: Semester
                - courses: List of StudentCourseGrade objects
                - semester_gpa: GPA for the semester
                - semester_weighted_gpa: GPA weighted by credit hours
                - total_credit_hours: Total credits attempted
                - is_released: Whether results are released to student
        """
        student = User.query.get(student_id)
        if not student:
            return None
        
        # Get all grades for this semester
        grades = GradingCalculationEngine.get_student_grades_for_semester(
            student_id, academic_year, semester
        )
        
        # Calculate GPA metrics
        semester_gpa = GradingCalculationEngine.calculate_gpa(grades)
        semester_weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(grades)
        
        # Calculate total credit hours
        total_credit_hours = 0
        for grade in grades:
            course = Course.query.get(grade.course_id)
            if course:
                total_credit_hours += course.credit_hours
        
        # Check if results are released
        is_released = TranscriptService._is_semester_released(academic_year, semester)
        
        # Build course details with course names and assessment weights
        from models import CourseAssessmentScheme
        course_details = []
        for grade in grades:
            course = Course.query.get(grade.course_id)
            if course:
                # Fetch assessment scheme for this course
                scheme = CourseAssessmentScheme.query.filter_by(course_id=course.id).first()
                
                course_details.append({
                    'course': course,
                    'grade': grade,
                    'course_name': course.name,
                    'course_code': course.code,
                    'credit_hours': course.credit_hours,
                    'final_score': grade.final_score,
                    'grade_letter': grade.grade_letter,
                    'quiz_score': grade.quiz_total_score,
                    'quiz_max': grade.quiz_max_possible,
                    'assignment_score': grade.assignment_total_score,
                    'assignment_max': grade.assignment_max_possible,
                    'exam_score': grade.exam_total_score,
                    'exam_max': grade.exam_max_possible,
                    'quiz_weight': scheme.quiz_weight if scheme else 10.0,
                    'assignment_weight': scheme.assignment_weight if scheme else 30.0,
                    'exam_weight': scheme.exam_weight if scheme else 60.0
                })
        
        return {
            'student': student,
            'student_id': student.user_id,
            'student_name': student.full_name,
            'academic_year': academic_year,
            'semester': semester,
            'courses': course_details,
            'semester_gpa': semester_gpa,
            'semester_weighted_gpa': semester_weighted_gpa,
            'total_credit_hours': total_credit_hours,
            'is_released': is_released,
            'generated_at': datetime.utcnow()
        }
    
    @staticmethod
    def generate_full_transcript(student_id):
        """
        Generate complete transcript across all semesters.
        
        Args:
            student_id (int): User.id
            
        Returns:
            dict: Full transcript data including:
                - student: User object
                - all_semesters: Dict of {(academic_year, semester): [grades]}
                - cumulative_gpa: GPA across all semesters
                - cumulative_weighted_gpa: Weighted GPA across all semesters
                - total_credit_hours_attempted: Total credits across all semesters
                - total_credit_hours_earned: Credits for passing grades
                - semesters_summary: List of semester summary dicts
        """
        student = User.query.get(student_id)
        if not student:
            return None
        
        # Get all grades for the student
        all_grades = GradingCalculationEngine.get_student_all_grades(student_id)
        
        # Group by (academic_year, semester)
        grouped = defaultdict(list)
        for grade in all_grades:
            key = (grade.academic_year, grade.semester)
            grouped[key].append(grade)
        
        # Sort by academic year and semester
        sorted_keys = sorted(grouped.keys(), key=lambda x: (x[0], x[1]))
        
        # Build semester summaries
        semesters_summary = []
        for academic_year, semester in sorted_keys:
            grades = grouped[(academic_year, semester)]
            semester_gpa = GradingCalculationEngine.calculate_gpa(grades)
            semester_weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(grades)
            
            total_credits = 0
            for grade in grades:
                course = Course.query.get(grade.course_id)
                if course:
                    total_credits += course.credit_hours
            
            semesters_summary.append({
                'academic_year': academic_year,
                'semester': semester,
                'gpa': semester_gpa,
                'weighted_gpa': semester_weighted_gpa,
                'credit_hours': total_credits,
                'courses_count': len(grades)
            })
        
        # Calculate cumulative GPA
        cumulative_gpa = GradingCalculationEngine.calculate_gpa(all_grades)
        cumulative_weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(all_grades)
        
        # Calculate total credit hours
        total_credit_hours_attempted = 0
        total_credit_hours_earned = 0  # Only for passing grades
        
        passing_grades = {'A', 'B', 'C', 'D'}  # Assuming D and above pass
        
        for grade in all_grades:
            course = Course.query.get(grade.course_id)
            if course:
                total_credit_hours_attempted += course.credit_hours
                if grade.grade_letter in passing_grades:
                    total_credit_hours_earned += course.credit_hours
        
        # Build detailed semester data with course information and weights
        from models import CourseAssessmentScheme
        semesters_detailed = {}
        for academic_year, semester in sorted_keys:
            grades = grouped[(academic_year, semester)]
            
            course_details = []
            for grade in grades:
                course = Course.query.get(grade.course_id)
                if course:
                    # Fetch assessment scheme for this course
                    scheme = CourseAssessmentScheme.query.filter_by(course_id=course.id).first()
                    
                    course_details.append({
                        'course': course,
                        'grade': grade,
                        'course_name': course.name,
                        'course_code': course.code,
                        'credit_hours': course.credit_hours,
                        'final_score': grade.final_score,
                        'grade_letter': grade.grade_letter,
                        'quiz_score': grade.quiz_total_score,
                        'quiz_max': grade.quiz_max_possible,
                        'assignment_score': grade.assignment_total_score,
                        'assignment_max': grade.assignment_max_possible,
                        'exam_score': grade.exam_total_score,
                        'exam_max': grade.exam_max_possible,
                        'quiz_weight': scheme.quiz_weight if scheme else 10.0,
                        'assignment_weight': scheme.assignment_weight if scheme else 30.0,
                        'exam_weight': scheme.exam_weight if scheme else 60.0
                    })
            
            is_released = TranscriptService._is_semester_released(academic_year, semester)
            
            semesters_detailed[(academic_year, semester)] = {
                'academic_year': academic_year,
                'semester': semester,
                'courses': course_details,
                'gpa': GradingCalculationEngine.calculate_gpa(grades),
                'is_released': is_released
            }
        
        return {
            'student': student,
            'student_id': student.user_id,
            'student_name': student.full_name,
            'all_semesters': semesters_detailed,
            'semesters_summary': semesters_summary,
            'cumulative_gpa': cumulative_gpa,
            'cumulative_weighted_gpa': cumulative_weighted_gpa,
            'total_credit_hours_attempted': total_credit_hours_attempted,
            'total_credit_hours_earned': total_credit_hours_earned,
            'generated_at': datetime.utcnow()
        }
    
    @staticmethod
    def _is_semester_released(academic_year, semester):
        """
        Check if results for a semester have been released.
        
        Args:
            academic_year (str): e.g., "2024/2025"
            semester (str): e.g., "1" or "2"
            
        Returns:
            bool: True if released, False otherwise
        """
        release = SemesterResultRelease.query.filter_by(
            academic_year=academic_year,
            semester=semester,
            is_released=True
        ).first()
        
        return bool(release)
    
    @staticmethod
    def get_current_semester_transcript(student_id):
        """
        Get transcript for the most recently released semester.
        
        Args:
            student_id (int): User.id
            
        Returns:
            dict: Semester transcript or None if no released semesters
        """
        # Get latest released semester
        release = (
            SemesterResultRelease.query
            .filter_by(is_released=True)
            .order_by(SemesterResultRelease.released_at.desc())
            .first()
        )
        
        if not release:
            return None
        
        return TranscriptService.generate_semester_transcript(
            student_id, release.academic_year, release.semester
        )
    
    @staticmethod
    def export_semester_transcript_text(transcript_data):
        """
        Export semester transcript as formatted text.
        
        Args:
            transcript_data (dict): Output from generate_semester_transcript()
            
        Returns:
            str: Formatted text transcript
        """
        if not transcript_data:
            return "No transcript data available."
        
        lines = []
        lines.append("=" * 80)
        lines.append("ACADEMIC TRANSCRIPT - SEMESTER REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Student info
        lines.append(f"Student Name: {transcript_data['student_name']}")
        lines.append(f"Student ID: {transcript_data['student_id']}")
        lines.append(f"Academic Year: {transcript_data['academic_year']}")
        lines.append(f"Semester: {transcript_data['semester']}")
        lines.append("")
        
        # Release status
        release_status = "RELEASED" if transcript_data['is_released'] else "NOT RELEASED"
        lines.append(f"Status: {release_status}")
        lines.append("")
        
        # Course details
        lines.append("-" * 80)
        lines.append(f"{'Course Code':<15} {'Course Name':<40} {'Score':<10} {'Grade':<5}")
        lines.append("-" * 80)
        
        for course_detail in transcript_data['courses']:
            code = course_detail['course_code']
            name = course_detail['course_name'][:38]
            score = f"{course_detail['final_score']:.2f}"
            grade = course_detail['grade_letter'] or 'N/A'
            lines.append(f"{code:<15} {name:<40} {score:>10} {grade:>5}")
        
        lines.append("-" * 80)
        lines.append("")
        
        # Summary statistics
        lines.append(f"Total Credit Hours: {transcript_data['total_credit_hours']}")
        lines.append(f"Semester GPA: {transcript_data['semester_gpa']:.2f}")
        lines.append(f"Weighted GPA: {transcript_data['semester_weighted_gpa']:.2f}")
        lines.append("")
        lines.append(f"Generated: {transcript_data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    @staticmethod
    def export_full_transcript_text(transcript_data):
        """
        Export full transcript as formatted text.
        
        Args:
            transcript_data (dict): Output from generate_full_transcript()
            
        Returns:
            str: Formatted text transcript
        """
        if not transcript_data:
            return "No transcript data available."
        
        lines = []
        lines.append("=" * 80)
        lines.append("ACADEMIC TRANSCRIPT - FULL HISTORY")
        lines.append("=" * 80)
        lines.append("")
        
        # Student info
        lines.append(f"Student Name: {transcript_data['student_name']}")
        lines.append(f"Student ID: {transcript_data['student_id']}")
        lines.append("")
        
        # Semester-by-semester details
        for key in sorted(transcript_data['all_semesters'].keys()):
            semester_data = transcript_data['all_semesters'][key]
            
            lines.append("-" * 80)
            lines.append(f"Academic Year: {semester_data['academic_year']} | Semester: {semester_data['semester']}")
            lines.append("-" * 80)
            lines.append(f"{'Course Code':<15} {'Course Name':<40} {'Score':<10} {'Grade':<5}")
            lines.append("-" * 80)
            
            for course_detail in semester_data['courses']:
                code = course_detail['course_code']
                name = course_detail['course_name'][:38]
                score = f"{course_detail['final_score']:.2f}"
                grade = course_detail['grade_letter'] or 'N/A'
                lines.append(f"{code:<15} {name:<40} {score:>10} {grade:>5}")
            
            lines.append("")
            lines.append(f"Semester GPA: {semester_data['gpa']:.2f}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("CUMULATIVE STATISTICS")
        lines.append("=" * 80)
        lines.append(f"Total Credit Hours Attempted: {transcript_data['total_credit_hours_attempted']}")
        lines.append(f"Total Credit Hours Earned: {transcript_data['total_credit_hours_earned']}")
        lines.append(f"Cumulative GPA: {transcript_data['cumulative_gpa']:.2f}")
        lines.append(f"Cumulative Weighted GPA: {transcript_data['cumulative_weighted_gpa']:.2f}")
        lines.append("")
        lines.append(f"Generated: {transcript_data['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    