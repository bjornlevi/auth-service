import pytest
from app import create_app, db
from app.models import User, ServiceApiKey
from werkzeug.security import generate_password_hash

TEST_API_KEY = "testkey123"

db.session.add(ServiceApiKey(key=TEST_API_KEY, description="test"))

@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/test.db"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"check_same_thread": False}}

    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(ApiKey(key=TEST_API_KEY, description="test"))
        db.session.add(User(username="existing", password=generate_password_hash("pass123")))
        db.session.commit()

    yield app.test_client()


# Test register

def test_register_new_user(client):
    res = client.post("/register",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": "newuser", "password": "newpass"})
    assert res.status_code == 201
    assert res.get_json()["message"] == "User registered"

def test_register_existing_user(client):
    res = client.post("/register",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": "existing", "password": "anything"})
    assert res.status_code == 400

# Test login

def test_login_success(client):
    res = client.post("/login",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": "existing", "password": "pass123"})
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data

def test_login_failure(client):
    res = client.post("/login",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": "existing", "password": "wrong"})
    assert res.status_code == 401

# Test verify

def test_verify_valid_token(client):
    # login first to get token
    login_res = client.post("/login",
                            headers={"x-api-key": TEST_API_KEY},
                            json={"username": "existing", "password": "pass123"})
    token = login_res.get_json()["token"]

    res = client.post("/verify",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": token})
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "existing"

def test_verify_invalid_token(client):
    res = client.post("/verify",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": "badtoken"})
    assert res.status_code == 401

# Test user info

def test_userinfo_valid_token(client):
    # login first to get token
    login_res = client.post("/login",
                            headers={"x-api-key": TEST_API_KEY},
                            json={"username": "existing", "password": "pass123"})
    token = login_res.get_json()["token"]

    res = client.post("/userinfo",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": token})
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "existing"
    assert "created_at" in data

def test_userinfo_invalid_token(client):
    res = client.post("/userinfo",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": "notajwt"})
    assert res.status_code == 401
