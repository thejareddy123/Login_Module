"""
app.py
------
This is the main entry point of the Flask application.

Its ONLY job is to:
  1. Create the Flask app
  2. Load configuration
  3. Set up extensions (database, mail, CSRF)
  4. Register the Blueprint (routes)
  5. Initialize the database table
  6. Run the development server

A fresher tip:
  app.py should be SHORT and clean. All routes go in blueprints/,
  all logic goes in services/, all DB code goes in models.py.
  This file just wires everything together.
"""

from flask import Flask
from flask_mail import Mail
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import init_db
from blueprints.auth_routes import auth_bp


# ─────────────────────────────────────────────────────────────
# 1. CREATE THE FLASK APP
# ─────────────────────────────────────────────────────────────
app = Flask(__name__)

# Load all settings from config.py
app.config.from_object(Config)


# ─────────────────────────────────────────────────────────────
# 2. SET UP EXTENSIONS
# ─────────────────────────────────────────────────────────────

# MySQL — connects Flask to the MySQL database
mysql = MySQL(app)

# Flask-Mail — allows the app to send emails
mail = Mail(app)

# CSRFProtect — automatically adds CSRF protection to all forms
# This prevents Cross-Site Request Forgery attacks
csrf = CSRFProtect(app)

# Make extensions accessible inside blueprints via current_app.extensions
# Flask-WTF registers 'csrf', but MySQL and Mail need manual registration
app.extensions['mysql'] = mysql
app.extensions['mail']  = mail


# ─────────────────────────────────────────────────────────────
# 3. REGISTER THE BLUEPRINT
# ─────────────────────────────────────────────────────────────

# This adds all the routes defined in blueprints/auth_routes.py to the app
app.register_blueprint(auth_bp)


# ─────────────────────────────────────────────────────────────
# 4. INITIALIZE THE DATABASE TABLE
# ─────────────────────────────────────────────────────────────

with app.app_context():
    try:
        init_db(mysql)
        print("[INFO] Database table checked/created successfully.")
    except Exception as error:
        print(f"[WARN] Could not initialize database: {error}")
        print("[WARN] Please check your MySQL credentials in .env")


# ─────────────────────────────────────────────────────────────
# 5. RUN THE SERVER
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # debug=True shows detailed error pages and auto-reloads on code changes
    # NEVER use debug=True in production!
    app.run(debug=True)
