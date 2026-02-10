# ===== GTK RUNTIME FIX FOR WEASYPRINT (Windows) =====
import os
import sys

if sys.platform == "win32":
    gtk_path = r"C:\Program Files\GTK3-Runtime Win64\bin"
    if os.path.exists(gtk_path):
        os.add_dll_directory(gtk_path)
        os.environ["PATH"] = gtk_path + ";" + os.environ["PATH"]
# ================================================

# app.py - My LMS — Clean Production Version

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_from_directory, current_app
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

# ===== Flask App =====
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions ONCE
db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)
socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
csrf = CSRFProtect(app)

# Import all models to ensure they're registered
from models import Admin, StudentProfile, User

# ===== Logging =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Auto-initialize database for Render (runs on every startup in production)
if os.environ.get('FLASK_ENV') == 'production':
    with app.app_context():
        try:
            # Create all tables (handle existing tables gracefully)
            db.create_all()
            logger.info("✓ Database tables created/verified on Render")
            
            # Ensure notification tables exist specifically
            from models import Notification, NotificationRecipient, NotificationPreference
            Notification.__table__.create(db.engine, checkfirst=True)
            NotificationRecipient.__table__.create(db.engine, checkfirst=True)
            NotificationPreference.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ Notification tables verified on Render")
            
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

# ===== Configuration =====
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
    SOCKETIO_ASYNC_MODE = "eventlet"
except ImportError:
    SOCKETIO_ASYNC_MODE = "threading"

# ===== Login Manager =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.admin_login'

@login_manager.user_loader
def load_user(user_id):
    """
    Load user by ID for Flask-Login
    Handles both Admin and User types with proper ID format:
    - Admin: "admin:public_id" 
    - User: numeric ID
    """
    try:
        if user_id.startswith('admin:'):
            # Extract public_id from "admin:public_id" format
            public_id = user_id.split(':', 1)[1]
            from models import Admin
            return Admin.query.filter_by(public_id=public_id).first()
        else:
            # Regular User (numeric ID)
            from models import User
            return User.query.get(int(user_id))
    except:
        return None

# ===== CSRF Protection =====
@app.before_request
def make_csrf_token_available():
    """Make CSRF token available in all templates"""
    generate_csrf()

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors gracefully"""
    flash('Security token expired. Please try again.', 'error')
    return redirect(url_for('home'))

# ===== Template Filters =====
def _start_year_filter(value):
    """Extract start year from academic year string"""
    if isinstance(value, str) and '/' in value:
        return value.split('/')[0]
    return value

app.jinja_env.filters['start_year'] = _start_year_filter

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

@app.route('/health')
def health():
    """Lightweight health check for load balancers and Render."""
    try:
        return jsonify(status='ok', service='lms', now=datetime.utcnow().isoformat()), 200
    except Exception:
        return jsonify(status='error'), 500

@app.route('/init-db')
def init_database_route():
    """Manual database initialization for Render deployment"""
    if os.environ.get('FLASK_ENV') != 'production':
        return jsonify(error='This route is only available in production'), 403
    
    try:
        # Import all models to ensure they're registered
        from models import User, Admin, StudentProfile, StudentFeeTransaction, StudentFeeBalance
        
        # Create all tables in correct dependency order
        try:
            # Create User table first (Admin depends on it)
            User.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ User table created/verified")
            
            # Create Admin table (depends on User)
            Admin.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ Admin table created/verified")
            
            # Create other core tables
            StudentProfile.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ StudentProfile table created/verified")
            
            StudentFeeTransaction.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ StudentFeeTransaction table created/verified")
            
            StudentFeeBalance.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ StudentFeeBalance table created/verified")
            
            # Create notification tables
            from models import Notification, NotificationRecipient, NotificationPreference
            Notification.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ Notification table created/verified")
            
            NotificationRecipient.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ NotificationRecipient table created/verified")
            
            NotificationPreference.__table__.create(db.engine, checkfirst=True)
            logger.info("✓ NotificationPreference table created/verified")
            
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Some database tables already exist")
            else:
                logger.error(f"Table creation error: {e}")
        
        # Create SuperAdmin if missing
        try:
            if not Admin.query.filter_by(username='SuperAdmin').first():
                admin = Admin(username='SuperAdmin', admin_id='ADM001', email='admin@lms.com')
                admin.set_password('Password123')
                Admin.apply_superadmin_preset(admin)
                db.session.add(admin)
                db.session.commit()
                logger.info("✓ SuperAdmin created")
                return jsonify(status='success', message='Database initialized and SuperAdmin created')
            else:
                return jsonify(status='success', message='Database already initialized and SuperAdmin exists')
        except Exception as e:
            logger.error(f"SuperAdmin creation error: {e}")
            return jsonify(status='error', message=f'SuperAdmin creation failed: {str(e)}'), 500
            
    except Exception as e:
        logger.error(f"Database init error: {e}")
        return jsonify(status='error', message=str(e)), 500

# ===== Blueprints =====
# Import and register all blueprints
from admin_routes import admin_bp
from student_routes import student_bp
from teacher_routes import teacher_bp
from exam_routes import exam_bp
from vclass_routes import vclass_bp
from chat_routes import chat_bp
from finance_routes import finance_bp
from student_results_routes import results_bp
from student_transcript_routes import create_student_transcript_blueprint
from admissions.routes import admissions_bp

app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(exam_bp, url_prefix='/exam')
app.register_blueprint(vclass_bp, url_prefix='/vclass')
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(finance_bp, url_prefix='/finance')
app.register_blueprint(results_bp, url_prefix='/student-results')
app.register_blueprint(create_student_transcript_blueprint())
app.register_blueprint(admissions_bp, url_prefix='/admissions')

logger.info("✓ All blueprints registered")

# ===== Static Files =====
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files with proper headers"""
    try:
        return send_from_directory('static', filename)
    except Exception as e:
        logger.error(f"Static file error: {e}")
        abort(404)

# ===== Error Handlers =====
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

# ===== Debug Routes =====
@app.route('/debug/routes')
def debug_routes():
    """List all registered routes (debug only)"""
    if not app.debug:
        abort(404)
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    
    return "<pre>" + "\n".join([str(r) for r in sorted(routes, key=lambda x: x['path'])]) + "</pre>"

# ===== Run =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("Starting LMS app")
    logger.info("Environment: %s", "PRODUCTION" if IS_PRODUCTION else "LOCAL")
    logger.info("SocketIO mode: %s", SOCKETIO_ASYNC_MODE)

    socketio.run(
        app,
        host="0.0.0.0" if IS_PRODUCTION else "127.0.0.1",
        port=port,
        debug=not IS_PRODUCTION,
        allow_unsafe_werkzeug=not IS_PRODUCTION
    )
