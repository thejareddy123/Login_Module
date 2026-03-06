"""
config.py
---------
This file holds all configuration settings for the application.
We read sensitive values (like passwords) from environment variables
so they are never hardcoded in the source code.

A fresher tip:
  Create a file called .env in the project root and put your
  secret values there. The dotenv library reads that file for you.
"""

import os
from dotenv import load_dotenv

# Load values from the .env file into environment variables
load_dotenv()


class Config:

    # ──────────────────────────────────────────────────────
    # SECRET KEY
    # Used by Flask to sign session cookies.
    # Change this to a long random string in production!
    # ──────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get(
        'SECRET_KEY',
        'change-this-to-a-very-long-random-secret-key'
    )

    # ──────────────────────────────────────────────────────
    # SESSION COOKIE SETTINGS
    # These make cookies more secure.
    # ──────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True    # JavaScript cannot read the cookie
    SESSION_COOKIE_SAMESITE  = 'Lax'  # Helps prevent CSRF attacks
    SESSION_COOKIE_SECURE    = False   # Set True when using HTTPS in production
    PERMANENT_SESSION_LIFETIME = 3600  # Session expires after 1 hour (in seconds)

    # ──────────────────────────────────────────────────────
    # MYSQL DATABASE SETTINGS
    # ──────────────────────────────────────────────────────
    MYSQL_HOST      = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_USER      = os.environ.get('MYSQL_USER',     'root')
    MYSQL_PASSWORD  = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB        = os.environ.get('MYSQL_DB',       'auth_system')
    MYSQL_CURSORCLASS = 'DictCursor'   # Return rows as dictionaries (easier to use)

    # ──────────────────────────────────────────────────────
    # EMAIL (SMTP) SETTINGS
    # We use Gmail's SMTP server to send emails.
    # You need to create an "App Password" in your Google account.
    # ──────────────────────────────────────────────────────
    MAIL_SERVER         = os.environ.get('MAIL_SERVER',  'smtp.gmail.com')
    MAIL_PORT           = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS        = True
    MAIL_USERNAME       = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD       = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get(
        'MAIL_DEFAULT_SENDER',
        'SecureAuth <noreply@example.com>'
    )

    # ──────────────────────────────────────────────────────
    # APPLICATION SETTINGS
    # ──────────────────────────────────────────────────────
    APP_NAME = os.environ.get('APP_NAME', 'SecureAuth')

    # ──────────────────────────────────────────────────────
    # OTP SETTINGS
    # ──────────────────────────────────────────────────────
    OTP_EXPIRY_SECONDS  = 300   # OTP is valid for 5 minutes (5 * 60 = 300 seconds)
    OTP_RESEND_COOLDOWN = 30    # User must wait 30 seconds before requesting a new OTP
    OTP_MAX_ATTEMPTS    = 5     # User gets 5 tries before OTP is locked

    # ──────────────────────────────────────────────────────
    # LOGIN SETTINGS
    # ──────────────────────────────────────────────────────
    LOGIN_MAX_ATTEMPTS    = 5   # Max failed login attempts before temporary lockout
    LOGIN_LOCKOUT_SECONDS = 30  # Wait 30 seconds after too many failed logins
