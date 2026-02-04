# LMS Grading System Implementation Guide

## Overview

This document describes the clean, consolidated grading system implemented for the LMS platform. The system provides a single source of truth for all grade calculations using a standardized weighted average formula.

## Architecture

### Core Components

#### 1. **GradingCalculationEngine** (`services/grading_calculation_engine.py`)
**PRIMARY ENGINE** - All grade calculations go through this class.

**Key Methods:**
- `calculate_course_grade(student_id, course_id, academic_year, semester)` - Main calculation method
- `recalculate_student_all_courses(student_id, academic_year, semester)` - Batch recalculation
- `recalculate_all_students_all_courses(academic_year, semester)` - Semester-wide finalization
- `get_student_grades_for_semester(student_id, academic_year, semester)` - Fetch semester grades
- `get_student_all_grades(student_id)` - Fetch all grades across semesters
- `calculate_gpa(grades)` - Simple GPA calculation
- `calculate_weighted_gpa(grades)` - Credit-weighted GPA calculation

**Internal Methods (private):**
- `_get_quiz_totals(student_id, course_id)` - Aggregates quiz scores
- `_get_assignment_totals(student_id, course_id)` - Aggregates assignment scores
- `_get_exam_totals(student_id, course_id)` - Aggregates exam scores

#### 2. **GradeService** (`services/grade_service.py`)
**LOOKUP SERVICE** - Converts numeric scores to letter grades.

**Key Methods:**
- `get_grade(percent)` - Get letter grade for a score (e.g., 85.4 → B+)
- `get_all_grades()` - Get all grading scale entries
- `get_grade_by_letter(letter)` - Look up grade details by letter

#### 3. **SemesterGradingService** (`services/semester_grading_service.py`)
**BATCH OPERATIONS** - Handles semester-level operations.

Uses GradingCalculationEngine for all calculations but adds:
- Result finalization
- Result release/recall
- Semester locking/unlocking
- Grading reports and summaries

#### 4. **TranscriptService** (`services/transcript_service.py`)
**TRANSCRIPT GENERATION** - Creates student transcripts.

Uses GradingCalculationEngine to fetch grades and calculate GPAs.

#### 5. **ResultBuilder** (`services/result_builder.py`)
**LEGACY ADAPTER** - Maintains backward compatibility.

Delegates to GradingCalculationEngine where possible.

#### 6. **UniversityResultEngine** (`services/result_engine.py`)
**DEPRECATED** - Now delegates to GradingCalculationEngine.

Kept for backward compatibility only.

---

## Grading Formula

### Standard Weighted Average Formula

```
Final Score = (Quiz% × Quiz_Weight) + (Assignment% × Assignment_Weight) + (Exam% × Exam_Weight)
```

Where:
- `Quiz% = (Total Quiz Score / Total Quiz Max) × 100`
- `Assignment% = (Total Assignment Score / Total Assignment Max) × 100`
- `Exam% = (Total Exam Score / Total Exam Max) × 100`
- **Weights sum to 100%** (e.g., 10% + 30% + 60%)

### Step-by-Step Example

**Input Data:**
- Student: STD001
- Course: CSC101 (Introduction to Programming)
- Academic Year: 2024, Semester: 1

**Assessment Results:**
| Assessment | Score | Max | % |
|------------|-------|-----|-----|
| Quiz 1 | 4 | 5 | 80% |
| Quiz 2 | 15 | 20 | 75% |
| **Quiz Total** | **19** | **25** | **76%** |
| Assignment 1 | 18 | 20 | 90% |
| Assignment 2 | 19 | 20 | 95% |
| **Assignment Total** | **37** | **40** | **92.5%** |
| Final Exam | 42 | 50 | 84% |
| **Exam Total** | **42** | **50** | **84%** |

**Assessment Scheme:**
- Quiz Weight: 10%
- Assignment Weight: 30%
- Exam Weight: 60%
- **Total: 100%**

**Calculation:**

```
1. Convert to percentages (already done above)
   - Quiz: 76%
   - Assignment: 92.5%
   - Exam: 84%

2. Apply weights
   - Quiz_weighted = (76 ÷ 100) × 10 = 0.76 × 10 = 7.6
   - Assignment_weighted = (92.5 ÷ 100) × 30 = 0.925 × 30 = 27.75
   - Exam_weighted = (84 ÷ 100) × 60 = 0.84 × 60 = 50.4

3. Sum weighted scores
   - Final_Score = 7.6 + 27.75 + 50.4 = 85.75

4. Convert to letter grade (using GradingScale)
   - 85.75 falls in range 85-89
   - Grade: B+ (or A- depending on institution config)
   - Grade Point: 3.3 (or 3.7)
   - Pass/Fail: PASS
```

**Result:**
```
Final Score: 85.75
Grade Letter: B+
Grade Point: 3.3
Status: PASS
```

---

## Data Flow

### Single Course Grade Calculation

```
1. Request: calculate_course_grade(student_id, course_id, academic_year, semester)
   ↓
2. Fetch or create StudentCourseGrade record
   ↓
3. Fetch assessment scheme (CourseAssessmentScheme)
   ↓
4. Aggregate scores for each category:
   - _get_quiz_totals() → (19, 25)
   - _get_assignment_totals() → (37, 40)
   - _get_exam_totals() → (42, 50)
   ↓
5. Calculate percentages
   - Quiz: 76%, Assignment: 92.5%, Exam: 84%
   ↓
6. Apply weights
   - Quiz: 7.6, Assignment: 27.75, Exam: 50.4
   ↓
7. Calculate final score: 85.75
   ↓
8. Lookup letter grade using GradeService.get_grade(85.75)
   - Returns: GradingScale(grade_letter='B+', grade_point=3.3, ...)
   ↓
9. Update StudentCourseGrade record with all calculated values
   ↓
10. Commit to database
    ↓
11. Return StudentCourseGrade object
```

### Semester-Wide Finalization

```
1. Request: finalize_all_course_grades(academic_year, semester)
   ↓
2. Get all courses for semester
   ↓
3. For each course:
   - Get all student registrations
   - For each registration:
     - Call calculate_course_grade()
   ↓
4. Report: success_count, error_count, errors
```

### GPA Calculation

```
1. Fetch semester grades using get_student_grades_for_semester()
   ↓
2. For each grade:
   - Get grade_point (from GradingScale)
   - Sum all grade_points
   ↓
3. Simple GPA = Sum ÷ Course Count
   ↓
4. For weighted GPA:
   - Sum = Σ(grade_point × credit_hours)
   - Total = Σ(credit_hours)
   - Weighted GPA = Sum ÷ Total
   ↓
5. Return rounded to 2 decimals
```

---

## Database Schema

### StudentCourseGrade Model

Stores all calculated grade information:

| Field | Type | Purpose |
|-------|------|---------|
| student_id | Integer | Student reference |
| course_id | Integer | Course reference |
| academic_year | String | Academic year (e.g., "2024") |
| semester | String | Semester (e.g., "1") |
| **Raw Scores** | | |
| quiz_raw_score | Float | Sum of all quiz scores |
| quiz_max_score | Float | Sum of all quiz max scores |
| assignment_raw_score | Float | Sum of all assignment scores |
| assignment_max_score | Float | Sum of all assignment max scores |
| exam_raw_score | Float | Sum of all exam scores |
| exam_max_score | Float | Sum of all exam max scores |
| **Percentages** | | |
| quiz_percentage | Float | (quiz_raw / quiz_max) × 100 |
| assignment_percentage | Float | (assignment_raw / assignment_max) × 100 |
| exam_percentage | Float | (exam_raw / exam_max) × 100 |
| **Weighted Scores** | | |
| quiz_weighted_score | Float | (percentage ÷ 100) × weight |
| assignment_weighted_score | Float | (percentage ÷ 100) × weight |
| exam_weighted_score | Float | (percentage ÷ 100) × weight |
| **Final Results** | | |
| final_score | Float | Sum of weighted scores (0-100) |
| grade_letter | String | Letter grade (A, B+, B, C, etc.) |
| grade_point | Float | Numeric grade point (4.0 scale) |
| pass_fail | String | "PASS" or "FAIL" |
| **Status** | | |
| is_finalized | Boolean | Grade is finalized (ready for release) |
| is_released | Boolean | Grade is released to student |
| calculated_at | DateTime | When calculation occurred |

### GradingScale Model

Configurable grading boundaries:

| Field | Type | Purpose |
|-------|------|---------|
| grade_letter | String | Letter grade (e.g., "A", "B+") |
| min_score | Float | Minimum score for this grade |
| max_score | Float | Maximum score for this grade |
| grade_point | Float | Grade point value (4.0 scale) |
| pass_fail | String | "PASS" or "FAIL" |

**Example Entries:**

| Letter | Min | Max | Points | Status |
|--------|-----|-----|--------|--------|
| A | 90 | 100 | 4.0 | PASS |
| B+ | 85 | 89 | 3.3 | PASS |
| B | 80 | 84 | 3.0 | PASS |
| C | 70 | 79 | 2.0 | PASS |
| F | 0 | 69 | 0.0 | FAIL |

---

## Usage Examples

### Example 1: Calculate Single Course Grade

```python
from services.grading_calculation_engine import GradingCalculationEngine

# Calculate grade for one student in one course
grade = GradingCalculationEngine.calculate_course_grade(
    student_id=student.id,
    course_id=course.id,
    academic_year="2024",
    semester="1"
)

print(f"Score: {grade.final_score}")
print(f"Grade: {grade.grade_letter}")
print(f"Pass/Fail: {grade.pass_fail}")
```

### Example 2: Recalculate All Courses for Student

```python
# Recalculate grades for all courses in a semester
result = GradingCalculationEngine.recalculate_student_all_courses(
    student_id=student.id,
    academic_year="2024",
    semester="1"
)

print(f"Success: {result['success_count']}")
print(f"Errors: {result['error_count']}")
if result['errors']:
    for error in result['errors']:
        print(f"  {error['course_name']}: {error['error']}")
```

### Example 3: Get Semester Transcript

```python
# Get all grades for a semester
grades = GradingCalculationEngine.get_student_grades_for_semester(
    student_id=student.id,
    academic_year="2024",
    semester="1"
)

# Calculate GPA
gpa = GradingCalculationEngine.calculate_gpa(grades)
weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(grades)

print(f"Semester GPA: {gpa}")
print(f"Weighted GPA: {weighted_gpa}")

# Display grades
for grade in grades:
    course = grade.course
    print(f"{course.code}: {grade.final_score} ({grade.grade_letter})")
```

### Example 4: Full Academic Transcript

```python
# Get all grades across all semesters
all_grades = GradingCalculationEngine.get_student_all_grades(student_id=student.id)

# Calculate cumulative GPA
cumulative_gpa = GradingCalculationEngine.calculate_gpa(all_grades)
cumulative_weighted_gpa = GradingCalculationEngine.calculate_weighted_gpa(all_grades)

print(f"Cumulative GPA: {cumulative_gpa}")
print(f"Cumulative Weighted GPA: {cumulative_weighted_gpa}")
```

### Example 5: Finalize Semester Grades

```python
# Finalize all grades for a semester (batch operation)
result = GradingCalculationEngine.recalculate_all_students_all_courses(
    academic_year="2024",
    semester="1"
)

print(f"Total calculated: {result['total_calculated']}")
print(f"Total errors: {result['total_errors']}")
```

---

## Integration Points

### Admin Routes (`admin_grading_routes.py`)

Uses GradingCalculationEngine for:
- Manual recalculation of student grades
- Semester summary reports
- Grade status queries

```python
from services.grading_calculation_engine import GradingCalculationEngine

# Recalculate for a student
result = GradingCalculationEngine.recalculate_student_all_courses(
    student_id=user_id,
    academic_year=year,
    semester=semester
)
```

### Semester Grading Service (`services/semester_grading_service.py`)

Uses GradingCalculationEngine for:
- Course-level grade finalization
- Batch calculations
- Student processing

```python
# Inside finalize_semester_grades()
GradingCalculationEngine.calculate_course_grade(
    student.user_id,
    course_id,
    academic_year,
    semester
)
```

### Transcript Service (`services/transcript_service.py`)

Uses GradingCalculationEngine for:
- Fetching semester grades
- Calculating GPAs
- Building transcript data

```python
grades = GradingCalculationEngine.get_student_grades_for_semester(
    student_id, academic_year, semester
)
gpa = GradingCalculationEngine.calculate_gpa(grades)
```

### Result Builder (`services/result_builder.py`)

Uses GradingCalculationEngine for:
- Semester results
- Student summaries
- Class results

```python
grades = StudentCourseGrade.query.filter_by(
    student_id=student_id,
    academic_year=academic_year,
    semester=semester
).all()
```

---

## Migration from Old System

### Before (Scattered Implementation)

```python
# Old location 1: models.py
from models import GradingService
GradingService.calculate_final_grade(student_id, course_id, year, sem)

# Old location 2: result_engine.py
from services.result_engine import UniversityResultEngine
UniversityResultEngine.compute_course(student_id, course)
```

### After (Consolidated)

```python
# Single source of truth
from services.grading_calculation_engine import GradingCalculationEngine
GradingCalculationEngine.calculate_course_grade(
    student_id=student_id,
    course_id=course_id,
    academic_year=year,
    semester=semester
)
```

---

## Key Features

### 1. **Unified Formula**
All calculations use the same weighted average formula.

### 2. **Comprehensive Data Storage**
Every step of the calculation is stored:
- Raw scores
- Percentages
- Weighted scores
- Final results

### 3. **Flexible Configuration**
- Customizable assessment weights per course
- Customizable grading scales
- Support for different credit hour systems

### 4. **Error Handling**
- Graceful handling of missing data
- Detailed error reporting
- Batch operation error tracking

### 5. **Performance**
- Efficient database queries
- Support for bulk operations
- Transaction management

### 6. **Auditing**
- Timestamp tracking of calculations
- Status flags (finalized, released)
- Change history available

---

## Best Practices

### 1. Always Use GradingCalculationEngine
Don't access calculations through other classes. All grade calculations should go through this engine.

### 2. Configure Assessment Schemes
Ensure CourseAssessmentScheme is set for each course before calculating grades:
```python
scheme = CourseAssessmentScheme(
    course_id=course.id,
    quiz_weight=10,
    assignment_weight=30,
    exam_weight=60
)
db.session.add(scheme)
db.session.commit()
```

### 3. Handle Failures Gracefully
Always check return values and error lists:
```python
result = GradingCalculationEngine.recalculate_student_all_courses(...)
if result['error_count'] > 0:
    for error in result['errors']:
        logger.error(f"Failed to calculate: {error}")
```

### 4. Finalize Before Release
Never release grades until finalized:
```python
# Calculate grades
GradingCalculationEngine.recalculate_all_students_all_courses(year, sem)

# Then finalize
SemesterGradingService.finalize_all_course_grades(...)

# Then release
SemesterGradingService.release_semester_results(...)
```

### 5. Use Weighted GPA for Official Records
For official transcripts, always use credit-weighted GPA:
```python
official_gpa = GradingCalculationEngine.calculate_weighted_gpa(grades)
```

---

## Troubleshooting

### Issue: Calculation Returns None

**Causes:**
1. No CourseAssessmentScheme defined for the course
2. Student not found in database
3. No course found

**Solution:**
```python
# Check scheme exists
scheme = CourseAssessmentScheme.query.filter_by(course_id=course_id).first()
if not scheme:
    print("ERROR: Assessment scheme not configured for course")
```

### Issue: No Assessments Found

**Causes:**
1. Student hasn't submitted any work
2. No submissions recorded in database
3. Submissions have score = None

**Solution:**
```python
# System returns 0 for missing assessments
# This is correct behavior - no work = 0% = fails category
# Grade will reflect the weighted impact
```

### Issue: Final Score Doesn't Add Up to 100

**Causes:**
This is NORMAL. The final score is the sum of weighted scores, not a percentage.

**Example:**
- Quiz: 7.6 (not 76%)
- Assignment: 27.75 (not 92.5%)
- Exam: 50.4 (not 84%)
- **Total: 85.75** ✓ Correct!

If weights sum to 100%, max score is 100. If student gets 0%, score is 0.

---

## Testing

### Test Single Calculation

```python
def test_single_grade_calculation():
    from services.grading_calculation_engine import GradingCalculationEngine
    
    grade = GradingCalculationEngine.calculate_course_grade(
        student_id=1,
        course_id=1,
        academic_year="2024",
        semester="1"
    )
    
    assert grade is not None
    assert grade.final_score >= 0
    assert grade.final_score <= 100
    assert grade.grade_letter is not None
```

### Test Batch Calculation

```python
def test_batch_calculation():
    result = GradingCalculationEngine.recalculate_all_students_all_courses(
        academic_year="2024",
        semester="1"
    )
    
    assert result['total_calculated'] > 0
    assert result['total_errors'] == 0
```

### Test GPA Calculation

```python
def test_gpa_calculation():
    grades = GradingCalculationEngine.get_student_grades_for_semester(
        student_id=1,
        academic_year="2024",
        semester="1"
    )
    
    gpa = GradingCalculationEngine.calculate_gpa(grades)
    
    assert gpa >= 0.0
    assert gpa <= 4.0
```

---

## Summary

The LMS now has a **clean, consolidated grading system** with:

✅ **Single source of truth** - All calculations through GradingCalculationEngine
✅ **Standardized formula** - Consistent weighted average across all calculations
✅ **Complete data storage** - Raw scores, percentages, weighted scores, final results
✅ **Flexible configuration** - Customizable weights and grading scales
✅ **Error handling** - Graceful failure with detailed reporting
✅ **Performance optimized** - Efficient queries and batch operations
✅ **Well documented** - Clear examples and integration points
✅ **Backward compatible** - Old code still works with deprecation notices

### Main Entry Point

```python
from services.grading_calculation_engine import GradingCalculationEngine

# All grading calculations go through this engine
grade = GradingCalculationEngine.calculate_course_grade(...)
gpa = GradingCalculationEngine.calculate_gpa(...)
```

For questions or issues, refer to the inline documentation in `services/grading_calculation_engine.py` or this guide.
