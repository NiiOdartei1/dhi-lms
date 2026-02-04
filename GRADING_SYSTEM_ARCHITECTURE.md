# Grading System Architecture

## File Structure

```
services/
├── grading_calculation_engine.py   ⭐ PRIMARY ENGINE
│   ├── GradingCalculationEngine (main calculation class)
│   └── GradeService (lookup service moved from models.py)
│
├── grade_service.py                (enhanced, comprehensive)
│   ├── get_grade(percent)
│   ├── get_all_grades()
│   └── get_grade_by_letter(letter)
│
├── semester_grading_service.py     (uses GradingCalculationEngine)
│   └── SemesterGradingService
│
├── transcript_service.py           (uses GradingCalculationEngine)
│   └── TranscriptService
│
├── result_builder.py               (uses GradingCalculationEngine)
│   └── ResultBuilder
│
├── result_engine.py                (DEPRECATED - delegates to above)
│   └── UniversityResultEngine (backward compatibility)
│
└── assessment_engine.py            (simple utility)
    └── AssessmentEngine
```

## Calculation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ calculate_course_grade(student_id, course_id, year, semester)   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Get/Create StudentCourseGrade record                         │
│     └─→ Check if exists, create if not                          │
│                                                                  │
│  2. Get Assessment Scheme for course                            │
│     └─→ Quiz Weight, Assignment Weight, Exam Weight             │
│                                                                  │
│  3. Aggregate Scores                                            │
│     ├─→ _get_quiz_totals() → (19, 25)                           │
│     ├─→ _get_assignment_totals() → (37, 40)                     │
│     └─→ _get_exam_totals() → (42, 50)                           │
│                                                                  │
│  4. Calculate Percentages                                       │
│     ├─→ Quiz%: 76%                                              │
│     ├─→ Assignment%: 92.5%                                      │
│     └─→ Exam%: 84%                                              │
│                                                                  │
│  5. Apply Weights                                               │
│     ├─→ (76/100) × 10 = 7.6                                     │
│     ├─→ (92.5/100) × 30 = 27.75                                 │
│     └─→ (84/100) × 60 = 50.4                                    │
│                                                                  │
│  6. Calculate Final Score                                       │
│     └─→ 7.6 + 27.75 + 50.4 = 85.75                              │
│                                                                  │
│  7. Lookup Letter Grade                                         │
│     └─→ GradeService.get_grade(85.75) → B+                      │
│                                                                  │
│  8. Update StudentCourseGrade record                            │
│     └─→ Store all calculated values                             │
│                                                                  │
│  9. Commit to database                                          │
│     └─→ Transaction complete                                    │
│                                                                  │
│  10. Return StudentCourseGrade object                           │
│      └─→ Contains all calculation details                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### StudentCourseGrade (Output)
```
┌─────────────────────────────────┐
│  StudentCourseGrade             │
├─────────────────────────────────┤
│ student_id                      │ ← Key
│ course_id                       │ ← Key
│ academic_year                   │ ← Key
│ semester                        │ ← Key
├─────────────────────────────────┤
│ QUIZ DATA:                      │
│ ├─ quiz_raw_score: 19           │
│ ├─ quiz_max_score: 25           │
│ ├─ quiz_percentage: 76.0        │
│ └─ quiz_weighted_score: 7.6     │
├─────────────────────────────────┤
│ ASSIGNMENT DATA:                │
│ ├─ assignment_raw_score: 37     │
│ ├─ assignment_max_score: 40     │
│ ├─ assignment_percentage: 92.5  │
│ └─ assignment_weighted: 27.75   │
├─────────────────────────────────┤
│ EXAM DATA:                      │
│ ├─ exam_raw_score: 42           │
│ ├─ exam_max_score: 50           │
│ ├─ exam_percentage: 84.0        │
│ └─ exam_weighted_score: 50.4    │
├─────────────────────────────────┤
│ FINAL RESULTS:                  │
│ ├─ final_score: 85.75           │
│ ├─ grade_letter: 'B+'           │
│ ├─ grade_point: 3.3             │
│ └─ pass_fail: 'PASS'            │
├─────────────────────────────────┤
│ STATUS:                         │
│ ├─ is_finalized: False          │
│ ├─ is_released: False           │
│ └─ calculated_at: DateTime      │
└─────────────────────────────────┘
```

### GradingScale (Configuration)
```
┌──────────────────────────────────┐
│  GradingScale                    │
├──────────────────────────────────┤
│ grade_letter: 'B+'               │
│ min_score: 85                    │
│ max_score: 89                    │
│ grade_point: 3.3                 │
│ pass_fail: 'PASS'                │
└──────────────────────────────────┘

┌────────────────────────────────────────┐
│ Complete Grading Scale                 │
├────────────────────────────────────────┤
│ A    │ 90-100  │ 4.0  │ PASS           │
│ A-   │ 85-89   │ 3.7  │ PASS           │
│ B+   │ 83-84   │ 3.3  │ PASS           │
│ B    │ 80-82   │ 3.0  │ PASS           │
│ B-   │ 78-79   │ 2.7  │ PASS           │
│ C+   │ 76-77   │ 2.3  │ PASS           │
│ C    │ 70-75   │ 2.0  │ PASS           │
│ C-   │ 68-69   │ 1.7  │ PASS           │
│ D+   │ 66-67   │ 1.3  │ PASS           │
│ D    │ 60-65   │ 1.0  │ PASS           │
│ F    │ 0-59    │ 0.0  │ FAIL           │
└────────────────────────────────────────┘
```

## GPA Calculation

### Simple GPA (Unweighted)
```
GPA = (Sum of grade_points) / (Number of courses)

Example:
  Course 1: B+ (3.3)
  Course 2: A- (3.7)
  Course 3: B  (3.0)
  
  GPA = (3.3 + 3.7 + 3.0) / 3 = 10.0 / 3 = 3.33
```

### Weighted GPA (Credit Hours)
```
GPA = (Sum of (grade_point × credit_hours)) / (Sum of credit_hours)

Example:
  Course 1: B+ (3.3) × 3 credits = 9.9
  Course 2: A- (3.7) × 4 credits = 14.8
  Course 3: B  (3.0) × 3 credits = 9.0
  
  Weighted GPA = (9.9 + 14.8 + 9.0) / (3 + 4 + 3)
               = 33.7 / 10
               = 3.37
```

## Class Hierarchy

```
GradingCalculationEngine
├── Public Methods (Main API)
│   ├── calculate_course_grade()
│   ├── recalculate_student_all_courses()
│   ├── recalculate_all_students_all_courses()
│   ├── get_student_grades_for_semester()
│   ├── get_student_all_grades()
│   ├── calculate_gpa()
│   └── calculate_weighted_gpa()
│
└── Private Methods (Internal)
    ├── _get_quiz_totals()
    ├── _get_assignment_totals()
    └── _get_exam_totals()

GradeService
├── get_grade(percent)
├── get_all_grades()
└── get_grade_by_letter(letter)
```

## Integration Points

```
admin_grading_routes.py
    │
    └─→ GradingCalculationEngine.recalculate_student_all_courses()
        GradingCalculationEngine.get_student_grades_for_semester()

admin_routes.py
    │
    └─→ SemesterGradingService.finalize_semester_grades()
        └─→ GradingCalculationEngine.calculate_course_grade()

semester_grading_service.py
    │
    └─→ GradingCalculationEngine.calculate_course_grade()
        GradingCalculationEngine.recalculate_all_students_all_courses()

transcript_service.py
    │
    └─→ GradingCalculationEngine.get_student_grades_for_semester()
        GradingCalculationEngine.get_student_all_grades()
        GradingCalculationEngine.calculate_gpa()
        GradingCalculationEngine.calculate_weighted_gpa()

result_builder.py
    │
    ├─→ GradingCalculationEngine methods
    └─→ StudentCourseGrade.query (direct access)

student_transcript_routes.py
    │
    └─→ TranscriptService
        └─→ GradingCalculationEngine
```

## Workflow Sequences

### Workflow 1: Single Grade Calculation
```
Teacher enters grade for student submission
  ↓
Trigger: AdminGradingRoutes.recalculate_student
  ↓
Call: GradingCalculationEngine.calculate_course_grade()
  ↓
Engine: Aggregates → Calculates → Stores
  ↓
Result: StudentCourseGrade updated in database
  ↓
Display: Grade summary to admin
```

### Workflow 2: Semester Finalization
```
Admin: Click "Finalize Semester"
  ↓
Trigger: admin_grading_routes.finalize_all_course_grades()
  ↓
Call: SemesterGradingService.finalize_all_course_grades()
  ↓
Loop: For each course in semester
  ├─→ Get all student registrations
  ├─→ For each student:
  │   Call: GradingCalculationEngine.calculate_course_grade()
  │   ├─→ Fetch assessments
  │   ├─→ Calculate scores
  │   ├─→ Apply weights
  │   ├─→ Determine grade
  │   └─→ Store to database
  └─→ Mark course as finalized
  ↓
Result: All grades calculated and finalized
  ↓
Summary: Success count, error count, error details
```

### Workflow 3: Grade Release to Students
```
Admin: Click "Release Results"
  ↓
Trigger: admin_routes.release_semester_results()
  ↓
Call: SemesterGradingService.release_semester_results()
  ↓
Action: Mark all grades as is_released = True
  ↓
Result: Grades visible to students
  ↓
Students can: View grades, download transcript
```

### Workflow 4: Student Views Transcript
```
Student: Click "View Transcript"
  ↓
Trigger: student_transcript_routes.semester_transcript()
  ↓
Call: TranscriptService.generate_semester_transcript()
  ↓
Engine:
  ├─→ GradingCalculationEngine.get_student_grades_for_semester()
  ├─→ GradingCalculationEngine.calculate_gpa()
  ├─→ GradingCalculationEngine.calculate_weighted_gpa()
  └─→ Format for display
  ↓
Display: Transcript with grades and GPA
```

## Error Handling

```
Error Scenarios:
├─ No Assessment Scheme Configured
│  └─→ Returns None, student registration fails
│
├─ Student Not Found
│  └─→ Caught in try/except, added to error list
│
├─ Course Not Found
│  └─→ Caught in try/except, added to error list
│
├─ No Submissions for Category
│  └─→ Score = 0, percentage = 0%, weighted = 0
│
├─ Database Transaction Failure
│  └─→ Rollback triggered, error logged
│
└─ Calculation Overflow/Underflow
   └─→ Values rounded to 2 decimals, bounded 0-100
```

## Performance Considerations

```
Optimization Strategies:
├─ Query Efficiency
│  └─→ Use .join() for submission queries
│
├─ Aggregation
│  └─→ Sum scores at query level when possible
│
├─ Batch Operations
│  ├─→ Process semester at once (not individually)
│  └─→ Commit transactions in batches
│
├─ Caching
│  └─→ GradingScale loaded once per process
│
└─ Lazy Loading
   └─→ Only fetch related objects when needed
```

## Key Improvements Over Previous System

| Aspect | Before | After |
|--------|--------|-------|
| **Location** | Scattered (models.py, result_engine.py) | Single engine (grading_calculation_engine.py) |
| **Formula Consistency** | Multiple implementations | One unified formula |
| **Data Storage** | Partial/inconsistent | Complete (all intermediate values stored) |
| **Error Handling** | Basic | Comprehensive with error lists |
| **Documentation** | Minimal | Extensive with examples |
| **Batch Operations** | Limited | Full support |
| **Testing** | Difficult | Straightforward |
| **Maintainability** | Low | High |
| **Extensibility** | Low | High |
| **Performance** | Variable | Optimized |

## Quick Reference

### Calculate Single Grade
```python
from services.grading_calculation_engine import GradingCalculationEngine

grade = GradingCalculationEngine.calculate_course_grade(
    student_id=1, course_id=5, academic_year="2024", semester="1"
)
```

### Get Semester Transcript
```python
grades = GradingCalculationEngine.get_student_grades_for_semester(
    student_id=1, academic_year="2024", semester="1"
)
gpa = GradingCalculationEngine.calculate_gpa(grades)
```

### Get Full Transcript
```python
all_grades = GradingCalculationEngine.get_student_all_grades(student_id=1)
cumulative_gpa = GradingCalculationEngine.calculate_gpa(all_grades)
```

### Convert Score to Grade
```python
from services.grade_service import GradeService

grade_obj = GradeService.get_grade(85.75)  # Returns B+ entry
```

---

**Last Updated:** February 1, 2026
**Status:** Production Ready ✓
