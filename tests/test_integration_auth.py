import bcrypt

from services.auth_service import authenticate_user
from models import insert_user, find_user_by_email


def test_user_registration_and_login(db_mysql):

    # Step 1: create password hash
    password = "Test123!"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Step 2: create test user data
    user_data = {
        "first_name": "Test",
        "last_name": "Theja",
        "age": 23,
        "gender": "Male",
        "address": "Test Address",
        "aadhar_number": "123456789012",
        "email": "testuser@gmail.com",
        "phone_number": "+919876543210",
        "password_hash": hashed
    }

    # Step 3: insert user into DB
    insert_user(db_mysql, user_data)

    # Step 4: try login
    user, error = authenticate_user(db_mysql, "testuser@gmail.com", password)

    # Step 5: verify login works
    assert user is not None
    assert error is None