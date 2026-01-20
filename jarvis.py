# jarvis.py (SocketIO-ready)
from datetime import datetime, timedelta
import json
import statistics
from flask import Blueprint, render_template, current_app
from utils.extensions import db, socketio
from flask_socketio import emit
from models import User, Quiz, QuizAttempt, AttendanceRecord, Notification, NotificationRecipient

jarvis_bp = Blueprint("jarvis", __name__, template_folder="templates/jarvis")

# ------------------------------
# Helper Functions
# ------------------------------
def student_engagement(days=7):
    alerts = []
    students = User.query.filter_by(role="student").all()
    for s in students:
        quizzes = Quiz.query.filter(Quiz.start_datetime >= datetime.utcnow() - timedelta(days=days)).all()
        total = len(quizzes) or 1
        attempts = QuizAttempt.query.filter(QuizAttempt.student_id == s.id,
                                            QuizAttempt.quiz_id.in_([q.id for q in quizzes])).count()
        ratio = attempts / total
        if ratio < 0.6:
            alerts.append((s, ratio))
    return alerts

def quiz_variance(days=30):
    flagged = []
    quizzes = Quiz.query.filter(Quiz.start_datetime >= datetime.utcnow() - timedelta(days=days)).all()
    for q in quizzes:
        scores = [a.score for a in q.submissions if a.score is not None]
        if len(scores) < 2:
            continue
        try:
            stdev = statistics.pstdev(scores)
        except Exception:
            stdev = 0.0
        if stdev > 0.3:
            flagged.append({"quiz": q, "stdev": stdev})
    return flagged

def attendance_variance(days=30):
    records = AttendanceRecord.query.filter(AttendanceRecord.date >= datetime.utcnow() - timedelta(days=days)).all()
    per_student = {}
    total_counts = {}
    for r in records:
        sid = r.student_id
        per_student.setdefault(sid, 0)
        total_counts.setdefault(sid, 0)
        if r.is_present:
            per_student[sid] += 1
        total_counts[sid] += 1
    rates = []
    rate_map = {}
    for sid, total in total_counts.items():
        rate = per_student.get(sid, 0) / total if total else 0
        rates.append(rate)
        rate_map[sid] = rate
    stdev = statistics.stdev(rates) if len(rates) > 1 else 0.0
    return stdev, rate_map

def send_notifications_for_alerts(alerts, ntype="jarvis"):
    for student, ratio in alerts:
        msg = f"Your engagement in the past week is {ratio:.0%}, below recommended threshold."
        n = Notification(type=ntype, title="Low Engagement Alert", message=msg,
                         sender_type="admin", sender_id="jarvis")
        db.session.add(n)
        db.session.flush()
        nr = NotificationRecipient(notification_id=n.id, user_id=student.user_id)
        db.session.add(nr)
    db.session.commit()

# ------------------------------
# Dashboard Route
# ------------------------------
@jarvis_bp.route("/jarvis-dashboard")
def dashboard():
    return render_template("jarvis/dashboard_socketio.html")

# ------------------------------
# SocketIO Events
# ------------------------------
@socketio.on("request_metrics")
def handle_request_metrics():
    # Compute metrics
    engagement_alerts = student_engagement()
    high_variance = quiz_variance()
    att_stdev, att_rates = attendance_variance()

    # Send to client
    emit("update_metrics", {
        "engagement_alerts": [
            {"name": s.full_name, "ratio": round(r*100)} for s, r in engagement_alerts
        ],
        "high_variance": [
            {"quiz": q["quiz"].title, "stdev": round(q["stdev"], 2)} for q in high_variance
        ],
        "attendance_stdev": round(att_stdev, 2),
        "attendance_rates": {sid: round(r*100, 2) for sid, r in att_rates.items()},
        "timestamp": datetime.utcnow().isoformat()
    })

# ------------------------------
# Auto-run on startup
# ------------------------------
def run_on_startup(app):
    with app.app_context():
        # Optional precompute to warm up metrics
        student_engagement()
        quiz_variance()
        attendance_variance()
        app.logger.info("✓ Jarvis SocketIO ready")
