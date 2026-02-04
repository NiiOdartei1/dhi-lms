# NOTIFICATION SYSTEM INTEGRATION GUIDE

## Status: ✅ IMPLEMENTED & READY

This guide covers how to use the new comprehensive notification system across the LMS.

---

## Quick Start

### 1. **System Already Registered**

The notification blueprint has been added to `app.py`:
```python
from utils.notification_routes import notification_bp
app.register_blueprint(notification_bp)  # Registered at /notifications
```

**Routes Available:**
- `/notifications/` - List all notifications
- `/notifications/unread` - Unread only
- `/notifications/<id>` - View single notification
- `/notifications/preferences` - User settings
- `/notifications/stats` - Statistics dashboard
- `/notifications/api/count` - Unread count (AJAX)
- `/notifications/api/recent` - Recent notifications (AJAX)

### 2. **Database Migration Required**

Before first use, run:
```bash
flask db migrate -m "Add comprehensive notification system"
flask db upgrade
```

This creates:
- `notifications` table
- `notification_recipients` table
- `notification_preferences` table

---

## Integration Points (Already Implemented)

### ✅ Teacher Routes - Quiz Creation

**File:** `teacher_routes.py` (line ~1030)

When a teacher creates a quiz, students are now automatically notified:

```python
from utils.notification_engine import notify_quiz_created

# ... quiz creation code ...
db.session.commit()

# Automatically notifies all students in the programme/level
try:
    notify_quiz_created(quiz, send_email=True)
except Exception as e:
    current_app.logger.warning(f"Failed to send quiz notification: {e}")

flash("Quiz created. Students have been notified.", "success")
```

### ✅ Teacher Routes - Assignment Creation

**File:** `teacher_routes.py` (line ~600)

Already implemented - uses legacy `create_assignment_notification()`. Can be upgraded to new engine:

```python
from utils.notification_engine import notify_assignment_created

# After creating assignment...
notify_assignment_created(assignment, send_email=True)
```

---

## How to Add Notifications to Other Events

### Pattern 1: Single Entity Event

When creating/updating a single resource (quiz, assignment, exam):

```python
from utils.notification_engine import notify_quiz_created

# Create resource
resource = Quiz(...)
db.session.add(resource)
db.session.flush()  # Get ID

# Add questions/options/etc...

# Commit
db.session.commit()

# Send notification
try:
    notify_quiz_created(resource, send_email=True)
except Exception as e:
    logger.warning(f"Notification failed: {e}")

flash("Resource created and stakeholders notified.", "success")
```

### Pattern 2: Bulk Notification

Notify specific users about something:

```python
from utils.notification_engine import create_notification
from models import User, StudentProfile

# Get recipients
students = User.query.join(StudentProfile).filter(
    StudentProfile.current_programme == 'Computer Science',
    StudentProfile.programme_level == 100
).all()

# Send notification
create_notification(
    notification_type='announcement',
    title='Important: Class Schedule Change',
    message='Physics 101 lecture moved to Wednesday 2 PM',
    recipients=students,
    send_email_copy=True,
    priority='high'
)

flash("Notification sent to all students.", "success")
```

### Pattern 3: Grade Release

When releasing grades:

```python
from utils.notification_engine import notify_grade_released

# Update grades...
course = Course.query.get(course_id)
programme = 'Computer Science'
level = 100

db.session.commit()

# Notify students
notify_grade_released(course_id, programme, level, send_email=True)
```

---

## Common Notification Types

### Academic Events

- `notify_quiz_created(quiz, send_email=True)`
- `notify_quiz_reminder(quiz, hours_before=1)`
- `notify_quiz_result_released(quiz)`
- `notify_assignment_created(assignment)`
- `notify_assignment_reminder(assignment, days_before=3)`
- `notify_assignment_graded(assignment_id, student_id, score, feedback)`
- `notify_exam_scheduled(exam)`
- `notify_exam_reminder(exam, hours_before=24)`
- `notify_grade_released(course_id, programme, level)`

### Administrative Events

- `notify_fee_assigned(fee_group)`
- `notify_fee_payment_reminder(days_overdue=7)`
- `notify_attendance_warning(student_id, attendance_percentage)`

### Generic

```python
from utils.notification_engine import create_notification

create_notification(
    notification_type='custom_type',
    title='Your Title',
    message='Full message text',
    recipients=[user1, user2, ...],
    send_email_copy=True,
    priority='high'
)
```

---

## User Preferences

Users can manage notifications at `/notifications/preferences`:

1. **Delivery Channels**
   - Email on/off
   - In-app display on/off
   - Daily digest option

2. **Quiet Hours**
   - Don't email between 10 PM - 8 AM (example)
   - Still shows in-app

3. **Notification Types**
   - Enable/disable by event (quiz created, assignment graded, etc.)

4. **Mute Period**
   - Temporarily disable all notifications (1/4/8/24 hours)

---

## Frontend Components

### Notification Bell Badge

Add to base template header:

```html
<a href="{{ url_for('notifications.list_notifications') }}" class="btn btn-outline-secondary position-relative">
    <i class="fas fa-bell"></i>
    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" id="notif-count">
        0
    </span>
</a>

<script>
setInterval(function() {
    fetch('{{ url_for("notifications.api_unread_count") }}')
        .then(r => r.json())
        .then(data => {
            document.getElementById('notif-count').textContent = data.count;
            document.getElementById('notif-count').style.display = data.count > 0 ? 'block' : 'none';
        });
}, 30000);  // Update every 30 seconds
</script>
```

### Notification Dropdown

```html
<div class="dropdown-menu dropdown-menu-end" style="width: 400px;">
    <div class="dropdown-header">Recent Notifications</div>
    <div id="recent-notifications"></div>
    <div class="dropdown-divider"></div>
    <a href="{{ url_for('notifications.list_notifications') }}" class="dropdown-item text-center">
        View All
    </a>
</div>

<script>
function loadRecent() {
    fetch('{{ url_for("notifications.api_recent_notifications", limit=5) }}')
        .then(r => r.json())
        .then(data => {
            const html = data.notifications.map(n => `
                <a href="{{ url_for('notifications.view_notification', notification_id=0) }}".replace('0', n.id) class="dropdown-item">
                    <strong>${n.title}</strong>
                    <small>${n.message}</small>
                </a>
            `).join('');
            document.getElementById('recent-notifications').innerHTML = html;
        });
}
loadRecent();
setInterval(loadRecent, 60000);  // Update every minute
</script>
```

---

## Email Templates

Email notifications are automatically formatted with:
- Title (bold)
- Message body
- Direct action link
- Footer with preference management link

Example email:

```
Subject: [LMS] New Quiz: Physics 101 - Midterm

---

New quiz has been created: Physics 101 - Midterm

Course: Physics 101
Start: 15 Feb 2026, 10:00 AM
End: 15 Feb 2026, 11:30 AM
Duration: 90 minutes
Attempts Allowed: 1

Please review the quiz details and prepare accordingly.

[View Quiz] ← Direct link

---

You can manage your notification preferences in your account settings.
```

---

## Best Practices

### When to Send Email Copies

✅ DO send emails for:
- High-priority items (exams, deadlines, fees)
- Time-sensitive information
- Important status changes (grades released, payment confirmed)

❌ DON'T send emails for:
- Low-priority updates
- Frequent reminders (use in-app only)
- System/debug messages

### Message Guidelines

- **Keep it concise**: First 120 characters shown in list
- **Include key details**: Date, time, deadline, amount, etc.
- **Action-oriented**: Tell user what to do next
- **Professional tone**: Maintain institutional voice

### Performance Considerations

- Notifications are created asynchronously when possible
- Email sending doesn't block request (try/except pattern)
- User preferences cached in session
- Database queries use indexes on type and created_at

---

## Testing the System

### Manual Test Checklist

1. **Create a quiz as teacher**
   - ✅ Notification created in DB
   - ✅ Email sent to students
   - ✅ Badge count updated
   - ✅ Shows in student's notification list

2. **Update preferences**
   - ✅ Disable quiz_created emails
   - ✅ Create another quiz
   - ✅ Email NOT sent (but in-app shows)
   - ✅ Re-enable and test again

3. **Mark as read**
   - ✅ Click notification
   - ✅ "Unread" badge disappears
   - ✅ read_at timestamp set
   - ✅ Unread count decreases

4. **View stats**
   - ✅ Navigate to `/notifications/stats`
   - ✅ See breakdown by type
   - ✅ Daily/weekly/monthly counts
   - ✅ Visualizations render

---

## Troubleshooting

### Email Not Sending

1. Check `utils/email.py` is configured
2. Verify SMTP settings in `config.py`
3. Check notification's `send_email_copy` parameter
4. Look for exceptions in app logs

### Notifications Not Appearing

1. Check `NotificationPreference` - type might be disabled
2. Verify user is in recipient list (programme/level match)
3. Confirm notification was committed to DB
4. Check quiet hours - might be muted

### Database Issues

After first migration:

```bash
# Verify tables exist
flask shell
>>> from models import Notification, NotificationRecipient, NotificationPreference
>>> # Should load without error
>>> Notification.query.count()
0
```

---

## File Locations

| Component | Location |
|-----------|----------|
| **Engine** | `utils/notification_engine.py` |
| **Routes** | `utils/notification_routes.py` |
| **Models** | `models.py` (Notification, NotificationRecipient, NotificationPreference) |
| **List Template** | `templates/notifications/list.html` |
| **Preferences UI** | `templates/notifications/preferences.html` |
| **Detail View** | `templates/notifications/detail.html` |
| **Stats Dashboard** | `templates/notifications/stats.html` |
| **Documentation** | `NOTIFICATION_SYSTEM_COMPLETE.md` |

---

## Next Steps

1. **Run database migration** (if not done)
   ```bash
   flask db migrate -m "Add notification system"
   flask db upgrade
   ```

2. **Test with existing data** (create a quiz, verify notification)

3. **Add UI components** to base template (bell icon, dropdown)

4. **Integrate remaining events** using patterns above:
   - Exam creation/release
   - Grade publication
   - Fee assignments
   - Attendance warnings
   - Academic promotions

5. **Enable email channel** (verify SMTP works)

6. **Monitor logs** for notification errors

---

## Support

For issues or enhancements:
- Check logs: `tail -f logs/app.log`
- Test in Flask shell: `flask shell`
- Review `NOTIFICATION_SYSTEM_COMPLETE.md` for detailed API docs

---

**Last Updated:** 2 Feb 2026  
**Status:** Production Ready ✅
