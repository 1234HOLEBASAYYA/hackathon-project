import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.api import app

client = TestClient(app)

@pytest.fixture
def mock_users_col():
    """Fixture to mock MongoDB users collection calls."""
    with patch("src.auth_routes.get_users_collection") as mock_get:
        col = AsyncMock()
        mock_get.return_value = col
        yield col

def test_register_success(mock_users_col) -> None:
    """Test successful user registration."""
    mock_users_col.find_one.return_value = None
    mock_users_col.insert_one.return_value = AsyncMock()

    response = client.post(
        "/auth/register",
        json={"name": "Dr. Test", "email": "test@doctor.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    mock_users_col.find_one.assert_called_once_with({"email": "test@doctor.com"})
    assert mock_users_col.insert_one.called

def test_register_duplicate_email(mock_users_col) -> None:
    """Test user registration duplicate email rejection."""
    mock_users_col.find_one.return_value = {"email": "test@doctor.com"}
    
    response = client.post(
        "/auth/register",
        json={"name": "Dr. Test", "email": "test@doctor.com", "password": "password123"}
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_login_success(mock_users_col) -> None:
    """Test successful user login."""
    from src.auth import get_password_hash
    hashed = get_password_hash("password123")
    mock_users_col.find_one.return_value = {
        "name": "Dr. Test",
        "email": "test@doctor.com",
        "password_hash": hashed
    }
    
    response = client.post(
        "/auth/login",
        json={"email": "test@doctor.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(mock_users_col) -> None:
    """Test user login wrong password rejection."""
    from src.auth import get_password_hash
    hashed = get_password_hash("password123")
    mock_users_col.find_one.return_value = {
        "name": "Dr. Test",
        "email": "test@doctor.com",
        "password_hash": hashed
    }
    
    response = client.post(
        "/auth/login",
        json={"email": "test@doctor.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()

def test_protected_route_without_token() -> None:
    """Test access rejection for protected routes without a token."""
    response = client.get("/history")
    assert response.status_code == 403
    assert "not authenticated" in response.json()["detail"].lower()
