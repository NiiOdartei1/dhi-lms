# ===== GTK RUNTIME FIX FOR WEASYPRINT (Windows) =====
import os
import sys

if sys.platform == "win32":
    gtk_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.exists(gtk_path):
        os.add_dll_directory(gtk_path)
        os.environ["PATH"] = gtk_path + ";" + os.environ["PATH"]
# ================================================

# app.py - My LMS — Render-Optimized with Local Support

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_from_directory, current_app
from sqlalchemy import Table
from werkzeug.utils import secure_filename

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ===== Extensions & Config =====
from flask_login import LoginManager, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from utils.extensions import db, mail, socketio
from config import Config

# Import all models to ensure they're registered with SQLAlchemy
from models import Admin, StudentProfile, User

# ===== Logging =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== Flask App =====
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions with app
db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

# Auto-initialize database for Render (runs on every startup in production)
if os.environ.get('FLASK_ENV') == 'production':
    with app.app_context():
        try:
            # Create all tables (handle existing tables gracefully)
            db.create_all()
            logger.info("✓ Database tables created/verified on Render")
            
            # Create SuperAdmin if missing
            if not Admin.query.filter_by(username='SuperAdmin').first():
                admin = Admin(username='SuperAdmin', admin_id='ADM001')
                admin.set_password('Password123')
                Admin.apply_superadmin_preset(admin)
                db.session.add(admin)
                db.session.commit()
                logger.info("✓ SuperAdmin created on Render")
            else:
                logger.info("✓ SuperAdmin already exists on Render")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Database tables already exist on Render")
            else:
                logger.error(f"Database init error: {e}")

IS_PRODUCTION = bool(
    app.config.get("IS_PRODUCTION")
    or os.environ.get("IS_PRODUCTION") in ("1", "true", "True")
    or app.config.get("ENV", "").lower() == "production"
)

# Ensure eventlet is imported only if installed. Fallback to threading if not.
try:
    import eventlet  # pip install eventlet
    # Only monkey-patch if we intend to use eventlet (avoid unnecessary patching)
    if IS_PRODUCTION:
        eventlet.monkey_patch()
    SOCKETIO_ASYNC_MODE = "eventlet" if IS_PRODUCTION else "threading"
except Exception:
    # eventlet not available — use threading which is safe for development
    SOCKETIO_ASYNC_MODE = "threading"

# ===== Paths =====
# Leave SQLALCHEMY_DATABASE_URI to be provided by `Config` (or DATABASE_URL).
app.config.setdefault('UPLOAD_FOLDER', os.path.join(app.instance_path, 'uploads'))
app.config.setdefault('MATERIALS_FOLDER', os.path.join(app.instance_path, 'materials'))
app.config.setdefault('PAYMENT_PROOF_FOLDER', os.path.join(app.instance_path, 'payment_proofs'))
app.config.setdefault('RECEIPT_FOLDER', os.path.join(app.instance_path, 'receipts'))
app.config.setdefault('PROFILE_PICS_FOLDER', os.path.join(app.instance_path, 'profile_pics'))

folders = [
    app.instance_path,
    os.path.join(app.instance_path, 'uploads'),
    os.path.join(app.instance_path, 'materials'),
    os.path.join(app.instance_path, 'payment_proofs'),
    os.path.join(app.instance_path, 'receipts'),
    os.path.join(app.instance_path, 'profile_pics'),
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

logger.info("App instance path: %s", app.instance_path)

# ===== Extensions =====
db.init_app(app)
mail.init_app(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# ===== SocketIO =====
logger.info("SocketIO async_mode=%s", SOCKETIO_ASYNC_MODE)
socketio.init_app(app, async_mode=SOCKETIO_ASYNC_MODE, manage_session=False)

# ===== Login Manager =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'student.student_login'

@login_manager.user_loader
def load_user(user_id):
    try:
        from models import Admin, User
        if user_id.startswith("admin:"):
            uid = user_id.split(":", 1)[1]
            return Admin.query.filter_by(public_id=uid).first()
        elif user_id.startswith("user:"):
            uid = user_id.split(":", 1)[1]
            return User.query.filter_by(public_id=uid).first()
    except Exception as e:
        logger.exception("user_loader error: %s", e)
    return None

# ===== Context processors =====
@app.context_processor
def inject_current_app():
    return dict(current_app=current_app)

@app.context_processor
def inject_csrf():
    return dict(csrf_token=generate_csrf)

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_active_assessment_period():
    def get_active_period():
        try:
            from models import TeacherAssessmentPeriod
            return TeacherAssessmentPeriod.query.filter_by(is_active=True).first()
        except Exception as e:
            logger.warning("Error fetching active assessment period: %s", e)
            return None
    return {'active_assessment_period': get_active_period}

# ===== Custom Jinja2 Filters =====
@app.template_filter('floatformat')
def floatformat(value, decimals=2):
    """Format a float to specified decimal places (Django-like floatformat)"""
    try:
        return f"{float(value):.{int(decimals)}f}"
    except (ValueError, TypeError):
        return value

# ===== Error Handlers =====
@app.errorhandler(CSRFError)
def handle_csrf(e):
    return jsonify({'error': 'CSRF token missing or invalid', 'reason': e.description}), 400

@app.after_request
def set_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers.setdefault('Cache-Control', 'no-store')
    return response


# Import blueprints
from admin_routes import admin_bp
from teacher_routes import teacher_bp
from student_routes import student_bp
from utils.auth_routes import auth_bp
from exam_routes import exam_bp
from vclass_routes import vclass_bp
from chat_routes import chat_bp
from admissions.routes import admissions_bp
from utils.notification_routes import notification_bp
from student_transcript_routes import create_student_transcript_blueprint
from admin_grading_routes import grading_bp
from student_results_routes import results_bp
from finance_routes import finance_bp

student_transcript_bp = create_student_transcript_blueprint()

# Register blueprints
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(teacher_bp, url_prefix="/teacher")
app.register_blueprint(student_bp, url_prefix="/student")
app.register_blueprint(auth_bp)
app.register_blueprint(exam_bp, url_prefix="/exam")
app.register_blueprint(vclass_bp, url_prefix="/vclass")
app.register_blueprint(chat_bp, url_prefix="/chat")
app.register_blueprint(admissions_bp, url_prefix="/admissions")
app.register_blueprint(notification_bp)  # Registered at /notifications
app.register_blueprint(student_transcript_bp)
app.register_blueprint(grading_bp)
app.register_blueprint(results_bp)
app.register_blueprint(finance_bp, url_prefix='/admin/finance')

logger.info("✓ All blueprints registered")

# -------------------------
# Jinja filters
# -------------------------
def _start_year_filter(val):
    try:
        if not val:
            return ''
        s = str(val)
        return s.split('/')[0].split('-')[0]
    except Exception:
        return val

app.jinja_env.filters['start_year'] = _start_year_filter

# ===== One-Time Initialization Function =====
def one_time_init():
    logger.info("===== STARTING APP INITIALIZATION =====")

    db.create_all()
    logger.info("✓ Database tables created/verified")

    # 2️⃣ Create SuperAdmin if missing
    if not Admin.query.filter_by(username='SuperAdmin').first():
        admin = Admin(username='SuperAdmin', admin_id='ADM001')
        admin.set_password('Password123')
        Admin.apply_superadmin_preset(admin)

        db.session.add(admin)
        db.session.commit()
        logger.info("✓ SuperAdmin created")
    else:
        logger.info("✓ SuperAdmin already exists")

    logger.info("=" * 70)
    logger.info("✓✓✓ APP INITIALIZATION COMPLETE - READY TO SERVE REQUESTS ✓✓✓")
    logger.info("=" * 70)

# ===== Routes =====
@app.route('/')
def home():
    try:
        return render_template('home.html')
    except Exception as e:
        logger.exception("Template error on /: %s", e)
        return f"<h1>Template rendering error: {e}</h1>", 500

@app.route('/portal')
def select_portal():
    return render_template('portal_selection.html')

@app.route('/portal/<portal>')
def redirect_to_portal(portal):
    mapping = {
        'exams': 'exam.exam_login',
        'teachers': 'teacher.teacher_login',
        'students': 'student.student_login',
        'vclass': 'vclass.vclass_login'
    }
    key = portal.lower()
    if key not in mapping:
        abort(404)
    return redirect(url_for(mapping[key]))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('select_portal'))

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    filename = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/routes')
def list_routes():
    from urllib.parse import unquote
    lines = [f"{rule.endpoint:30s} → {unquote(str(rule))}" for rule in app.url_map.iter_rules()]
    return "<pre>" + "\n".join(sorted(lines)) + "</pre>"

@app.route('/health')
def health():
    """Lightweight health check for load balancers and Render."""
    try:
        return jsonify(status='ok', service='lms', now=datetime.utcnow().isoformat()), 200
    except Exception:
        return jsonify(status='error'), 500

# ===== Run =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting LMS app")
    logger.info("Environment: %s", "PRODUCTION" if IS_PRODUCTION else "LOCAL")
    logger.info("SocketIO mode: %s", SOCKETIO_ASYNC_MODE)

    with app.app_context():
        one_time_init()

    socketio.run(
        app,
        host="0.0.0.0" if IS_PRODUCTION else "127.0.0.1",
        port=port,
        debug=not IS_PRODUCTION,
        allow_unsafe_werkzeug=not IS_PRODUCTION
    )
