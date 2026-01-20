# utils/notifications.py
from datetime import datetime
import json
from models import SchoolClass, db, Notification, NotificationRecipient, User, StudentProfile
from flask_login import current_user

def create_assignment_notification(assignment):
    """
    Create a notification for a new assignment and send to all students in the assigned class.
    The notification message includes date + time.
    """
    # format due date with time
    due_str = assignment.due_date.strftime('%d %B %Y, %I:%M %p') if assignment.due_date else 'No due date'

    notice = Notification(
        type='assignment',
        title=f"New Assignment: {assignment.title}",
        message=(
            f"A new assignment has been posted for {assignment.course_name}.\n\n"
            f"Due Date: {due_str}\n\n"
            f"Please check the Assignments section."
        ),
        created_at=datetime.utcnow(),
        related_type='assignment',
        related_id=assignment.id,
        # store sender as current_user.user_id when available (user or teacher)
        sender_id=getattr(current_user, 'user_id', None) or getattr(current_user, 'admin_id', None)
    )

    db.session.add(notice)
    db.session.flush()  # get notice.id

    # Find all students in the assigned class (use student.user_id)
    students = User.query.join(StudentProfile).filter(
        StudentProfile.current_class == assignment.assigned_class
    ).all()

    recipients = [
        NotificationRecipient(notification_id=notice.id, user_id=s.user_id)
        for s in students if s.user_id
    ]
    if recipients:
        db.session.add_all(recipients)

    db.session.commit()
    return notice

def create_fee_notification(fee_group, sender=None):
    if sender is None:
        sender = current_user

    sender_id = getattr(sender, 'user_id', None) or getattr(sender, 'admin_id', None)
    sender_type = 'admin' if getattr(sender, 'is_admin', False) else 'user'

    # Create message
    try:
        items = json.loads(fee_group.items) if isinstance(fee_group.items, str) else fee_group.items
    except Exception:
        items = []

    items_text = "\n".join([f"• {i.get('description', '')}: {i.get('amount',0)} GHS" for i in items])
    message = (
        f"New fee assigned for {fee_group.class_level}\n"
        f"Year: {fee_group.academic_year}, Semester: {fee_group.semester}\n"
        f"Total: {fee_group.amount} GHS\n\nBreakdown:\n{items_text}"
    )

    # Notification
    notification = Notification(
        type='fee',
        title=f"Fee Assigned: {fee_group.description}",
        message=message,
        sender_id=sender_id,
        sender_type=sender_type,
        related_type='fee',
        related_id=fee_group.id,
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.flush()  # get notification.id

    # Get all students in the class
    school_class = SchoolClass.query.filter_by(name=fee_group.class_level).first()
    if not school_class:
        school_class = SchoolClass.query.filter(SchoolClass.name.ilike(f"%{fee_group.class_level}%")).first()
    if not school_class:
        db.session.rollback()
        raise ValueError(f"No class found for '{fee_group.class_level}'")

    students = User.query.filter_by(class_id=school_class.id, role='student').all()

    recipient_user_ids = set()
    for student in students:
        recipient_user_ids.add(student.user_id)
        # Add parents if available via StudentProfile
        sp = getattr(student, 'student_profile', None)
        if sp and hasattr(sp, 'parents'):
            parents = sp.parents.all() if hasattr(sp.parents, 'all') else sp.parents
            for p in parents:
                if hasattr(p, 'user_id'):
                    recipient_user_ids.add(p.user_id)

    if not recipient_user_ids:
        db.session.rollback()
        raise ValueError("No recipients found!")

    # Create NotificationRecipient
    recipients = [NotificationRecipient(notification_id=notification.id, user_id=uid, is_read=False) for uid in recipient_user_ids]
    db.session.add_all(recipients)
    db.session.commit()

    return notification

def create_missed_call_notification(caller_name, target_user_id, conversation_id):
    """
    Create a notification for a missed call when the target user is not online.
    """
    notice = Notification(
        type='call',
        title="Missed Call",
        message=f"You missed a call from {caller_name}.",
        created_at=datetime.utcnow(),
        related_type='conversation',
        related_id=conversation_id,
        sender_id=getattr(current_user, 'user_id', None) or getattr(current_user, 'admin_id', None)
    )

    db.session.add(notice)
    db.session.flush()  # get notice.id

    # Send to the target user
    recipient = NotificationRecipient(notification_id=notice.id, user_id=target_user_id)
    db.session.add(recipient)

    db.session.commit()
    return notice
