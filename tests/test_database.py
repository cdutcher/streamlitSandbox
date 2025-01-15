import pytest
from database import UserDB, User

def test_add_user():
    db = UserDB()
    username = "testuser"
    email = "test@example.com"
    name = "Test User"
    password = "testpass123"
    
    # Test user creation
    assert db.add_user(username, email, name, password)
    
    # Test user retrieval
    user = db.get_user(username)
    assert user is not None
    assert user.email == email
    assert user.name == name

def test_validate_signup():
    db = UserDB()
    
    # Test invalid email
    with pytest.raises(ValueError, match="Invalid email format"):
        db.validate_signup("user", "invalid-email", "password")
    
    # Test short password
    with pytest.raises(ValueError, match="Password must be at least 6 characters"):
        db.validate_signup("user", "test@example.com", "short") 