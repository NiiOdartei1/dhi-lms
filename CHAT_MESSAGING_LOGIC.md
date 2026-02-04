# Chat Messaging Logic - Programme/Level Requirements

## Overview
The messaging system now correctly handles programme and level requirements based on recipient type. Admins and teachers are not bound by programmes, so messaging them doesn't require programme selection.

## Messaging Rules

### 1. **Admin to Admin**
- **Programme/Level Required**: ❌ NO
- **Steps**: 
  1. Select role (Admin)
  2. Select Admin from list
- **Reason**: Admins operate across all programmes and aren't bound by programme structure

### 2. **Admin to Teacher**
- **Programme/Level Required**: ❌ NO
- **Steps**:
  1. Select role (Teacher)
  2. Select Teacher from list
- **Reason**: Teachers are assigned to departments, not specific programmes. They teach courses across multiple programmes

### 3. **Admin to Student**
- **Programme/Level Required**: ✅ YES
- **Steps**:
  1. Select role (Student)
  2. Select Programme
  3. Select Level
  4. Select Student from filtered list
- **Reason**: Students are enrolled in specific programmes and levels, enabling precise targeting

### 4. **Student/Teacher to Admin**
- **Programme/Level Required**: ❌ NO
- **Steps**:
  1. Select role (Admin)
  2. Select Admin from list
- **Reason**: Admins operate across all programmes

## Backend Implementation

### Chat Routes (`/chat/users`)
The `/chat/users` endpoint handles filtering:

```
GET /chat/users?role={role}&programme={name}&level={number}
```

**Response Logic:**
- **role=admin**: Returns all admins (no programme/level filtering)
- **role=teacher**: Returns all teachers (no programme/level filtering)
- **role=student**: 
  - If `programme` AND `level` provided: Returns students from that programme/level
  - If only `programme`: Returns all students in that programme
  - If neither: Returns all students (not recommended for large user bases)

### Send DM Route (`/chat/send_dm`)
Updated to accept all valid recipient roles:
- ✅ student
- ✅ teacher
- ✅ superadmin, finance_admin, academic_admin, admissions_admin

## Database Models

### User Binding
- **StudentProfile**: Bound to `current_programme` and `programme_level`
- **TeacherProfile**: Bound to `department` (not programme-specific)
- **Admin**: No programme binding (operates globally)

## Frontend Implementation

### Role Selection Flow (chat.html)

1. **Teacher Button Clicked**
   - Show Step 2: Teacher List
   - Load all teachers
   - No programme/level fields shown

2. **Admin Button Clicked**
   - Show Step 2: Admin List
   - Load all admins
   - No programme/level fields shown

3. **Student Button Clicked**
   - Show Step 2: Programme Selector
   - Show Step 3: Level Selector (after programme selected)
   - Show Step 4: Student List (after level selected)

### JavaScript Functions
- `loadUsers(role, programme, level)`: Fetches users with optional filters
- `loadProgrammes(targetRole)`: Loads available programmes
- `loadLevels()`: Loads levels for selected programme
- `handleProgrammeChange()`: Manages programme selection flow
- `handleLevelChange()`: Manages level selection flow

## Validation Rules

1. **Cannot message yourself** ✓
2. **Admin role validation** ✓ (updated to support all admin types)
3. **User existence check** ✓
4. **Access control** ✓ (uses `@login_required` and `is_user_or_admin()`)

## Example Workflows

### Workflow 1: Admin messaging a student from Business programme, Level 200
1. Click FAB button → "New Chat"
2. Select "Student" role
3. Select "Business" programme
4. Select "Level 200"
5. Select student from filtered list
6. Start conversation

### Workflow 2: Admin messaging another admin
1. Click FAB button → "New Chat"
2. Select "Admin" role
3. Select admin from list
4. Start conversation (no programme filtering)

### Workflow 3: Admin messaging teacher
1. Click FAB button → "New Chat"
2. Select "Teacher" role
3. Select teacher from list
4. Start conversation (no programme filtering)

## Changes Made

### Files Modified
1. **chat_routes.py** (line 291-350):
   - Updated `send_dm()` to accept admin roles
   - Changed error message from "Can only message teachers and students" to "Invalid recipient role"

2. **templates/chat.html** (lines 340-430):
   - Separated messaging flows for admins and teachers (no programme filtering)
   - Updated step labels to reflect conditional steps
   - Fixed event listener management to prevent duplicate handlers
   - Simplified teacher/admin selection flow

### Backward Compatibility
- ✅ Existing student-to-student messaging unchanged
- ✅ All existing conversations still work
- ✅ No database schema changes required
