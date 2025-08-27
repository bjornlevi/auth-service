import pytest

def login_admin(client):
    return client.post("/login", data={
        "username": "admin",
        "password": "adminpass"
    }, follow_redirects=True)


def test_add_user(client):
    login_admin(client)
    res = client.post("/users/add", data={
        "username": "bob",
        "email": "bob@example.com",
        "password": "secret",
        "confirm_password": "secret",
        "is_admin": "on"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"User bob created" in res.data


def test_delete_user(client):
    login_admin(client)
    # Add user first
    client.post("/users/add", data={
        "username": "alice",
        "email": "alice@example.com",
        "password": "123",
        "confirm_password": "123"
    }, follow_redirects=True)

    # Delete user (should be id=2, since admin is id=1)
    res = client.post("/users/delete/2", follow_redirects=True)
    assert res.status_code == 200


def test_toggle_admin(client):
    login_admin(client)
    client.post("/users/add", data={
        "username": "joe",
        "password": "123",
        "confirm_password": "123"
    }, follow_redirects=True)

    res = client.post("/users/toggle/2", follow_redirects=True)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["username"] == "joe"
    assert "is_admin" in data


def test_reset_password(client):
    login_admin(client)
    client.post("/users/add", data={
        "username": "eve",
        "password": "oldpass",
        "confirm_password": "oldpass"
    }, follow_redirects=True)

    res = client.post("/users/reset/2")
    token = res.get_json()["reset_url"].split("/")[-1]

    # Reset with new password
    res = client.post(f"/reset/{token}", data={
        "password": "newpass",
        "confirm_password": "newpass"
    }, follow_redirects=True)
    assert b"Password updated" in res.data
