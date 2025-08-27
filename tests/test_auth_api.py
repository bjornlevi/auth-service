import pytest

TEST_API_KEY = "testkey123"


def api_login(client, username="admin", password="adminpass"):
    """Helper: perform API login and return a JWT token."""
    res = client.post("/auth/login",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": username, "password": password})
    assert res.status_code == 200
    return res.get_json()["token"]


def test_register_new_user(client):
    res = client.post("/auth/register",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"username": "newuser", "password": "newpass"})
    assert res.status_code == 201
    assert res.get_json()["message"] == "User registered"

    # login with the new user
    login_res = client.post("/auth/login",
                            headers={"x-api-key": TEST_API_KEY},
                            json={"username": "newuser", "password": "newpass"})
    assert login_res.status_code == 200
    token = login_res.get_json()["token"]
    assert token

    # verify token
    verify_res = client.post("/auth/verify",
                             headers={"x-api-key": TEST_API_KEY},
                             json={"token": token})
    assert verify_res.status_code == 200
    assert verify_res.get_json()["username"] == "newuser"

    # get userinfo
    info_res = client.post("/auth/userinfo",
                           headers={"x-api-key": TEST_API_KEY},
                           json={"token": token})
    assert info_res.status_code == 200
    assert info_res.get_json()["username"] == "newuser"
    assert "created_at" in info_res.get_json()


def test_register_duplicate_user(client):
    # First registration succeeds
    res1 = client.post("/auth/register",
                       headers={"x-api-key": TEST_API_KEY},
                       json={"username": "dupe", "password": "pw1"})
    assert res1.status_code == 201

    # Second registration with same username should fail
    res2 = client.post("/auth/register",
                       headers={"x-api-key": TEST_API_KEY},
                       json={"username": "dupe", "password": "pw2"})
    assert res2.status_code == 400
    assert "error" in res2.get_json()

def test_register_duplicate_email(client):
    # First registration with email
    res1 = client.post("/auth/register",
                       headers={"x-api-key": TEST_API_KEY},
                       json={"username": "user1", "password": "pw1", "email": "dupe@example.com"})
    assert res1.status_code == 201

    # Second registration with same email, different username
    res2 = client.post("/auth/register",
                       headers={"x-api-key": TEST_API_KEY},
                       json={"username": "user2", "password": "pw2", "email": "dupe@example.com"})
    assert res2.status_code == 400
    assert "error" in res2.get_json()

def test_login_and_get_token(client):
    token = api_login(client)
    assert token


def test_verify_valid_token(client):
    token = api_login(client)

    res = client.post("/auth/verify",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": token})
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "admin"


def test_verify_invalid_token(client):
    res = client.post("/auth/verify",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": "bogus"})
    assert res.status_code == 401


def test_userinfo(client):
    token = api_login(client)

    res = client.post("/auth/userinfo",
                      headers={"x-api-key": TEST_API_KEY},
                      json={"token": token})
    assert res.status_code == 200
    data = res.get_json()
    assert data["username"] == "admin"
    assert "created_at" in data
