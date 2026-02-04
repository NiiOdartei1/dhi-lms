# NOTIFICATION SYSTEM - QUICK REFERENCE

## 🚀 Fast Integration Cheat Sheet

### Step 1: Import Engine
```python
from utils.notification_engine import (
    notify_quiz_created,
    notify_assignment_created,
    notify_exam_scheduled,
    create_notification
)
```

### Step 2: After Creating Resource
```python
db.session.commit()
notify_quiz_created(quiz, send_email=True)
```

### Step 3: Done! ✅
- ✅ Notification created in DB
- ✅ Email sent to students
- ✅ In-app notification displayed
- ✅ Respects user preferences
- ✅ Shows in `/notifications/` page

---

## 📋 All Available Functions

### Quiz
```python
notify_quiz_created(quiz, send_email=True)
notify_quiz_reminder(quiz, hours_before=1, send_email=True)
notify_quiz_result_released(quiz, send_email=True)
```

### Assignment
```python
notify_assignment_created(assignment, send_email=True)
notify_assignment_reminder(assignment, days_before=3, send_email=True)
notify_assignment_graded(assignment_id, student_id, score, feedback, send_email=True)
```

### Exam
```python
notify_exam_scheduled(exam, send_email=True)
notify_exam_reminder(exam, hours_before=24, send_email=True)
```

### Grades
```python
notify_grade_released(course_id, programme, level, send_email=True)
```

### Fees
```python
notify_fee_assigned(fee_group, send_email=True)
notify_fee_payment_reminder(days_overdue=7, send_email=True)
notify_attendance_warning(student_id, attendance_percentage, send_email=True)
```

### Generic (for custom events)
```python
create_notification(
    notification_type='announcement',
    title='Title Here',
    message='Full message text',
    recipients=[user1, user2],  # List of User objects
    send_email_copy=True,
    priority='high'  # 'low', 'normal', or 'high'
)
```

---

## 📊 Routes for Users

| Route | Purpose |
|-------|---------|
| `/notifications/` | View all notifications |
| `/notifications/unread` | Unread only |
| `/notifications/<id>` | View single notification |
| `/notifications/preferences` | Configure preferences |
| `/notifications/stats` | Statistics dashboard |

---

## 🔌 API Endpoints (AJAX)

```javascript
// Get unread count
fetch('/notifications/api/count')
  .then(r => r.json())
  .then(data => console.log(data.count))

// Get recent 5 unread
fetch('/notifications/api/recent?limit=5')
  .then(r => r.json())
  .then(data => console.log(data.notifications))

// Filter by type
fetch('/notifications/api/filter?type=quiz_created&limit=10')
  .then(r => r.json())
  .then(data => console.log(data.notifications))
```

---

## 🎯 Common Patterns

### After Quiz Creation
```python
# In teacher_routes.py or admin_routes.py
db.session.commit()
try:
    notify_quiz_created(quiz, send_email=True)
except Exception as e:
    logger.warning(f"Notification failed: {e}")
flash("Quiz created and students notified.", "success")
```

### After Assignment Posting
```python
db.session.commit()
try:
    notify_assignment_created(assignment, send_email=True)
except Exception as e:
    logger.warning(f"Notification failed: {e}")
flash("Assignment posted and students notified.", "success")
```

### Bulk Announcement
```python
from utils.notification_engine import create_notification

students = User.query.join(StudentProfile).filter(
    StudentProfile.current_programme == 'CS',
    StudentProfile.programme_level == 100
).all()

create_notification(
    notification_type='announcement',
    title='Schedule Change',
    message='Class moved to Friday 2 PM',
    recipients=students,
    send_email_copy=True,
    priority='high'
)
```

---

## ⚙️ Notification Types

**Academic**: quiz_created, quiz_reminder, quiz_result, assignment_created, assignment_reminder, assignment_graded, exam_scheduled, exam_reminder, grade_released, course_registration

**Admin**: fee_assigned, fee_payment_reminder, fee_overdue, attendance_marked, attendance_warning

**System**: announcement, event_reminder, promotion, message_received

---

## 🔧 Setup Checklist

- [ ] Run `flask db migrate && flask db upgrade`
- [ ] Register blueprint in `app.py` (✅ already done)
- [ ] Configure email in `config.py` (SMTP settings)
- [ ] Add bell icon to base template (optional)
- [ ] Test with first quiz/assignment
- [ ] Verify email delivery
- [ ] Check `/notifications/stats` dashboard

---

## 📧 Email Configuration

In `config.py`:
```python
MAIL_SERVER = 'smtp.gmail.com'  # or your provider
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@example.com'
MAIL_PASSWORD = 'your-app-password'  # Use app password, not regular password
MAIL_DEFAULT_SENDER = 'noreply@lms.edu'
```

---

## 🧪 Quick Test

```bash
flask shell

# Create test notification
from utils.notification_engine import create_notification
from models import User

user = User.query.first()
notif = create_notification(
    notification_type='test',
    title='Test Notification',
    message='This is a test',
    recipients=[user],
    priority='high'
)
print(f"Notification created: {notif.id}")

# Check if it was created
from models import NotificationRecipient
NotificationRecipient.query.filter_by(user_id=user.user_id).count()
# Should return 1 or more
```

---

## 📱 Frontend Integration

### Add bell icon to navbar
```html
<a href="{{ url_for('notifications.list_notifications') }}" class="btn btn-outline-secondary position-relative">
    <i class="fas fa-bell"></i>
    <span class="position-absolute badge bg-danger" id="notif-count">0</span>
</a>
```

### Update count automatically
```javascript
setInterval(() => {
    fetch('/notifications/api/count')
        .then(r => r.json())
        .then(d => {
            const el = document.getElementById('notif-count');
            el.textContent = d.count;
            el.style.display = d.count > 0 ? 'block' : 'none';
        });
}, 30000);  // Every 30 seconds
```

---

## 🚨 Error Handling

Always wrap notifications in try/except:

```python
try:
    notify_quiz_created(quiz, send_email=True)
except Exception as e:
    # Log but don't block request
    logger.warning(f"Notification error: {e}")
    # User still gets flash message
```

This ensures:
- Notification failures don't crash the app
- User still sees success message
- Errors are logged for debugging
- Resource is still created even if notification fails

---

## 📞 Priority Levels

- **high**: Exams, deadlines, payments (email + in-app)
- **normal**: Assignments, quizzes, materials (email + in-app)
- **low**: General updates (in-app only)

---

## 🔐 Privacy & Preferences

Users can:
- ✅ Enable/disable email notifications
- ✅ Set quiet hours (no emails 10 PM - 8 AM)
- ✅ Choose notification types to receive
- ✅ Mute all notifications temporarily
- ✅ Delete individual notifications
- ✅ View notification history

All changes are instant and stored in `NotificationPreference` table.

---

## 📊 Analytics

Visit `/notifications/stats` to see:
- Unread count
- Today's notifications
- This week's notifications
- Breakdown by type
- Visual charts

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Notifications not appearing | Check user preferences at `/notifications/preferences` |
| Email not sending | Verify SMTP in config.py, check logs |
| Database error | Run `flask db upgrade` |
| Badge not updating | Check `/notifications/api/count` endpoint |
| Notification not created | Check exception in logs, ensure DB committed |

---

## 📚 Full Documentation

See:
- `NOTIFICATION_SYSTEM_COMPLETE.md` - Full system docs
- `NOTIFICATION_INTEGRATION_GUIDE.md` - Integration patterns

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: 2 Feb 2026
