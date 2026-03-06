"""
services/auth_service.py
------------------------
This file contains the "business logic" of the authentication system.

What is business logic?
  It's the rules your app follows — like:
    "A password must have at least 8 characters"
    "The phone number must be 10 digits starting with 6/7/8/9"
    "OTP must be checked within 5 minutes"

Why put it here?
  By separating it from the routes (blueprints), we keep each file
  focused on one job. The route file just handles HTTP requests;
  this file handles the actual logic.

A fresher tip:
  If you ever need to change a validation rule, you only change it
  here — not in 5 different places.
"""

import re
import bcrypt

from models import (
    email_exists, aadhar_exists, phone_exists,
    insert_user, update_password, find_user_by_email
)
from utils.otp_utils import (
    generate_otp, hash_otp, get_current_timestamp,
    is_otp_expired, is_in_cooldown, seconds_remaining_in_cooldown
)
from utils.email_utils import (
    send_otp_email,
    send_registration_success_email,
    send_password_reset_otp_email,
    send_password_reset_success_email
)


# ═════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# Each function checks one thing and returns an error string
# if invalid, or None if valid.
# ═════════════════════════════════════════════════════════════

def validate_name(name, field_label):
    """
    Validates that a name contains only letters and spaces.
    Returns an error message string, or None if valid.
    """
    if not name:
        return f"{field_label} is required."
    if not re.match(r'^[A-Za-z ]+$', name):
        return f"{field_label} must contain alphabets only."
    return None


def validate_age(age_raw):
    """
    Validates age is a number between 18 and 100.
    Returns (age_as_int, None) on success, or (None, error_string) on failure.
    """
    try:
        age = int(age_raw)
        if not (18 <= age <= 100):
            return None, "Age must be between 18 and 100."
        return age, None
    except (ValueError, TypeError):
        return None, "Please enter a valid age."


def validate_address(address):
    """
    Validates address is at least 5 characters long.
    """
    if len(address) < 5:
        return "Address must be at least 5 characters."
    return None


def validate_aadhar(aadhar):
    """
    Validates Aadhar is exactly 12 digits.
    """
    if not aadhar.isdigit() or len(aadhar) != 12:
        return "Aadhar number must be exactly 12 digits."
    return None


def validate_email(email):
    """
    Validates email ends with @gmail.com.
    """
    if not email.endswith('@gmail.com'):
        return "Email must be a valid @gmail.com address."
    return None


def validate_indian_phone(phone_number):
    """
    Validates an Indian mobile number (without country code).

    Rules:
      - Must be exactly 10 digits
      - Must start with 6, 7, 8, or 9
      - No spaces, dashes, or letters allowed

    Returns:
        (formatted_number, None)  if valid   e.g. ('+919876543210', None)
        (None, error_string)      if invalid
    """
    # Remove any spaces the user might have typed
    phone_number = phone_number.strip()

    # Check: only digits allowed
    if not phone_number.isdigit():
        return None, "Phone number must contain digits only."

    # Check: must be exactly 10 digits
    if len(phone_number) != 10:
        return None, "Phone number must be exactly 10 digits."

    # Check: must start with 6, 7, 8, or 9
    if phone_number[0] not in ('6', '7', '8', '9'):
        return None, "Phone number is invaid "

    # Format as +91XXXXXXXXXX for storage
    formatted = "+91" + phone_number
    return formatted, None


def validate_password(password):
    """
    Validates password strength.

    Rules:
      - At least 8 characters
      - At least 1 uppercase letter (A-Z)
      - At least 1 lowercase letter (a-z)
      - At least 1 number (0-9)
      - At least 1 special character (like @, #, !, etc.)

    Returns None if valid, or an error string if invalid.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return "Password must contain at least one number."
    if not re.search(r'[^A-Za-z0-9]', password):
        return "Password must contain at least one special character."
    return None


def validate_registration_form(form_data):
    """
    Runs all validations on the registration form data.

    Parameters:
        form_data (dict): Dictionary of all form field values.

    Returns:
        (cleaned_data dict, errors list)
        - cleaned_data contains sanitized values (or None if validation failed)
        - errors is a list of error message strings (empty if all valid)
    """
    errors = []

    # ── Sanitize inputs first ──────────────────────────────
    # .strip()  removes leading/trailing spaces
    # .title()  capitalises first letter of each word (e.g. "john doe" → "John Doe")
    # .lower()  converts to lowercase (for email)

    first_name = form_data.get('first_name', '').strip().title()
    last_name  = form_data.get('last_name',  '').strip().title()
    age_raw    = form_data.get('age', '').strip()
    gender     = form_data.get('gender', '').strip()
    address    = form_data.get('address', '').strip()
    aadhar     = form_data.get('aadhar', '').strip()
    email      = form_data.get('email', '').strip().lower()
    phone_raw  = form_data.get('phone', '').strip()
    password   = form_data.get('password', '')
    confirm_pw = form_data.get('confirm_password', '')

    # ── Run each validation ────────────────────────────────
    err = validate_name(first_name, "First name")
    if err: errors.append(err)

    err = validate_name(last_name, "Last name")
    if err: errors.append(err)

    age, err = validate_age(age_raw)
    if err: errors.append(err)

    if not gender:
        errors.append("Please select a gender.")

    err = validate_address(address)
    if err: errors.append(err)

    err = validate_aadhar(aadhar)
    if err: errors.append(err)

    err = validate_email(email)
    if err: errors.append(err)

    formatted_phone, err = validate_indian_phone(phone_raw)
    if err: errors.append(err)

    err = validate_password(password)
    if err:
        errors.append(err)
    elif password != confirm_pw:
        errors.append("Passwords do not match.")

    # Return cleaned data so the caller has sanitized values
    cleaned = {
        'first_name': first_name,
        'last_name':  last_name,
        'age':        age,
        'gender':     gender,
        'address':    address,
        'aadhar':     aadhar,
        'email':      email,
        'phone':      phone_raw,       # original input (for form re-fill)
        'formatted_phone': formatted_phone,
        'password':   password,
    }

    return cleaned, errors


# ═════════════════════════════════════════════════════════════
# REGISTRATION SERVICE FUNCTIONS
# ═════════════════════════════════════════════════════════════

def check_uniqueness(mysql, email, aadhar, formatted_phone):
    """
    Checks if email, aadhar, or phone already exist in the database.

    Returns:
        list: A list of error messages. Empty list means all values are unique.
    """
    errors = []

    if email_exists(mysql, email):
        errors.append("This email address is already registered.")

    if aadhar_exists(mysql, aadhar):
        errors.append("This Aadhar number is already registered.")

    if phone_exists(mysql, formatted_phone):
        errors.append("This phone number is already registered.")

    return errors


def hash_password(plain_password):
    """
    Hashes a plain-text password using bcrypt.

    bcrypt automatically:
      - Adds a random "salt" (extra random data) to make hashes unique
      - Runs the hash thousands of times to make brute-force attacks slow

    Returns:
        str: The hashed password as a string.
    """
    # bcrypt needs bytes, so we encode the string first
    # gensalt() creates a unique salt each time
    hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
    return hashed.decode()   # Convert bytes back to string for storage


def prepare_pending_user(cleaned_data, password_hash):
    """
    Builds the 'pending_user' dictionary to store in the session.
    We store this BEFORE inserting into the database (waiting for OTP verification).

    Returns:
        dict: All user data ready to be stored in session.
    """
    return {
        'first_name':    cleaned_data['first_name'],
        'last_name':     cleaned_data['last_name'],
        'age':           cleaned_data['age'],
        'gender':        cleaned_data['gender'],
        'address':       cleaned_data['address'],
        'aadhar_number': cleaned_data['aadhar'],
        'email':         cleaned_data['email'],
        'phone_number':  cleaned_data['formatted_phone'],
        'password_hash': password_hash,
    }


def create_and_send_otp(mail, email, app_name, config):
    """
    Generates a new OTP, hashes it, and sends it by email.

    Returns:
        dict: OTP session data to store (otp_hash, otp_expiry, last_otp_sent_time)
    """
    now        = get_current_timestamp()
    otp        = generate_otp()
    otp_hash   = hash_otp(otp)
    otp_expiry = now + config['OTP_EXPIRY_SECONDS']   # e.g. now + 300 seconds

    # Send the OTP by email
    send_otp_email(mail, email, otp, app_name)

    # Return data to be stored in the session
    return {
        'otp_hash':          otp_hash,
        'otp_expiry':        otp_expiry,
        'last_otp_sent_time': now,
        'otp_attempts':      0,
    }


def verify_otp_and_register(mysql, mail, session_data, otp_input, config, app_name):
    """
    Verifies the submitted OTP and, if correct, inserts the user into the database.

    Parameters:
        mysql        : MySQL extension instance
        mail         : Flask-Mail instance
        session_data : The Flask session dictionary
        otp_input    : The OTP string entered by the user
        config       : App configuration dictionary
        app_name     : Application name (for emails)

    Returns:
        (success: bool, message: str, flags: dict)

        flags is a dictionary with extra info for the frontend:
          - flags['expired'] = True  → OTP has expired (show resend button)
          - flags['locked']  = True  → Too many wrong attempts (block verify button)
        Both default to False when not set.
    """
    # Step 1: Check OTP is all digits
    if not otp_input.isdigit():
        return False, "OTP must contain only numbers.", {}

    # Step 2: Check if OTP was ever sent
    if 'otp_hash' not in session_data:
        return False, "No OTP found. Please click 'Send OTP' first.", {}

    # Step 3: Check if OTP has expired
    # If expired → tell the frontend so it can show the Resend button immediately
    if is_otp_expired(session_data.get('otp_expiry', 0)):
        return False, "OTP has expired. Please request a new one.", {'expired': True}

    # Step 4: Check attempt limit
    attempts = session_data.get('otp_attempts', 0)
    if attempts >= config['OTP_MAX_ATTEMPTS']:
        # If locked → tell the frontend so it keeps the verify button disabled
        return False, "Too many incorrect attempts. Please request a new OTP.", {'locked': True}

    # Step 5: Compare entered OTP with stored hash
    if hash_otp(otp_input) != session_data.get('otp_hash'):
        # Increment the failed attempt counter
        session_data['otp_attempts'] = attempts + 1
        attempts_left = config['OTP_MAX_ATTEMPTS'] - session_data['otp_attempts']
        return False, f"Incorrect OTP. {attempts_left} attempt(s) remaining.", {}

    # ── OTP is CORRECT ─────────────────────────────────────────────────────

    pending = session_data['pending_user']

    # Re-normalize email just before inserting (good practice)
    pending['email'] = pending['email'].strip().lower()

    # Re-check uniqueness to prevent race conditions
    # (two users submitting the same email at the same millisecond)
    if email_exists(mysql, pending['email']):
        return False, "This email was just registered by someone else.", {}
    if aadhar_exists(mysql, pending['aadhar_number']):
        return False, "This Aadhar number was just registered by someone else.", {}
    if phone_exists(mysql, pending['phone_number']):
        return False, "This phone number was just registered by someone else.", {}

    # Insert the user into the database
    insert_user(mysql, pending)

    # Send welcome email
    send_registration_success_email(
        mail,
        pending['email'],
        pending['first_name'],
        app_name
    )

    # Clear all OTP and pending user data from session
    for key in ('pending_user', 'otp_hash', 'otp_expiry',
                'otp_attempts', 'last_otp_sent_time'):
        session_data.pop(key, None)

    return True, "Registration successful. You can now log in.", {}


# ═════════════════════════════════════════════════════════════
# LOGIN SERVICE FUNCTIONS
# ═════════════════════════════════════════════════════════════

def authenticate_user(mysql, email, password):
    """
    Checks if the email and password are correct.

    Returns:
        (user_dict, None)  if credentials are correct
        (None, error_str)  if wrong
    """
    # Look up the user by email
    user = find_user_by_email(mysql, email)

    if user is None:
        # We don't say "email not found" — that reveals too much info
        return None, "Invalid email or password."

    # bcrypt.checkpw() compares the plain password with the stored hash
    # It returns True if they match, False otherwise
    password_matches = bcrypt.checkpw(
        password.encode(),              # plain password as bytes
        user['password_hash'].encode()  # stored hash as bytes
    )

    if not password_matches:
        return None, "Invalid email or password."

    return user, None


# ═════════════════════════════════════════════════════════════
# FORGOT PASSWORD SERVICE FUNCTIONS
# ═════════════════════════════════════════════════════════════

def initiate_password_reset(mysql, mail, email, session_data, config, app_name):
    """
    Handles the first step of password reset: generate & send OTP.

    Security rule: We NEVER reveal whether the email exists or not.
    We always show the same message to the user.

    Returns:
        str: A generic message to display (same regardless of whether email exists)
    """
    generic_message = "If this email is registered, a reset code has been sent."

    # Basic email format check
    if not email.endswith('@gmail.com'):
        return generic_message

    now       = get_current_timestamp()
    last_sent = session_data.get('fp_last_sent', 0)

    # Check 30-second cooldown
    if is_in_cooldown(last_sent, config['OTP_RESEND_COOLDOWN']):
        return generic_message

    # Only generate and send OTP if the email actually exists
    user = find_user_by_email(mysql, email)
    if user:
        otp        = generate_otp()
        otp_hash   = hash_otp(otp)
        otp_expiry = now + config['OTP_EXPIRY_SECONDS']

        # Store reset OTP data in session (prefixed with 'fp_' for 'forgot password')
        session_data['fp_email']        = email
        session_data['fp_otp_hash']     = otp_hash
        session_data['fp_otp_expiry']   = otp_expiry
        session_data['fp_otp_attempts'] = 0
        session_data['fp_last_sent']    = now

        # Clear any previous verified flag
        session_data.pop('fp_otp_verified', None)

        send_password_reset_otp_email(mail, email, otp, app_name)

    return generic_message


def resend_reset_otp(mysql, mail, session_data, config, app_name):
    """
    Resends a new OTP for password reset. Used from the verify-reset-otp page.

    Invalidates the previous OTP immediately by overwriting it.

    Returns:
        (success: bool, data: dict)
        data contains: message, expiry_ts, sent_ts (for the frontend timers)
    """
    now       = get_current_timestamp()
    last_sent = session_data.get('fp_last_sent', 0)

    # Server-side cooldown check
    if is_in_cooldown(last_sent, config['OTP_RESEND_COOLDOWN']):
        secs = seconds_remaining_in_cooldown(last_sent, config['OTP_RESEND_COOLDOWN'])
        return False, {
            'message': f"Please wait {secs} second(s) before requesting another OTP."
        }

    email = session_data.get('fp_email')
    user  = find_user_by_email(mysql, email)

    expiry = now + config['OTP_EXPIRY_SECONDS']

    if user:
        otp      = generate_otp()
        otp_hash = hash_otp(otp)

        # Overwrite old OTP — this invalidates it immediately
        session_data['fp_otp_hash']     = otp_hash
        session_data['fp_otp_expiry']   = expiry
        session_data['fp_otp_attempts'] = 0
        session_data['fp_last_sent']    = now

        send_password_reset_otp_email(mail, email, otp, app_name)

    return True, {
        'message':   'A new OTP has been sent to your email.',
        'expiry_ts': expiry,
        'sent_ts':   now,
    }


def verify_reset_otp_code(session_data, otp_input, config):
    """
    Validates the OTP entered on the verify-reset-otp page.

    Returns:
        (success: bool, message: str)
    """
    if not otp_input.isdigit():
        return False, "OTP must contain only numbers."

    if 'fp_otp_hash' not in session_data:
        return False, "No OTP found. Please go back and request a new one."

    if is_otp_expired(session_data.get('fp_otp_expiry', 0)):
        return False, "OTP has expired. Please request a new one."

    attempts = session_data.get('fp_otp_attempts', 0)
    if attempts >= config['OTP_MAX_ATTEMPTS']:
        return False, "Too many incorrect attempts. Please restart the process."

    if hash_otp(otp_input) != session_data.get('fp_otp_hash'):
        session_data['fp_otp_attempts'] = attempts + 1
        attempts_left = config['OTP_MAX_ATTEMPTS'] - session_data['fp_otp_attempts']
        return False, f"Incorrect OTP. {attempts_left} attempt(s) remaining."

    # OTP is correct — mark as verified
    session_data['fp_otp_verified'] = True

    # Clear OTP data from session (no longer needed)
    for key in ('fp_otp_hash', 'fp_otp_expiry', 'fp_otp_attempts', 'fp_last_sent'):
        session_data.pop(key, None)

    return True, "OTP verified successfully."


def reset_user_password(mysql, mail, session_data, new_password, confirm_password, app_name):
    """
    Resets the user's password after OTP verification.

    Returns:
        (success: bool, message: str)
    """
    # Validate new password strength
    err = validate_password(new_password)
    if err:
        return False, err

    if new_password != confirm_password:
        return False, "Passwords do not match."

    email    = session_data.get('fp_email')
    new_hash = hash_password(new_password)

    # Update the password in the database
    update_password(mysql, email, new_hash)

    # Send confirmation email
    send_password_reset_success_email(mail, email, app_name)

    # Clear all reset-related and login session data
    for key in ('fp_email', 'fp_otp_verified', 'user_id', 'user_email', 'user_name'):
        session_data.pop(key, None)

    return True, "Password reset successfully. Please log in with your new password."
