/**
 * auth.js — Frontend JavaScript for the Authentication System
 * ============================================================
 *
 * This file handles:
 *   1. Registration form — inline validation, password strength bar
 *   2. Verify page      — OTP send/resend, 5-min expiry timer, 30-s cooldown
 *   3. Login form       — disable button on submit
 *   4. Reset password   — password strength bar, validation
 *   5. Verify Reset OTP — same timer/cooldown logic as verify page
 *
 * A fresher tip:
 *   We wrap each section in an IIFE (Immediately Invoked Function Expression):
 *     (function() { ... })();
 *   This means the code runs immediately but keeps variables private,
 *   so different sections don't accidentally overwrite each other's variables.
 */


/* ════════════════════════════════════════════════════════════
   SECTION 1 — SHARED HELPER FUNCTIONS
   These are used by multiple sections below.
════════════════════════════════════════════════════════════ */

/**
 * Shows an inline error message below a form field.
 * Also adds a red border to the field.
 *
 * @param {HTMLElement} field - The input element
 * @param {string}      msg   - The error message to display
 */
function setFieldError(field, msg) {
  if (!field) return;

  // Add red border
  field.classList.add('error');

  // Find or create the error message element
  let errorSpan = field.parentElement.querySelector('.field-error');
  if (!errorSpan) {
    errorSpan = document.createElement('span');
    errorSpan.className = 'field-error';
    errorSpan.style.cssText = 'font-size:0.75rem; color:#e05555; display:block; margin-top:0.25rem;';
    field.parentElement.appendChild(errorSpan);
  }

  errorSpan.textContent = msg;
}

/**
 * Clears the error styling and message from a field.
 *
 * @param {HTMLElement} field - The input element
 */
function clearFieldError(field) {
  if (!field) return;
  field.classList.remove('error');
  const errorSpan = field.parentElement.querySelector('.field-error');
  if (errorSpan) errorSpan.textContent = '';
}

/**
 * Validates a single form field based on its id/name.
 * Shows inline error if invalid.
 *
 * @param  {HTMLElement} field
 * @returns {boolean} true if valid, false if invalid
 */
function validateField(field) {
  const fieldId = field.id || field.name;
  const value   = field.value.trim();

  // First name and last name: letters only
  if (fieldId === 'first_name' || fieldId === 'last_name') {
    if (!value || !/^[A-Za-z ]+$/.test(value)) {
      setFieldError(field, 'Alphabets only.');
      return false;
    }
  }

  // Age: number between 18 and 100
  if (fieldId === 'age') {
    const ageNum = parseInt(value, 10);
    if (isNaN(ageNum) || ageNum < 18 || ageNum > 100) {
      setFieldError(field, 'Age must be between 18 and 100.');
      return false;
    }
  }

  // Address: at least 5 characters
  if (fieldId === 'address') {
    if (value.length < 5) {
      setFieldError(field, 'At least 5 characters required.');
      return false;
    }
  }

  // Aadhar: exactly 12 digits
  if (fieldId === 'aadhar') {
    if (!/^\d{12}$/.test(value)) {
      setFieldError(field, 'Must be exactly 12 digits.');
      return false;
    }
  }

  // Email: must end with @gmail.com
  if (fieldId === 'email') {
    if (!value.endsWith('@gmail.com')) {
      setFieldError(field, 'Must end with @gmail.com.');
      return false;
    }
  }

  // Phone: 10 digits, starting with 6/7/8/9
  if (fieldId === 'phone') {
    if (!/^\d{10}$/.test(value)) {
      setFieldError(field, 'Must be exactly 10 digits.');
      return false;
    }
    if (!['6','7','8','9'].includes(value[0])) {
      setFieldError(field, 'Must start with 6, 7, 8, or 9.');
      return false;
    }
  }

  // Password: strength rules
  if (fieldId === 'password') {
    const passwordError = getPasswordError(value);
    if (passwordError) {
      setFieldError(field, passwordError);
      return false;
    }
  }

  // Confirm password: must match password
  if (fieldId === 'confirm_password') {
    const passwordField = document.getElementById('password');
    if (passwordField && value !== passwordField.value) {
      setFieldError(field, 'Passwords do not match.');
      return false;
    }
  }

  // If we reach here, the field is valid
  clearFieldError(field);
  return true;
}

/**
 * Checks password strength rules.
 * Returns an error string if invalid, or null if valid.
 *
 * @param  {string} password
 * @returns {string|null}
 */
function getPasswordError(password) {
  if (password.length < 8)           return 'At least 8 characters required.';
  if (!/[A-Z]/.test(password))       return 'Must contain an uppercase letter.';
  if (!/[a-z]/.test(password))       return 'Must contain a lowercase letter.';
  if (!/\d/.test(password))          return 'Must contain a number.';
  if (!/[^A-Za-z0-9]/.test(password)) return 'Must contain a special character.';
  return null;
}

/**
 * Calculates a password strength score from 0 to 4.
 * Used to fill the strength bar.
 *
 * @param  {string} password
 * @returns {number} 0 = empty/weak, 4 = strong
 */
function getPasswordScore(password) {
  let score = 0;
  if (password.length >= 8)           score++;
  if (/[A-Z]/.test(password))         score++;
  if (/\d/.test(password))            score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;
  return score;
}

/**
 * Formats a number of seconds as MM:SS string.
 * Example: formatTime(90) → "01:30"
 *
 * @param  {number} totalSeconds
 * @returns {string}
 */
function formatTime(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
  const seconds = String(totalSeconds % 60).padStart(2, '0');
  return `${minutes}:${seconds}`;
}


/* ════════════════════════════════════════════════════════════
   SECTION 2 — REGISTRATION FORM
   File: register.html
════════════════════════════════════════════════════════════ */

(function initRegistrationForm() {

  // Only run on the registration page
  const form = document.getElementById('registerForm');
  if (!form) return;

  // ── Auto-capitalize first letter of name fields as user types ─────────
  ['first_name', 'last_name'].forEach(function(fieldName) {
    const input = form.elements[fieldName];
    if (!input) return;

    input.addEventListener('input', function() {
      // Save cursor position so it doesn't jump to the end
      const cursorPos = input.selectionStart;
      // Capitalize the first letter of each word
      input.value = input.value.replace(/\b\w/g, function(char) {
        return char.toUpperCase();
      });
      // Restore cursor position
      input.setSelectionRange(cursorPos, cursorPos);
    });

    // Validate on blur (when user leaves the field)
    input.addEventListener('blur', function() { validateField(input); });
  });

  // ── Email: auto lowercase + trim when user leaves the field ───────────
  const emailInput = form.elements['email'];
  if (emailInput) {
    emailInput.addEventListener('blur', function() {
      emailInput.value = emailInput.value.trim().toLowerCase();
      validateField(emailInput);
    });
  }

  // ── Validate all other fields on blur ─────────────────────────────────
  form.querySelectorAll('input, select').forEach(function(input) {
    input.addEventListener('blur', function() { validateField(input); });
  });

  // ── Password strength bar ──────────────────────────────────────────────
  const passwordInput = form.elements['password'];
  const strengthBar   = document.getElementById('strengthFill');
  const strengthLabel = document.getElementById('strengthLabel');

  // Colour and text for each score level (0=none, 1=weak, 2=fair, 3=good, 4=strong)
  const barColors  = ['#e05555', '#e09a40', '#e8c96d', '#4caf7d'];
  const barLabels  = ['Weak', 'Fair', 'Good', 'Strong'];

  if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', function() {
      const score = getPasswordScore(passwordInput.value);

      // Update bar width (each level = 25%)
      strengthBar.style.width      = (score * 25) + '%';
      strengthBar.style.background = score > 0 ? barColors[score - 1] : '#2a2a38';

      // Update label text
      if (strengthLabel) {
        strengthLabel.textContent = passwordInput.value ? barLabels[Math.max(0, score - 1)] : '';
      }
    });
  }

  // ── Full form validation on submit ─────────────────────────────────────
  form.addEventListener('submit', function(event) {
    let allValid = true;

    // Check every required field
    form.querySelectorAll('input[required], select[required]').forEach(function(input) {
      if (!validateField(input)) {
        allValid = false;
      }
    });

    if (!allValid) {
      // Stop form from submitting if any field is invalid
      event.preventDefault();
      return;
    }

    // Disable the submit button to prevent the user clicking twice
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add('loading');
    }
  });

})(); // End of registration form section


/* ════════════════════════════════════════════════════════════
   SECTION 3 — OTP VERIFY PAGE  (Registration flow)
   File: verify.html

   What this section does:
     ┌─ User clicks "Send OTP"
     │    → AJAX call to /send-otp
     │    → Hide "Send OTP" button, show OTP input section
     │    → Start 3-minute expiry countdown  (timerWrap)
     │    → Show resend section immediately
     │    → Start 30-second cooldown         (resendBtn disabled)
     │
     ├─ Cooldown counting (0 → 30 s):
     │    → cooldownText shows "Resend OTP available in 30 seconds"
     │    → resendBtn is DISABLED
     │
     ├─ Cooldown finished (after 30 s):
     │    → cooldownText is hidden
     │    → resendBtn is ENABLED
     │
     ├─ OTP expires (after 3 minutes):
     │    → timerWrap is hidden
     │    → cooldown timer is STOPPED (user doesn't need cooldown anymore)
     │    → cooldownText is hidden
     │    → resendBtn is ENABLED immediately
     │    → Status shows "OTP expired. Click Resend OTP."
     │    → verifyOtpBtn is DISABLED (can't verify an expired OTP)
     │
     └─ User clicks "Resend OTP":
          → AJAX call to /send-otp
          → New OTP sent, previous one invalidated
          → Restart 3-min expiry countdown
          → Restart 30-s cooldown (disable resend button again)
════════════════════════════════════════════════════════════ */

(function initVerifyPage() {

  // Only run this code when we are on the verify page
  const pageElement = document.getElementById('verifyPage');
  if (!pageElement) return;

  // ── Grab all UI elements we need ──────────────────────────────────────
  const sendOtpBtn     = document.getElementById('sendOtpBtn');
  const sendBtnSection = document.getElementById('sendBtnSection');
  const otpSection     = document.getElementById('otpInputSection');
  const otpInput       = document.getElementById('otp_input');
  const verifyOtpBtn   = document.getElementById('verifyOtpBtn');

  const timerWrap      = document.getElementById('timerWrap');
  const timerText      = document.getElementById('timerText');      // "OTP expires in MM:SS"

  const resendSection  = document.getElementById('resendSection');
  const cooldownText   = document.getElementById('cooldownText');   // "Resend OTP available in Xs"
  const resendBtn      = document.getElementById('resendBtn');

  const statusDiv      = document.getElementById('otpStatus');      // feedback messages

  // ── Timer variables ────────────────────────────────────────────────────
  // We store the interval IDs so we can stop them with clearInterval()
  let expiryTimer   = null;   // runs every second, counts down 3 minutes
  let cooldownTimer = null;   // runs every second, counts down 30 seconds

  // ── Read any existing timestamps from server (for page-refresh resume) ──
  // If the user already sent an OTP and then refreshed, these won't be 0
  const existingExpiryTs = parseFloat(pageElement.dataset.expiryTs || '0');
  const existingSentTs   = parseFloat(pageElement.dataset.sentTs   || '0');
  const COOLDOWN_SECS    = parseInt(pageElement.dataset.cooldown   || '30', 10);


  // ── HELPER: Show a coloured status message ─────────────────────────────
  // type = 'success' | 'error' | 'warning' | 'info'
  function showStatus(message, type) {
    statusDiv.textContent   = message;
    statusDiv.className     = 'flash ' + type;
    statusDiv.style.display = 'flex';
  }

  // ── HELPER: Hide the status message ───────────────────────────────────
  function hideStatus() {
    statusDiv.style.display = 'none';
  }


  // ── HELPER: Start (or restart) the 3-minute OTP expiry countdown ───────
  //
  // Shows: "OTP expires in 02:59", "OTP expires in 02:58" … "00:00"
  //
  // When timer reaches 0:
  //   - Hides the timer display
  //   - Stops the cooldown timer (not needed anymore)
  //   - Hides the cooldown message
  //   - Enables the Resend button immediately
  //   - Disables the Verify button (expired OTP can't be verified)
  //   - Shows "OTP expired. Click Resend OTP."
  //
  function startExpiryCountdown(expiryTimestamp) {
    // Stop any previous expiry timer before starting a new one
    clearInterval(expiryTimer);

    // Show the timer display
    timerWrap.style.display = 'block';

    // Make sure the verify button is enabled while OTP is still valid
    verifyOtpBtn.disabled = false;

    expiryTimer = setInterval(function () {
      // How many seconds remain before OTP expires?
      const nowSecs     = Math.floor(Date.now() / 1000);
      const secondsLeft = Math.max(0, Math.floor(expiryTimestamp - nowSecs));

      // Update the on-screen timer text
      timerText.textContent = 'OTP expires in ' + formatTime(secondsLeft);

      if (secondsLeft <= 0) {
        // ── OTP has expired ───────────────────────────────────────────

        // 1. Stop both timers — no longer needed
        clearInterval(expiryTimer);
        clearInterval(cooldownTimer);

        // 2. Hide the expiry countdown
        timerWrap.style.display = 'none';

        // 3. Hide the cooldown message (cooldown is irrelevant now)
        cooldownText.style.display = 'none';

        // 4. Enable Resend button immediately (user must request a new OTP)
        resendBtn.disabled = false;

        // 5. Disable Verify button (can't verify an expired OTP)
        verifyOtpBtn.disabled = true;

        // 6. Show the expiry message
        showStatus('OTP expired. Click Resend OTP.', 'warning');
      }
    }, 1000); // tick every 1 second
  }


  // ── HELPER: Start (or restart) the 30-second resend cooldown ──────────
  //
  // Shows: "Resend OTP available in 30 seconds" … "Resend OTP available in 1 second"
  // Disables resendBtn for 30 seconds, then enables it.
  //
  // The cooldown timer is STOPPED immediately if the OTP expires,
  // so the user doesn't see a cooldown countdown after expiry.
  //
  function startResendCooldown(sentTimestamp) {
    // Stop any previous cooldown timer
    clearInterval(cooldownTimer);

    // Disable the resend button right away
    resendBtn.disabled = true;

    cooldownTimer = setInterval(function () {
      const nowSecs     = Math.floor(Date.now() / 1000);
      const elapsed     = nowSecs - Math.floor(sentTimestamp);
      const secondsLeft = Math.max(0, COOLDOWN_SECS - elapsed);

      if (secondsLeft > 0) {
        // Still in cooldown — show the countdown and keep button disabled
        cooldownText.style.display = 'block';
        cooldownText.textContent   =
          'Resend OTP available in ' + secondsLeft +
          ' second' + (secondsLeft !== 1 ? 's' : '');
        resendBtn.disabled = true;

      } else {
        // Cooldown finished — hide message, enable button
        clearInterval(cooldownTimer);
        cooldownText.style.display = 'none';
        resendBtn.disabled = false;
      }
    }, 1000);
  }


  // ── HELPER: Activate the OTP input UI after a successful send ─────────
  //
  // Called after both the first Send and every Resend:
  //   - Hides the initial "Send OTP" button section
  //   - Shows the OTP input section
  //   - Shows the resend section (with cooldown running)
  //   - Starts the expiry and cooldown timers
  //
  function activateOtpUI(expiryTs, sentTs) {
    // Hide the initial send-button area
    sendBtnSection.style.display = 'none';

    // Show the OTP input + timer + resend section
    otpSection.style.display    = 'block';
    resendSection.style.display = 'block';

    // Clear the OTP input so user types into a fresh field
    otpInput.value = '';

    // Start/restart both countdown timers
    startExpiryCountdown(expiryTs);
    startResendCooldown(sentTs);
  }


  // ── Auto-resume timers if OTP was already sent (e.g. page refresh) ────
  //
  // If existingExpiryTs > 0, it means the user already clicked Send OTP
  // before this page load. We restore the UI to the correct state.
  //
  if (existingExpiryTs > 0) {
    // Show OTP section (as if user had already clicked Send OTP)
    sendBtnSection.style.display = 'none';
    otpSection.style.display     = 'block';
    resendSection.style.display  = 'block';

    // Resume timers from where they were
    startExpiryCountdown(existingExpiryTs);
    startResendCooldown(existingSentTs);
  }


  // ── EVENT: "Send OTP" button clicked ──────────────────────────────────
  sendOtpBtn.addEventListener('click', async function () {

    // Disable button so user can't click twice
    sendOtpBtn.disabled = true;
    sendOtpBtn.classList.add('loading');

    try {
      // Call the server to generate and email the OTP
      const response = await fetch('/send-otp', {
        method: 'POST',
        headers: {
          // Flask-WTF requires this CSRF header on every POST
          'X-CSRFToken': document.querySelector('[name=csrf_token]').value
        }
      });

      const result = await response.json();

      if (result.success) {
        showStatus(result.message, 'success');
        // Switch UI to OTP-entry mode and start timers
        activateOtpUI(result.expiry_ts, result.sent_ts);

      } else {
        // Server rejected the request (e.g. cooldown still active)
        showStatus(result.message, 'error');
        sendOtpBtn.disabled = false;
      }

    } catch (networkError) {
      showStatus('Network error. Please try again.', 'error');
      sendOtpBtn.disabled = false;
    }

    sendOtpBtn.classList.remove('loading');
  });


  // ── EVENT: "Resend OTP" button clicked ────────────────────────────────
  resendBtn.addEventListener('click', async function () {

    resendBtn.disabled    = true;
    resendBtn.textContent = 'Sending…';

    try {
      // Same endpoint as Send OTP — the server always generates a fresh OTP
      const response = await fetch('/send-otp', {
        method: 'POST',
        headers: {
          'X-CSRFToken': document.querySelector('[name=csrf_token]').value
        }
      });

      const result = await response.json();

      if (result.success) {
        showStatus(result.message, 'success');
        otpInput.focus();

        // Restart both timers with fresh timestamps from the server
        // This also re-disables the resend button for another 30 seconds
        startExpiryCountdown(result.expiry_ts);
        startResendCooldown(result.sent_ts);

      } else {
        // e.g. server-side cooldown still active (shouldn't happen normally
        // because the button is disabled client-side, but good to handle)
        showStatus(result.message, 'warning');
        resendBtn.disabled = false;
      }

    } catch (networkError) {
      showStatus('Network error. Please try again.', 'error');
      resendBtn.disabled = false;
    }

    resendBtn.textContent = '↺ Resend OTP';
  });


  // ── EVENT: "Verify & Create Account" button clicked ───────────────────
  verifyOtpBtn.addEventListener('click', async function () {

    const enteredOtp = otpInput.value.trim();

    // Quick client-side check before hitting the server
    if (!enteredOtp || !/^\d{6}$/.test(enteredOtp)) {
      showStatus('Please enter the 6-digit OTP.', 'error');
      return;
    }

    verifyOtpBtn.disabled = true;
    verifyOtpBtn.classList.add('loading');

    try {
      const response = await fetch('/verify-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  document.querySelector('[name=csrf_token]').value
        },
        body: JSON.stringify({ otp: enteredOtp })
      });

      const result = await response.json();

      if (result.success) {
        // ── OTP correct: stop timers, redirect ──────────────────────
        clearInterval(expiryTimer);
        clearInterval(cooldownTimer);

        showStatus('Verified! Redirecting…', 'success');

        // Short delay so the user can see the success message
        setTimeout(function () {
          window.location.href = result.redirect;
        }, 1200);

      } else {
        // ── OTP wrong or expired ─────────────────────────────────────
        showStatus(result.message, 'error');
        otpInput.value = '';
        otpInput.focus();

        if (result.expired) {
          // Server says OTP expired — stop timers, enable resend
          clearInterval(expiryTimer);
          clearInterval(cooldownTimer);
          timerWrap.style.display    = 'none';
          cooldownText.style.display = 'none';
          resendBtn.disabled         = false;
          verifyOtpBtn.disabled      = true;

        } else if (result.locked) {
          // Too many wrong attempts — keep verify button disabled
          verifyOtpBtn.disabled = true;

        } else {
          // Wrong OTP but still have attempts left — let user try again
          verifyOtpBtn.disabled = false;
        }
      }

    } catch (networkError) {
      showStatus('Network error. Please try again.', 'error');
      verifyOtpBtn.disabled = false;
    }

    verifyOtpBtn.classList.remove('loading');
  });


  // ── INPUT: OTP field — digits only, max 6 ─────────────────────────────
  otpInput.addEventListener('input', function () {
    otpInput.value = otpInput.value.replace(/\D/g, '').slice(0, 6);
  });

  // Allow pressing Enter in OTP input to trigger the verify button
  otpInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') verifyOtpBtn.click();
  });

})(); // End of Section 3


/* ════════════════════════════════════════════════════════════
   SECTION 4 — LOGIN FORM
   File: login.html
════════════════════════════════════════════════════════════ */

(function initLoginForm() {

  const form = document.getElementById('loginForm');
  if (!form) return;

  form.addEventListener('submit', function() {
    // Disable submit button to prevent double-submission
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add('loading');
    }
  });

})();


/* ════════════════════════════════════════════════════════════
   SECTION 5 — RESET PASSWORD FORM
   File: reset_password.html

   Just handles password strength bar and validation.
   (OTP verification is on a separate page.)
════════════════════════════════════════════════════════════ */

(function initResetPasswordForm() {

  const form = document.getElementById('resetForm');
  if (!form) return;

  // Password strength bar (same logic as registration)
  const passwordInput = form.elements['password'];
  const strengthBar   = document.getElementById('strengthFill');
  const strengthLabel = document.getElementById('strengthLabel');

  const barColors = ['#e05555', '#e09a40', '#e8c96d', '#4caf7d'];
  const barLabels = ['Weak', 'Fair', 'Good', 'Strong'];

  if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', function() {
      const score = getPasswordScore(passwordInput.value);
      strengthBar.style.width      = (score * 25) + '%';
      strengthBar.style.background = score > 0 ? barColors[score - 1] : '#2a2a38';
      if (strengthLabel) {
        strengthLabel.textContent = passwordInput.value ? barLabels[Math.max(0, score - 1)] : '';
      }
    });
  }

  // Validate on submit
  form.addEventListener('submit', function(event) {
    let allValid = true;

    form.querySelectorAll('input').forEach(function(input) {
      if (!validateField(input)) allValid = false;
    });

    if (!allValid) {
      event.preventDefault();
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.classList.add('loading');
    }
  });

})();


/* ════════════════════════════════════════════════════════════
   SECTION 6 — VERIFY RESET OTP PAGE  (Forgot-password flow)
   File: verify_reset_otp.html

   This page is reached after the user submits their email on
   /forgot-password. The server has ALREADY sent the OTP, so
   the OTP input and timers show immediately on page load.

   Behavior is the same as Section 3 (registration verify page),
   with one key difference:
     - The Resend button calls /resend-reset-otp (not /send-otp)
     - The form submits via regular POST (not AJAX) to verify OTP
     - The page NEVER redirects to /forgot-password on resend

   Timer behavior:
     ┌─ Page loads with OTP already sent
     │    → Start 3-minute expiry countdown
     │    → Start 30-second cooldown (resend button disabled)
     │
     ├─ Cooldown counting (0 → 30 s):
     │    → "Resend OTP available in 30 seconds"
     │    → Resend button DISABLED
     │
     ├─ After cooldown (30 s):
     │    → Cooldown message hidden
     │    → Resend button ENABLED
     │
     ├─ OTP expires (3 minutes):
     │    → Timer hidden, cooldown stopped
     │    → Resend button ENABLED immediately
     │    → "OTP expired. Click Resend OTP."
     │    → Verify button stays enabled (server will reject expired OTP)
     │
     └─ Resend clicked:
          → AJAX to /resend-reset-otp
          → New timers start, stays on same page
════════════════════════════════════════════════════════════ */

(function initVerifyResetOtpPage() {

  // Only run on the verify-reset-otp page
  const pageElement = document.getElementById('verifyResetOtpPage');
  if (!pageElement) return;

  // ── Grab all UI elements ───────────────────────────────────────────────
  const otpInput       = document.getElementById('reset_otp_input');
  const verifyForm     = document.getElementById('verifyResetOtpForm');
  const verifyBtn      = document.getElementById('verifyResetOtpBtn');

  const timerWrap      = document.getElementById('resetTimerWrap');
  const timerText      = document.getElementById('resetTimerText');     // "OTP expires in MM:SS"

  const resendSection  = document.getElementById('resetResendSection');
  const cooldownText   = document.getElementById('resetCooldownText');  // "Resend OTP available in Xs"
  const resendBtn      = document.getElementById('resetResendBtn');

  const statusDiv      = document.getElementById('resetOtpStatus');     // feedback messages

  // ── Read timestamps from server (passed via data-* attributes) ─────────
  // These allow timers to resume correctly even after a page refresh
  let expiryTimestamp = parseFloat(pageElement.dataset.expiryTs || '0');
  let sentTimestamp   = parseFloat(pageElement.dataset.sentTs   || '0');
  const COOLDOWN_SECS = parseInt(pageElement.dataset.cooldown   || '30', 10);

  // Timer interval IDs (stored so we can clearInterval() them)
  let expiryTimer   = null;
  let cooldownTimer = null;


  // ── HELPER: Show a coloured status message ─────────────────────────────
  function showStatus(message, type) {
    statusDiv.textContent   = message;
    statusDiv.className     = 'flash ' + type;
    statusDiv.style.display = 'flex';
  }


  // ── HELPER: Start (or restart) the 3-minute OTP expiry countdown ───────
  //
  // When timer reaches 0:
  //   - Stops both timers
  //   - Hides expiry countdown
  //   - Hides cooldown message
  //   - Enables Resend button immediately
  //   - Shows "OTP expired. Click Resend OTP."
  //
  function startExpiryCountdown(newExpiryTs) {
    expiryTimestamp = newExpiryTs;
    clearInterval(expiryTimer);

    // Show the timer
    timerWrap.style.display = 'block';

    expiryTimer = setInterval(function () {
      const nowSecs     = Math.floor(Date.now() / 1000);
      const secondsLeft = Math.max(0, Math.floor(expiryTimestamp - nowSecs));

      timerText.textContent = 'OTP expires in ' + formatTime(secondsLeft);

      if (secondsLeft <= 0) {
        // ── OTP expired ─────────────────────────────────────────────

        // Stop both timers
        clearInterval(expiryTimer);
        clearInterval(cooldownTimer);

        // Hide countdown and cooldown message
        timerWrap.style.display    = 'none';
        cooldownText.style.display = 'none';

        // Enable Resend button immediately
        resendBtn.disabled = false;

        // Show expiry message
        showStatus('OTP expired. Click Resend OTP.', 'warning');
      }
    }, 1000);
  }


  // ── HELPER: Start (or restart) the 30-second resend cooldown ──────────
  //
  // Shows "Resend OTP available in 30 seconds" counting down.
  // Enables Resend button when it reaches 0.
  //
  function startResendCooldown(newSentTs) {
    sentTimestamp = newSentTs;
    clearInterval(cooldownTimer);

    // Disable resend button while cooling down
    resendBtn.disabled = true;

    cooldownTimer = setInterval(function () {
      const nowSecs     = Math.floor(Date.now() / 1000);
      const elapsed     = nowSecs - Math.floor(sentTimestamp);
      const secondsLeft = Math.max(0, COOLDOWN_SECS - elapsed);

      if (secondsLeft > 0) {
        cooldownText.style.display = 'block';
        cooldownText.textContent   =
          'Resend OTP available in ' + secondsLeft +
          ' second' + (secondsLeft !== 1 ? 's' : '');
        resendBtn.disabled = true;

      } else {
        // Cooldown over — enable resend button
        clearInterval(cooldownTimer);
        cooldownText.style.display = 'none';
        resendBtn.disabled = false;
      }
    }, 1000);
  }


  // ── Auto-start timers on page load ────────────────────────────────────
  //
  // The server always sends an OTP before redirecting here, so
  // expiryTimestamp should always be > 0 on first load.
  //
  if (expiryTimestamp > 0) {
    startExpiryCountdown(expiryTimestamp);
    startResendCooldown(sentTimestamp);
  }


  // ── EVENT: "Resend OTP" button clicked ────────────────────────────────
  //
  // IMPORTANT: This uses AJAX (fetch). The page does NOT redirect.
  // The server endpoint is /resend-reset-otp.
  //
  resendBtn.addEventListener('click', async function () {

    resendBtn.disabled    = true;
    resendBtn.textContent = 'Sending…';

    try {
      // Call the dedicated resend endpoint — stays on this page
      const response = await fetch('/resend-reset-otp', {
        method: 'POST',
        headers: {
          'X-CSRFToken': document.querySelector('[name=csrf_token]').value
        }
      });

      const result = await response.json();

      if (result.success) {
        // New OTP sent — clear input, restart timers
        showStatus(result.message, 'success');
        otpInput.value = '';
        otpInput.focus();

        // Restart both timers with fresh server timestamps
        startExpiryCountdown(result.expiry_ts);
        startResendCooldown(result.sent_ts);

      } else {
        // Server rejected resend (e.g. cooldown still active server-side)
        showStatus(result.message, 'warning');
        resendBtn.disabled = false;
      }

    } catch (networkError) {
      showStatus('Network error. Please try again.', 'error');
      resendBtn.disabled = false;
    }

    resendBtn.textContent = '↺ Resend OTP';
  });


  // ── INPUT: OTP field — digits only, max 6 ─────────────────────────────
  otpInput.addEventListener('input', function () {
    otpInput.value = otpInput.value.replace(/\D/g, '').slice(0, 6);
  });


  // ── FORM SUBMIT: validate OTP input + disable button ──────────────────
  //
  // The form submits via regular POST (not AJAX) because the server needs
  // to set a session flag (fp_otp_verified) and redirect to /reset-password.
  //
  verifyForm.addEventListener('submit', function (event) {
    const enteredOtp = otpInput.value.trim();

    if (!enteredOtp || !/^\d{6}$/.test(enteredOtp)) {
      event.preventDefault();
      showStatus('Please enter the 6-digit OTP.', 'error');
      return;
    }

    // Disable button to prevent double-submission
    verifyBtn.disabled = true;
    verifyBtn.classList.add('loading');
  });

})(); // End of Section 6
