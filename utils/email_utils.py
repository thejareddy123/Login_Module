"""
utils/email_utils.py
--------------------
Functions for sending emails from the application.

We keep all email-related code here so:
  - The rest of the app doesn't need to know SMTP details
  - Email templates are easy to find and edit
  - We can change email providers without touching other files

A fresher tip:
  Each function builds an email for one specific purpose.
  Just call the function with the required info — it handles the rest.
"""

from flask_mail import Message


def send_email(mail, to_address, subject, body):
    """
    Base function to send a plain-text email.

    Parameters:
        mail        : The Flask-Mail extension instance
        to_address  : The recipient's email address (string)
        subject     : The email subject line (string)
        body        : The plain-text email body (string)

    If sending fails (e.g. wrong SMTP credentials), we catch the
    error and print it instead of crashing the whole app.
    """
    try:
        # Create a Message object with the subject and recipient
        msg = Message(
            subject    = subject,
            recipients = [to_address],  # Must be a list
            body       = body
        )
        mail.send(msg)
    except Exception as error:
        # In production you would log this to a file
        print(f"[EMAIL ERROR] Could not send email to {to_address}: {error}")


# ─────────────────────────────────────────────────────────────
# SPECIFIC EMAIL FUNCTIONS
# Each function calls send_email() with the right content.
# ─────────────────────────────────────────────────────────────

def send_otp_email(mail, to_address, otp, app_name):
    """
    Sends the registration OTP to the user's email.

    Parameters:
        mail        : Flask-Mail instance
        to_address  : User's email address
        otp         : The 6-digit OTP string
        app_name    : Application name (shown in email)
    """
    subject = "Your Verification Code"

    body = (
        f"Hello,\n\n"
        f"Your verification code is: {otp}\n\n"
        f"This code will expire in 5 minutes.\n\n"
        f"Do not share this code with anyone.\n\n"
        f"Thank you,\n"
        f"{app_name} Team"
    )

    send_email(mail, to_address, subject, body)


def send_registration_success_email(mail, to_address, first_name, app_name):
    """
    Sends a welcome email after the user successfully registers.

    Parameters:
        mail        : Flask-Mail instance
        to_address  : User's email address
        first_name  : User's first name (for personalisation)
        app_name    : Application name
    """
    subject = f"Welcome to {app_name} – Registration Successful"

    body = (
        f"Hello {first_name},\n\n"
        f"Your account has been successfully created.\n\n"
        f"You can now log in using your registered email address.\n\n"
        f"If you did not create this account, please contact support immediately.\n\n"
        f"Thank you,\n"
        f"{app_name} Team"
    )

    send_email(mail, to_address, subject, body)


def send_password_reset_otp_email(mail, to_address, otp, app_name):
    """
    Sends a password reset OTP to the user's email.
    """
    subject = "Password Reset Verification Code"

    body = (
        f"Your password reset code is: {otp}\n\n"
        f"This code will expire in 5 minutes.\n\n"
        f"If you did not request this reset, ignore this email.\n\n"
        f"Thank you,\n"
        f"{app_name} Team"
    )

    send_email(mail, to_address, subject, body)


def send_password_reset_success_email(mail, to_address, app_name):
    """
    Sends a confirmation email after a successful password reset.
    """
    subject = "Your Password Has Been Reset"

    body = (
        f"Hello,\n\n"
        f"Your password has been successfully reset.\n\n"
        f"If you made this change, no further action is required.\n\n"
        f"If you did NOT reset your password, please contact support immediately.\n\n"
        f"Thank you,\n"
        f"{app_name} Team"
    )

    send_email(mail, to_address, subject, body)
