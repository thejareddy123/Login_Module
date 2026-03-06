from services.auth_service import validate_password


def test_valid_password():
    password = "Test123!"
    result = validate_password(password)

    assert result is None


def test_password_no_uppercase():
    password = "test123!"
    result = validate_password(password)

    assert result == "Password must contain at least one uppercase letter."


def test_password_too_short():
    password = "T1!"
    result = validate_password(password)

    assert result == "Password must be at least 8 characters."


from services.auth_service import validate_indian_phone


def test_valid_phone():
    phone, error = validate_indian_phone("9876543210")

    assert phone == "+919876543210"
    assert error is None


def test_phone_invalid_start():
    phone, error = validate_indian_phone("5876543210")

    assert phone is None
    assert error == "Phone number must start with 6, 7, 8, or 9."


from services.auth_service import validate_age


def test_valid_age():
    age, error = validate_age("25")

    assert age == 25
    assert error is None


def test_invalid_age():
    age, error = validate_age("10")

    assert age is None
    assert error == "Age must be between 18 and 100."