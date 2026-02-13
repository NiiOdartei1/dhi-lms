from flask import current_app, url_for
import resend
import logging

# Initialize Resend client
resend.api_key = current_app.config.get('RESEND_API_KEY', 're_a8DrgsUK_LCTo9FaBkR8J4XUvRauYS2gB')


def _get_sender():
    """
    Safely get default sender from config.
    """
    return current_app.config.get(
        'MAIL_DEFAULT_SENDER',
        'onboarding@resend.dev'  # Use Resend default domain
    )


def _get_applicant_name(applicant):
    """
    Safely resolve applicant name.
    Falls back to email if personal info is not yet filled.
    """
    try:
        if applicant.application and applicant.application.surname:
            return f"{applicant.application.surname} {applicant.application.other_names or ''}".strip()
    except Exception:
        pass

    return applicant.email


def send_email(to_email, subject, body):
    """
    Core email sender using Resend API.
    Cloud-friendly and reliable.
    """
    try:
        params = {
            "from": _get_sender(),
            "to": [to_email],
            "subject": subject,
            "html": body.replace('\n', '<br>')  # Convert to HTML
        }
        
        result = resend.Emails.send(params)
        logging.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logging.error(f"Email sending failed to {to_email}: {str(e)}")
        return False


# ------------------------------------------------------------------
# PASSWORD RESET EMAIL
# ------------------------------------------------------------------

def send_password_reset_email(applicant, token):
    reset_url = url_for(
        'vclass.reset_password',
        token=token,
        _external=True
    )

    name = _get_applicant_name(applicant)

    subject = "Password Reset – Online Admissions Portal"

    body = f"""
Dear {name},

A request has been received to reset the password for your Online Admissions Portal account.

To proceed, please click the secure link below to set a new password.
This link will expire in 1 hour.

{reset_url}

If you did not initiate this request, please ignore this email.
No changes will be made to your account.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)


# ------------------------------------------------------------------
# TEMPORARY PASSWORD EMAIL (ADMIN RESET)
# ------------------------------------------------------------------

def send_temporary_password_email(applicant, temp_password):
    name = _get_applicant_name(applicant)

    subject = "Temporary Password – Online Admissions Portal"

    body = f"""
Dear {name},

Your account password has been reset by the Admissions Office.

Your temporary password is:

{temp_password}

Please log in immediately and change your password to keep your account secure.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)


# ------------------------------------------------------------------
# EMAIL VERIFICATION (KNUST-STYLE)
# ------------------------------------------------------------------

def send_email_verification(applicant, verification_code):
    name = _get_applicant_name(applicant)

    subject = "Verify Your Email Address – Online Admissions"

    body = f"""
Dear {name},

Thank you for creating an account on the Online Admissions Portal.

To complete your registration, please verify your email address
using the verification code below:

VERIFICATION CODE: {verification_code}

This code will expire shortly.
Do not share this code with anyone.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)

# ------------------------------------------------------------------
# APPLICATION COMPLETION EMAIL
# ------------------------------------------------------------------

def send_application_completed_email(applicant):
    name = _get_applicant_name(applicant)

    subject = "Admission Application Successfully Submitted"

    body = f"""
Dear {name},

Your admission application has been successfully submitted.

Our admissions team will review your application.
If additional information is required, you will be contacted via this email address.

You may log into the Online Admissions Portal at any time to track your application status.

Thank you for choosing our institution.

Admissions Office
Online Admissions Portal
"""

    return send_email(applicant.email, subject, body)

def send_approval_credentials_email(applicant, username, student_id, temp_password, fees_info=None):
    name = _get_applicant_name(applicant)

    subject = "Your Student Account is Ready – Online Admissions Portal"

    fees_section = ""
    if fees_info:
        fees_section = f"""
    <hr>
    <h3>Programme Fees</h3>
    <p><b>Programme:</b> {fees_info.get('programme_name', 'N/A')}</p>
    <table style="border-collapse: collapse; width: 100%; margin-top: 10px;">
        <tr style="background-color: #f2f2f2;">
            <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Fee Component</th>
            <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Amount (GHS)</th>
        </tr>
"""
        total_fees = 0
        for fee in fees_info.get('fees', []):
            amount = float(fee.get('amount', 0))
            total_fees += amount
            fees_section += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px;">{fee.get('description', 'Fee')}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{amount:,.2f}</td>
        </tr>
"""
        fees_section += f"""
        <tr style="background-color: #f2f2f2; font-weight: bold;">
            <td style="border: 1px solid #ddd; padding: 8px;">Total</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_fees:,.2f}</td>
        </tr>
    </table>
    <p style="margin-top: 10px;">You will be prompted to pay these fees upon login to your student portal.</p>
        """

    body = f"""
    <p>Dear {name},</p>

    <p>Congratulations! Your admission application has been approved.</p>

    <p>Your student account has been created with the following credentials:</p>

    <ul>
        <li><b>Username:</b> {username}</li>
        <li><b>Student ID:</b> {student_id}</li>
        <li><b>Temporary Password:</b> {temp_password}</li>
    </ul>

    <p>
        Please log in immediately at
        <a href="{url_for('admissions.login', _external=True)}">Online Admissions Portal</a>
        and change your password.
    </p>

    {fees_section}

    <p>Admissions Office<br>Online Admissions Portal</p>
    """

    try:
        params = {
            "from": _get_sender(),
            "to": [applicant.email],
            "subject": subject,
            "html": body
        }
        
        result = resend.Emails.send(params)
        logging.info(f"Approval credentials email sent successfully to {applicant.email}")
        return True
    except Exception as e:
        logging.error(
            f"Failed to send approval credentials email to {applicant.email}: {str(e)}"
        )
        return False


# ------------------------------------------------------------------
# TEACHER REGISTRATION CREDENTIALS EMAIL
# ------------------------------------------------------------------

def send_teacher_registration_email(email, first_name, last_name, username, user_id, employee_id, temp_password):
    """
    Send registration credentials to newly created teacher
    """
    name = f"{first_name} {last_name}"
    
    subject = "Your Teacher Account is Ready – DHI LMS"
    
    body = f"""
Dear {name},

Your teacher account has been successfully created at DHI College of Health & Education.

Your login credentials are:
- Username: {username}
- User ID: {user_id}
- Employee ID: {employee_id}
- Temporary Password: {temp_password}

Please log in immediately at the Teacher Portal and change your password to keep your account secure.

Login URL: {url_for('teacher.teacher_login', _external=True)}

Important:
- Keep your credentials confidential
- Change your password on first login
- Contact IT support if you have any issues

Best regards,
DHI College of Health & Education
IT Department
"""

    return send_email(email, subject, body)


# ------------------------------------------------------------------
# ADMIN REGISTRATION CREDENTIALS EMAIL
# ------------------------------------------------------------------

def send_admin_registration_email(email, first_name, last_name, username, admin_id, role, temp_password):
    """
    Send registration credentials to newly created admin
    """
    name = f"{first_name} {last_name}"
    
    role_display = {
        'finance_admin': 'Finance Admin',
        'academic_admin': 'Academic Admin', 
        'admissions_admin': 'Admissions Admin',
        'superadmin': 'Super Admin'
    }.get(role, role.replace('_', ' ').title())
    
    subject = f"Your {role_display} Account is Ready – DHI LMS"
    
    body = f"""
Dear {name},

Your {role_display} account has been successfully created at DHI College of Health & Education.

Your login credentials are:
- Username: {username}
- Admin ID: {admin_id}
- Role: {role_display}
- Temporary Password: {temp_password}

Please log in immediately at the Admin Portal and change your password to keep your account secure.

Login URL: {url_for('admin.admin_login', _external=True)}

Important:
- Keep your credentials confidential
- Change your password on first login
- Contact IT support if you have any issues
- Your role permissions have been configured accordingly

Best regards,
DHI College of Health & Education
System Administration
"""

    return send_email(email, subject, body)


def send_continuing_student_credentials_email(email, first_name, last_name, username, student_id, index_number, temp_password, programme, level):
    """
    Send registration credentials to newly created continuing student
    """
    name = f"{first_name} {last_name}"
    
    subject = "Your Student Account is Ready – DHI LMS Portal"
    
    body = f"""
Dear {name},

Your continuing student account has been successfully created at DHI College of Health & Education.

Your login credentials are:
- Username: {username}
- Student ID: {student_id}
- Index Number: {index_number}
- Temporary Password: {temp_password}
- Programme: {programme}
- Level: {level}

Please log in immediately at the Student Portal and change your password to keep your account secure.

Login URL: {url_for('vclass.vclass_login', _external=True)}

Important:
- Keep your credentials confidential
- Change your password on first login
- Complete your profile information
- Contact IT support if you have any issues
- Your academic records have been updated for the new level

Best regards,
DHI College of Health & Education
Student Administration
"""

    return send_email(email, subject, body)
