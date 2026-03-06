from services.auth_service import hash_password
import bcrypt

def test_hash_password():
    password = "Test123"
    hashed = hash_password(password)

    # bcrypt should verify the password matches the hash
    result = bcrypt.checkpw(password.encode(), hashed.encode())

    assert result is True



