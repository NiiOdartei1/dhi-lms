# LMS Grading System - Quick Reference Card

## The One File You Need to Know

```python
from services.grading_calculation_engine import GradingCalculationEngine
```

---

## Main Methods

### 1. Calculate Single Grade (Most Common)
```python
grade = GradingCalculationEngine.calculate_course_grade(
    student_id=user.id,
    course_id=course.id,
    academic_year="2024",
    semester="1"
)

# Result object has:
grade.final_score      # 85.75
grade.grade_letter     # "B+"
grade.grade_point      # 3.3
grade.pass_fail        # "PASS"
grade.quiz_raw_score   # 19
grade.quiz_max_score   # 25
# ... etc for all details
```

### 2. Recalculate All Courses for Student
```python
result = GradingCalculationEngine.recalculate_student_all_courses(
    student_id=user.id,
    academic_year="2024",
    semester="1"
)

# Returns:
result['success_count']  # 5
result['error_count']    # 0
result['errors']         # []
```

### 3. Get Semester Grades
```python
grades = GradingCalculationEngine.get_student_grades_for_semester(
    student_id=user.id,
    academic_year="2024",
    semester="1"
)

# grades is a list of StudentCourseGrade objects
for grade in grades:
    print(f"{grade.course.code}: {grade.final_score} ({grade.grade_letter})")
```

### 4. Calculate GPA
```python
# Simple GPA (unweighted)
gpa = GradingCalculationEngine.calculate_gpa(grades)  # 3.45

# Credit-weighted GPA
weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(grades)  # 3.52
```

### 5. Get Full Transcript
```python
all_grades = GradingCalculationEngine.get_student_all_grades(student_id=user.id)
cumulative_gpa = GradingCalculationEngine.calculate_gpa(all_grades)
```

### 6. Batch Semester Finalization
```python
result = GradingCalculationEngine.recalculate_all_students_all_courses(
    academic_year="2024",
    semester="1"
)

# Returns statistics
result['total_calculated']  # 250
result['total_errors']      # 3
```

---

## Convert Score to Letter Grade

```python
from services.grade_service import GradeService

grade_obj = GradeService.get_grade(85.75)  # Get grade for score
# Returns: GradingScale(grade_letter='B+', grade_point=3.3, ...)

letter = grade_obj.grade_letter
point = grade_obj.grade_point
status = grade_obj.pass_fail  # "PASS" or "FAIL"
```

---

## The Grading Formula

```
Final Score = (Quiz% × 10) + (Assignment% × 30) + (Exam% × 60)

Example:
  Quiz: 19/25 = 76%
  Assignment: 37/40 = 92.5%
  Exam: 42/50 = 84%

  Final = (76 ÷ 100 × 10) + (92.5 ÷ 100 × 30) + (84 ÷ 100 × 60)
        = 7.6 + 27.75 + 50.4
        = 85.75 → Grade: B+
```

---

## Error Handling

```python
try:
    grade = GradingCalculationEngine.calculate_course_grade(...)
    if grade is None:
        print("ERROR: Assessment scheme not configured")
except Exception as e:
    print(f"ERROR: {str(e)}")
```

---

## Common Scenarios

### Scenario 1: Admin calculates grades after submission
```python
# After teacher submits grades for course
result = GradingCalculationEngine.recalculate_student_all_courses(
    student_id=student.id,
    academic_year="2024",
    semester="1"
)
if result['error_count'] == 0:
    print("✓ Grades calculated successfully")
else:
    print(f"✗ {result['error_count']} errors occurred")
```

### Scenario 2: Finalize semester (batch)
```python
# End of semester - finalize all grades
from services.semester_grading_service import SemesterGradingService

result = SemesterGradingService.finalize_all_course_grades(
    academic_year="2024",
    semester="1"
)
print(f"Finalized {result['success_count']} courses")
```

### Scenario 3: Student views transcript
```python
# From student portal
grades = GradingCalculationEngine.get_student_grades_for_semester(
    student_id=current_user.id,
    academic_year="2024",
    semester="1"
)

gpa = GradingCalculationEngine.calculate_gpa(grades)

# Display in template:
# GPA: 3.45
# Courses:
#   CSC101: 85.75 (B+)
#   MAT101: 78.00 (B-)
#   ENG101: 92.50 (A-)
```

### Scenario 4: Admin views class results
```python
# Get grades for all students in a course
from models import StudentCourseGrade

grades = StudentCourseGrade.query.filter_by(
    course_id=course.id,
    academic_year="2024",
    semester="1"
).all()

# Calculate class statistics
average_score = sum(g.final_score for g in grades) / len(grades)
passed = sum(1 for g in grades if g.pass_fail == "PASS")
failed = len(grades) - passed

print(f"Class Average: {average_score:.2f}")
print(f"Pass Rate: {passed}/{len(grades)}")
```

---

## Data Stored in StudentCourseGrade

| Field | Example | Purpose |
|-------|---------|---------|
| student_id | 5 | Student record |
| course_id | 12 | Course record |
| academic_year | "2024" | Year |
| semester | "1" | Semester |
| quiz_raw_score | 19 | Total quiz points |
| quiz_max_score | 25 | Total possible quiz points |
| quiz_percentage | 76.0 | Quiz as percentage |
| quiz_weighted_score | 7.6 | Quiz weighted by 10% |
| assignment_raw_score | 37 | Total assignment points |
| assignment_max_score | 40 | Total possible assignment points |
| assignment_percentage | 92.5 | Assignment as percentage |
| assignment_weighted_score | 27.75 | Assignment weighted by 30% |
| exam_raw_score | 42 | Total exam points |
| exam_max_score | 50 | Total possible exam points |
| exam_percentage | 84.0 | Exam as percentage |
| exam_weighted_score | 50.4 | Exam weighted by 60% |
| final_score | 85.75 | **Sum of weighted scores** |
| grade_letter | "B+" | Letter grade |
| grade_point | 3.3 | Grade point (4.0 scale) |
| pass_fail | "PASS" | Pass/Fail status |
| is_finalized | True | Ready for release? |
| is_released | True | Visible to student? |
| calculated_at | 2026-02-01 | When calculated |

---

## GPA Scale Reference

| Grade | Points | Range |
|-------|--------|-------|
| A | 4.0 | 90-100 |
| A- | 3.7 | 85-89 |
| B+ | 3.3 | 83-84 |
| B | 3.0 | 80-82 |
| B- | 2.7 | 78-79 |
| C+ | 2.3 | 76-77 |
| C | 2.0 | 70-75 |
| C- | 1.7 | 68-69 |
| D+ | 1.3 | 66-67 |
| D | 1.0 | 60-65 |
| F | 0.0 | 0-59 |

*(Configurable in GradingScale model)*

---

## Imports You'll Need

```python
# Main calculation engine
from services.grading_calculation_engine import GradingCalculationEngine

# Grade lookup
from services.grade_service import GradeService

# Semester operations
from services.semester_grading_service import SemesterGradingService

# Transcript generation
from services.transcript_service import TranscriptService

# Database models
from models import StudentCourseGrade, GradingScale, CourseAssessmentScheme
```

---

## Debugging Tips

### Check if assessment scheme exists
```python
from models import CourseAssessmentScheme

scheme = CourseAssessmentScheme.query.filter_by(course_id=course_id).first()
if not scheme:
    print("ERROR: Scheme not configured for this course")
else:
    print(f"Quiz: {scheme.quiz_weight}%")
    print(f"Assignment: {scheme.assignment_weight}%")
    print(f"Exam: {scheme.exam_weight}%")
```

### Check if student has submissions
```python
from models import StudentQuizSubmission, StudentCourseGrade

subs = StudentQuizSubmission.query.filter_by(
    student_id=student_id,
    # ... join with Quiz where Quiz.course_id=course_id
).all()

print(f"Quiz submissions: {len(subs)}")
for sub in subs:
    print(f"  - {sub.score}/{sub.quiz.max_score}")
```

### Check grade calculation details
```python
grade = StudentCourseGrade.query.filter_by(
    student_id=student_id,
    course_id=course_id,
    academic_year="2024",
    semester="1"
).first()

print(f"Quiz: {grade.quiz_raw_score}/{grade.quiz_max_score} = {grade.quiz_percentage}% → {grade.quiz_weighted_score}")
print(f"Assignment: {grade.assignment_raw_score}/{grade.assignment_max_score} = {grade.assignment_percentage}% → {grade.assignment_weighted_score}")
print(f"Exam: {grade.exam_raw_score}/{grade.exam_max_score} = {grade.exam_percentage}% → {grade.exam_weighted_score}")
print(f"Final: {grade.final_score} → {grade.grade_letter}")
```

---

## Performance Notes

✅ **Efficient queries**
- Uses `.join()` for submission queries
- Aggregates at database level

✅ **Batch operations**
- Process semester at once
- Commit in batches

✅ **Caching**
- GradingScale queries are lightweight
- Consider caching for 1000+ student operations

⚠️ **Avoid**
- Individual calculations in loops (use batch methods)
- Recalculating unnecessarily
- Accessing grade.course multiple times (load once)

---

## Documentation Files

| File | Purpose |
|------|---------|
| **GRADING_SYSTEM_IMPLEMENTATION.md** | Complete implementation guide |
| **GRADING_SYSTEM_ARCHITECTURE.md** | Visual diagrams and workflows |
| **GRADING_SYSTEM_COMPLETION_SUMMARY.md** | What changed and why |
| **GRADING_SYSTEM_QUICK_REFERENCE.md** | This file |

---

## Support

For detailed information, see:
1. `GRADING_SYSTEM_IMPLEMENTATION.md` - Complete guide
2. `services/grading_calculation_engine.py` - Inline documentation
3. `services/grade_service.py` - Grade lookup details

---

**Last Updated:** February 1, 2026  
**Status:** Production Ready ✅
