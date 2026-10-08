from app.core.security import hash_password, verify_password


def test_password_hash():
    h = hash_password("StrongPassword123!")
    assert h != "StrongPassword123!"
    assert verify_password("StrongPassword123!", h)
    assert not verify_password("wrong", h)
