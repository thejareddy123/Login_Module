"""
utils/otp_utils.py
------------------
Utility functions related to OTP (One-Time Password) generation,
hashing, and time calculations.

A fresher tip:
  "Utils" means utility — small, reusable helper functions that
  don't belong to any specific feature. We put them here so any
  part of the app can import and use them.
"""

import random
import hashlib
from datetime import datetime, timezone


def get_current_timestamp():
    """
    Returns the current time as a Unix timestamp (float).
    A Unix timestamp is the number of seconds since Jan 1, 1970.
    We use this to calculate OTP expiry and cooldown times.
    """
    return datetime.now(timezone.utc).timestamp()


def generate_otp():
    """
    Generates a random 6-digit OTP (One-Time Password).

    We use SystemRandom() instead of regular random() because
    SystemRandom uses the OS's secure random generator, which
    is harder to predict (more secure).

    Example: returns '483920' or '017364'
    """
    # randint(100000, 999999) gives us a number between 100000 and 999999
    otp = str(random.SystemRandom().randint(100000, 999999))
    return otp


def hash_otp(otp):
    """
    Hashes the OTP using SHA-256 before storing it in the session.

    Why hash it?
      If someone could read the session data, they would see the
      hashed version (a long string of letters/numbers), not the
      actual OTP. So the real OTP stays safe.

    Example:
      Input:  '483920'
      Output: 'a1b2c3d4...' (64-character hex string)
    """
    return hashlib.sha256(otp.encode()).hexdigest()


def is_otp_expired(otp_expiry_timestamp):
    """
    Checks if the OTP has expired by comparing the stored expiry
    timestamp with the current time.

    Parameters:
        otp_expiry_timestamp (float): The Unix timestamp when the OTP expires.

    Returns:
        bool: True if expired, False if still valid.
    """
    current_time = get_current_timestamp()
    return current_time > otp_expiry_timestamp


def is_in_cooldown(last_sent_timestamp, cooldown_seconds):
    """
    Checks if the user is still within the resend cooldown period.

    For example, if the cooldown is 30 seconds and the last OTP was
    sent 15 seconds ago, this returns True (still in cooldown).

    Parameters:
        last_sent_timestamp (float): When the last OTP was sent.
        cooldown_seconds (int): How many seconds the cooldown lasts.

    Returns:
        bool: True if still in cooldown, False if cooldown is over.
    """
    current_time = get_current_timestamp()
    time_passed  = current_time - last_sent_timestamp
    return time_passed < cooldown_seconds


def seconds_remaining_in_cooldown(last_sent_timestamp, cooldown_seconds):
    """
    Returns how many seconds are left in the cooldown period.
    Used to show the user a message like "Please wait 25 seconds".

    Returns:
        int: Seconds remaining (0 if cooldown is already over).
    """
    current_time = get_current_timestamp()
    time_passed  = current_time - last_sent_timestamp
    remaining    = cooldown_seconds - time_passed
    return max(0, int(remaining))    # Never return a negative number
