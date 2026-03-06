# SecureAuth — Flask Authentication System

A complete, beginner-friendly authentication system built with Flask + MySQL.

---

## Project Structure

```
/project
├── app.py                      ← Entry point: wires everything together
├── config.py                   ← All settings (reads from .env)
├── models.py                   ← Database table + query helpers
├── requirements.txt
├── .env.example                ← Copy to .env and fill in your values
│
├── /blueprints
│   └── auth_routes.py          ← All URL routes (thin — just handles requests)
│
├── /services
│   └── auth_service.py         ← All business logic (validations, OTP, etc.)
│
├── /utils
│   ├── otp_utils.py            ← OTP generation, hashing, expiry helpers
│   └── email_utils.py          ← Email sending functions
│
├── /static
│   ├── /css/style.css          ← Dark gold theme
│   └── /js/auth.js             ← Frontend validation + OTP timer
│
└── /templates
    ├── base.html
    ├── register.html
    ├── verify.html
    ├── login.html
    ├── forgot_password.html
    ├── verify_reset_otp.html
    ├── reset_password.html
    └── dashboard.html
```

---

## Quick Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create the MySQL database

```sql
CREATE DATABASE auth_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

The `users` table is created automatically when the app first starts.

### 3. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in your MySQL credentials and Gmail App Password
```

### 4. Run the app

```bash
python app.py
```

Visit: **http://127.0.0.1:5000**

---

## Registration Flow

```
/register  →  /verify (Send OTP → Verify OTP)  →  /login
```

## Password Reset Flow

```
/forgot-password  →  /verify-reset-otp  →  /reset-password  →  /login
```

---

## Key Features

| Feature | Details |
|---|---|
| Phone validation | India only (+91), 10 digits, starts with 6/7/8/9 |
| OTP expiry | 5 minutes |
| Resend cooldown | 30 seconds |
| Password hashing | bcrypt with auto-generated salt |
| OTP storage | SHA-256 hashed — never stored in plain text |
| CSRF protection | Flask-WTF on every form |
| Login security | Generic errors, 5-attempt lockout |
| Forgot password | Never reveals if email exists |

---

## Architecture

- **app.py** — creates Flask app, registers extensions and blueprint
- **blueprints/auth_routes.py** — handles HTTP requests and responses only
- **services/auth_service.py** — all business logic and validation rules
- **utils/otp_utils.py** — OTP helpers (generate, hash, check expiry)
- **utils/email_utils.py** — email sending functions
- **models.py** — database queries only
