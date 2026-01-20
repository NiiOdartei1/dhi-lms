import os


class Config:
    # ------------------------------------------------------
    # CORE
    # ------------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///lms.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB uploads

    # ------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------
    VOUCHER_DEFAULT_AMOUNT = 220.0

    # ------------------------------------------------------
    # FILE UPLOADS
    # ------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'assignments')
    MATERIALS_FOLDER = os.path.join(os.getcwd(), 'uploads', 'materials')
    PAYMENT_PROOF_FOLDER = os.path.join('static', 'uploads', 'payments')
    RECEIPT_FOLDER = os.path.join('static', 'uploads', 'receipts')
    PROFILE_PICS_FOLDER = os.path.join('static', 'uploads', 'profile_pictures')

    # ------------------------------------------------------
    # EMAIL (Flask-Mailman – GMAIL)
    # ------------------------------------------------------
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.environ.get(
        'MAIL_USERNAME',
        'lampteyjoseph860@gmail.com'
    )

    MAIL_PASSWORD = os.environ.get(
        'MAIL_PASSWORD'
        # ⚠️ MUST be Gmail App Password, not normal Gmail password
    )

    MAIL_DEFAULT_SENDER = (
        'Admissions Office',
        MAIL_USERNAME
    )

    # ------------------------------------------------------
    # ZOOM (OPTIONAL)
    # ------------------------------------------------------
    ZOOM_ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
    ZOOM_CLIENT_ID = os.environ.get('ZOOM_CLIENT_ID')
    ZOOM_CLIENT_SECRET = os.environ.get('ZOOM_CLIENT_SECRET')
