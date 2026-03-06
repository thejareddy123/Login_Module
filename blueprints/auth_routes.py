"""
blueprints/auth_routes.py
-------------------------
This file defines all the URL routes (pages) of our app.

What is a Blueprint?
  A Blueprint is Flask's way of grouping related routes together.
  Instead of putting all routes in app.py, we put them here and
  register the Blueprint in app.py. This keeps the code organized.

What does this file do?
  - Handle HTTP requests (GET = loading a page, POST = submitting a form)
  - Read form data
  - Call service functions to do the actual work
  - Show the user the result (redirect, flash message, render page)

A fresher tip:
  Routes should be THIN — they just receive the request, call a
  service, and return a response. All the real logic is in services/.
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, current_app
)

from utils.otp_utils import (
    get_current_timestamp,
    is_in_cooldown,
    seconds_remaining_in_cooldown
)

from services.auth_service import (
    validate_registration_form,
    check_uniqueness,
    hash_password,
    prepare_pending_user,
    create_and_send_otp,
    verify_otp_and_register,
    authenticate_user,
    initiate_password_reset,
    resend_reset_otp,
    verify_reset_otp_code,
    reset_user_password,
)

from models import find_user_by_id

# Create a Blueprint named 'auth'
# url_prefix='' means routes don't get an extra prefix
auth_bp = Blueprint('auth', __name__)


# ─────────────────────────────────────────────────────────────
# HOME  /
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/')
def index():
    """Root URL — redirect to dashboard if logged in, else to login."""
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────────────────────
# REGISTRATION STEP 1  /register
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    GET  → Show the registration form.
    POST → Validate form data, store in session, go to /verify.
    """

    # GET request: just show the form
    if request.method == 'GET':
        # If the user pressed "Back to Edit" from /verify, prefill the form
        prefill = session.get('pending_user', {})
        return render_template('register.html', prefill=prefill)

    # POST request: process the submitted form
    # ── Step 1: Validate all form fields ──────────────────────
    cleaned, errors = validate_registration_form(request.form)

    # ── Step 2: Check database uniqueness (only if basic validation passed) ─
    if not errors:
        db_errors = check_uniqueness(
            current_app.extensions['mysql'],
            cleaned['email'],
            cleaned['aadhar'],
            cleaned['formatted_phone']
        )
        errors.extend(db_errors)

    # ── Step 3: If any errors, show them and re-render the form ─────────────
    if errors:
        for error_message in errors:
            flash(error_message, 'error')
        # Pass cleaned values back to re-fill the form (so user doesn't retype everything)
        return render_template('register.html', prefill=cleaned)

    # ── Step 4: Hash the password (never store plain text!) ─────────────────
    password_hash = hash_password(cleaned['password'])

    # ── Step 5: Save user data to session (NOT database yet!) ───────────────
    # We wait until email is verified before saving to DB
    session['pending_user'] = prepare_pending_user(cleaned, password_hash)

    # Clear any old OTP data when user re-submits the registration form
    for key in ('otp_hash', 'otp_expiry', 'otp_attempts', 'last_otp_sent_time'):
        session.pop(key, None)

    # ── Step 6: Go to the email verification page ───────────────────────────
    return redirect(url_for('auth.verify'))


# ─────────────────────────────────────────────────────────────
# REGISTRATION STEP 2  /verify
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/verify')
def verify():
    """
    Shows the OTP verification page.
    If no pending_user in session → redirect back to registration.
    """
    if 'pending_user' not in session:
        flash("Your session expired. Please register again.", 'warning')
        return redirect(url_for('auth.register'))

    return render_template(
        'verify.html',
        email      = session['pending_user']['email'],
        app_name   = current_app.config['APP_NAME'],
        cooldown   = current_app.config['OTP_RESEND_COOLDOWN'],
        # Pass any existing OTP timing so the JS timers can resume correctly
        expiry_ts  = session.get('otp_expiry', 0),
        last_sent  = session.get('last_otp_sent_time', 0),
        server_now = get_current_timestamp(),
    )


@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """
    AJAX endpoint — called when user clicks 'Send OTP' or 'Resend OTP'.
    Generates a new OTP, stores hash in session, and emails the user.

    Returns JSON:
        { success: true/false, message: "...", expiry_ts: ..., sent_ts: ... }
    """
    # Security check: must have pending_user in session
    if 'pending_user' not in session:
        return {'success': False, 'message': 'Session expired. Please register again.'}, 403

    now       = get_current_timestamp()
    last_sent = session.get('last_otp_sent_time', 0)
    cooldown  = current_app.config['OTP_RESEND_COOLDOWN']

    # Check 30-second cooldown
    if is_in_cooldown(last_sent, cooldown):
        secs = seconds_remaining_in_cooldown(last_sent, cooldown)
        return {
            'success': False,
            'message': f"Please wait {secs} second(s) before requesting another OTP."
        }, 429   # 429 = Too Many Requests

    # Generate OTP and send email
    email    = session['pending_user']['email']
    app_name = current_app.config['APP_NAME']
    config   = current_app.config

    otp_data = create_and_send_otp(
        current_app.extensions['mail'],
        email,
        app_name,
        config
    )

    # Save OTP data into the session
    session['otp_hash']           = otp_data['otp_hash']
    session['otp_expiry']         = otp_data['otp_expiry']
    session['last_otp_sent_time'] = otp_data['last_otp_sent_time']
    session['otp_attempts']       = 0

    return {
        'success':   True,
        'message':   'OTP sent successfully to your email.',
        'expiry_ts': otp_data['otp_expiry'],
        'sent_ts':   otp_data['last_otp_sent_time'],
    }


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    """
    AJAX endpoint — called when user clicks 'Verify & Create Account'.
    Validates the OTP and registers the user if correct.

    Returns JSON:
        On success: { success: true,  message: "...", redirect: "/login" }
        On failure: { success: false, message: "...", expired: bool, locked: bool }

        The 'expired' and 'locked' flags tell the frontend what UI to show:
          expired = true  → hide verify button, show resend button immediately
          locked  = true  → too many attempts, keep verify button disabled
    """
    if 'pending_user' not in session:
        return {'success': False, 'message': 'Session expired.'}, 403

    # Get the OTP the user typed
    otp_input = request.json.get('otp', '').strip()

    # Service returns (success, message, flags)
    # flags is a dict like {'expired': True} or {'locked': True} or {}
    success, message, flags = verify_otp_and_register(
        mysql        = current_app.extensions['mysql'],
        mail         = current_app.extensions['mail'],
        session_data = session,
        otp_input    = otp_input,
        config       = current_app.config,
        app_name     = current_app.config['APP_NAME']
    )

    if success:
        # Store the success message in the session so it appears on the login page
        # after the JavaScript redirects the user there.
        # flash() saves the message until it is displayed once, then clears it.
        flash(message, 'success')
        return {
            'success':  True,
            'message':  message,
            'redirect': url_for('auth.login')
        }
    else:
        # Merge the flags dict into the response so JS knows what happened
        # e.g. { success: false, message: "...", expired: true }
        return {'success': False, 'message': message, **flags}, 400


# ─────────────────────────────────────────────────────────────
# LOGIN  /login
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → Show the login form.
    POST → Check credentials, set session if correct.
    """
    # If already logged in, go to dashboard
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))

    if request.method == 'GET':
        return render_template('login.html')

    # Read form data
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    # ── Check for login lockout ────────────────────────────────
    # We track failed attempts per email using session keys
    attempts_key = f'login_fail_{email}'
    lockout_key  = f'login_lock_{email}'
    now          = get_current_timestamp()

    lockout_until = session.get(lockout_key, 0)
    if now < lockout_until:
        wait_secs = int(lockout_until - now)
        flash(f"Too many failed attempts. Please wait {wait_secs} seconds.", 'warning')
        return render_template('login.html', email=email)

    # ── Try to authenticate ────────────────────────────────────
    user, error = authenticate_user(
        current_app.extensions['mysql'],
        email,
        password
    )

    if user:
        # ── Login successful ──────────────────────────────────
        # Reset failed attempt counter
        session.pop(attempts_key, None)
        session.pop(lockout_key,  None)

        # Store user info in session
        session['user_id']    = user['id']
        session['user_email'] = user['email']
        session['user_name']  = user['first_name']

        flash(f"Welcome back, {user['first_name']}!", 'success')
        return redirect(url_for('auth.dashboard'))

    else:
        # ── Login failed ──────────────────────────────────────
        fail_count = session.get(attempts_key, 0) + 1
        session[attempts_key] = fail_count

        max_attempts = current_app.config['LOGIN_MAX_ATTEMPTS']

        if fail_count >= max_attempts:
            # Temporarily lock the account
            session[lockout_key]  = now + current_app.config['LOGIN_LOCKOUT_SECONDS']
            session[attempts_key] = 0
            flash("Too many failed attempts. Please wait 30 seconds.", 'warning')
        else:
            # Generic error — never say "email not found" or "wrong password"
            flash("Invalid email or password.", 'error')

        # Keep email filled in, clear password (for security)
        return render_template('login.html', email=email)


# ─────────────────────────────────────────────────────────────
# LOGOUT  /logout
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    """Clears the session and redirects to login."""
    session.clear()
    flash("You have been logged out.", 'info')
    return redirect(url_for('auth.login'))


# ─────────────────────────────────────────────────────────────
# DASHBOARD  /dashboard
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/dashboard')
def dashboard():
    """
    The protected home page after login.
    If not logged in, redirect to login.
    """
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", 'warning')
        return redirect(url_for('auth.login'))

    # Load the user's full data from the database
    user = find_user_by_id(
        current_app.extensions['mysql'],
        session['user_id']
    )

    if not user:
        # User ID in session but not in DB — clear and redirect
        session.clear()
        return redirect(url_for('auth.login'))

    return render_template('dashboard.html', user=user)


# ─────────────────────────────────────────────────────────────
# FORGOT PASSWORD STEP 1  /forgot-password
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    GET  → Show "enter your email" form.
    POST → Send reset OTP and go to OTP verification page.
    """
    if request.method == 'GET':
        return render_template('forgot_password.html')

    email = request.form.get('email', '').strip().lower()

    # This function handles everything — it never reveals if email exists
    message = initiate_password_reset(
        mysql        = current_app.extensions['mysql'],
        mail         = current_app.extensions['mail'],
        email        = email,
        session_data = session,
        config       = current_app.config,
        app_name     = current_app.config['APP_NAME']
    )

    flash(message, 'info')
    return redirect(url_for('auth.verify_reset_otp'))


# ─────────────────────────────────────────────────────────────
# FORGOT PASSWORD STEP 2  /verify-reset-otp
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    """
    GET  → Show OTP input form (with countdown timer).
    POST → Validate OTP and go to password reset form.
    """
    if 'fp_email' not in session:
        flash("Please start the password reset process.", 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'GET':
        return render_template(
            'verify_reset_otp.html',
            email      = session['fp_email'],
            expiry_ts  = session.get('fp_otp_expiry', 0),
            last_sent  = session.get('fp_last_sent', 0),
            cooldown   = current_app.config['OTP_RESEND_COOLDOWN'],
            server_now = get_current_timestamp(),
        )

    # POST: validate the submitted OTP
    otp_input = request.form.get('otp', '').strip()

    success, message = verify_reset_otp_code(session, otp_input, current_app.config)

    if success:
        flash(message, 'success')
        return redirect(url_for('auth.reset_password'))
    else:
        flash(message, 'error')
        return redirect(url_for('auth.verify_reset_otp'))


@auth_bp.route('/resend-reset-otp', methods=['POST'])
def resend_reset_otp_route():
    """
    AJAX endpoint — resend the password reset OTP.
    Called from the verify-reset-otp page's Resend button.

    Returns JSON with new timer timestamps for the frontend.
    """
    if 'fp_email' not in session:
        return {'success': False, 'message': 'Session expired.'}, 403

    success, data = resend_reset_otp(
        mysql        = current_app.extensions['mysql'],
        mail         = current_app.extensions['mail'],
        session_data = session,
        config       = current_app.config,
        app_name     = current_app.config['APP_NAME']
    )

    if success:
        return {'success': True, **data}
    else:
        return {'success': False, **data}, 429


# ─────────────────────────────────────────────────────────────
# FORGOT PASSWORD STEP 3  /reset-password
# ─────────────────────────────────────────────────────────────

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """
    GET  → Show the new password form (only reachable after OTP verified).
    POST → Update password in database, redirect to login.
    """
    # Guard: user must have passed OTP verification to reach this page
    if not session.get('fp_otp_verified') or 'fp_email' not in session:
        flash("Please verify your OTP first.", 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'GET':
        return render_template('reset_password.html', email=session['fp_email'])

    # POST: update the password
    new_password     = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    success, message = reset_user_password(
        mysql            = current_app.extensions['mysql'],
        mail             = current_app.extensions['mail'],
        session_data     = session,
        new_password     = new_password,
        confirm_password = confirm_password,
        app_name         = current_app.config['APP_NAME']
    )

    if success:
        flash(message, 'success')
        return redirect(url_for('auth.login'))
    else:
        flash(message, 'error')
        return render_template('reset_password.html', email=session.get('fp_email', ''))
