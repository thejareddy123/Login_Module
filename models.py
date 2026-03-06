"""
models.py
---------
This file is responsible for:
  1. Creating the database table when the app starts (init_db)
  2. Providing simple helper functions to read/write data

Think of this file as the "data layer" — it only talks to the database.
All business logic lives in the services/ folder.

A fresher tip:
  Each function here does ONE thing — query or update the database.
  This makes it easy to test and reuse.
"""


def init_db(mysql):
    """
    Creates the 'users' table if it does not already exist.
    Called once when the Flask app starts.
    """
    cursor = mysql.connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            first_name    VARCHAR(50)  NOT NULL,
            last_name     VARCHAR(50)  NOT NULL,
            age           TINYINT UNSIGNED NOT NULL,
            gender        VARCHAR(20)  NOT NULL,
            address       TEXT         NOT NULL,
            aadhar_number VARCHAR(12)  NOT NULL UNIQUE,
            email         VARCHAR(255) NOT NULL UNIQUE,
            phone_number  VARCHAR(15)  NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    mysql.connection.commit()
    cursor.close()


# ─────────────────────────────────────────────────────────────
# READ HELPERS
# ─────────────────────────────────────────────────────────────

def find_user_by_email(mysql, email):
    """
    Look up a user by their email address.
    Returns the user row as a dictionary, or None if not found.
    """
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email.strip().lower(),)
    )
    user = cursor.fetchone()   # fetchone() returns one row or None
    cursor.close()
    return user


def find_user_by_id(mysql, user_id):
    """
    Look up a user by their database ID.
    Returns the user row as a dictionary, or None if not found.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user


# ─────────────────────────────────────────────────────────────
# UNIQUENESS CHECK HELPERS
# Each returns True if the value already exists in the database.
# ─────────────────────────────────────────────────────────────

def email_exists(mysql, email):
    """Returns True if this email is already registered."""
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email.strip().lower(),)
    )
    result = cursor.fetchone()
    cursor.close()
    return result is not None    # True if a row was found


def aadhar_exists(mysql, aadhar):
    """Returns True if this Aadhar number is already registered."""
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE aadhar_number = %s",
        (aadhar,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result is not None


def phone_exists(mysql, phone):
    """Returns True if this phone number is already registered."""
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT id FROM users WHERE phone_number = %s",
        (phone,)
    )
    result = cursor.fetchone()
    cursor.close()
    return result is not None


# ─────────────────────────────────────────────────────────────
# WRITE HELPERS
# ─────────────────────────────────────────────────────────────

def insert_user(mysql, data):
    """
    Insert a new verified user into the database.

    Parameters:
        data (dict): A dictionary containing all user fields.

    Returns:
        int: The ID of the newly created user.
    """
    cursor = mysql.connection.cursor()

    cursor.execute("""
        INSERT INTO users
            (first_name, last_name, age, gender, address,
             aadhar_number, email, phone_number, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data['first_name'],
        data['last_name'],
        data['age'],
        data['gender'],
        data['address'],
        data['aadhar_number'],
        data['email'],
        data['phone_number'],
        data['password_hash'],
    ))

    mysql.connection.commit()      # Save the change to the database
    new_id = cursor.lastrowid      # Get the auto-generated ID
    cursor.close()
    return new_id


def update_password(mysql, email, new_hash):
    """
    Update the password hash for a user identified by email.
    Used after a successful password reset.
    """
    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s",
        (new_hash, email.strip().lower())
    )
    mysql.connection.commit()
    cursor.close()
