import os


class Config:
    # ------------------------------------------------------
    # CORE
    # ------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # DATABASE (Render-safe)
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        SQLALCHEMY_DATABASE_URI = db_url.replace(
            "postgres://", "postgresql://"
        )
        # Add SSL configuration for production databases
        if "sslmode=" not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI += "?sslmode=require"
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///instance/lms.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Aggressive connection pool settings for production (prevent memory issues)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 3,         # Further reduced from 5
        "pool_recycle": 120,    # Further reduced from 180 (2 minutes)
        "pool_pre_ping": True,
        "max_overflow": 5,       # Further reduced from 10
        "pool_timeout": 30,     # Add timeout for getting connections
        "pool_reset_on_return": "commit"  # Reset connections on return
    }

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB uploads

    # Aggressive memory management settings
    MEMORY_LIMIT_MB = 256  # Reduced from 512 - more aggressive threshold
    
    # More frequent cleanup settings
    CLEANUP_INTERVAL = 180  # Reduced from 300 (3 minutes)

    # ------------------------------------------------------
    # BASE DIRECTORY
    # ------------------------------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # ------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------
    VOUCHER_DEFAULT_AMOUNT = 220.0

    # ------------------------------------------------------
    # FILE UPLOADS
    # ------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "assignments")
    MATERIALS_FOLDER = os.path.join(BASE_DIR, "uploads", "materials")

    PAYMENT_PROOF_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "payments"
    )
    RECEIPT_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "receipts"
    )
    PROFILE_PICS_FOLDER = os.path.join(
        BASE_DIR, "static", "uploads", "profile_pictures"
    )

    # ------------------------------------------------------
    # EMAIL CONFIGURATION (BREVO HTTPS API)
    # ------------------------------------------------------
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
    BREVO_DEFAULT_SENDER = os.environ.get("BREVO_DEFAULT_SENDER", "noreply@dhi-online.onrender.com")

    # ------------------------------------------------------
    # ZOOM (OPTIONAL)
    # ------------------------------------------------------
    ZOOM_ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID")
    ZOOM_CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID")
    ZOOM_CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET")
