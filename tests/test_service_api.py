import pytest

def login_admin(client):
    return client.post("/login", data={
        "username": "admin",
        "password": "adminpass"
    }, follow_redirects=True)


def test_add_service_api_key(client):
    login_admin(client)
    res = client.post("/apikeys/add", data={"description": "new site"}, follow_redirects=True)
    assert res.status_code == 200


def test_delete_service_api_key(client):
    login_admin(client)
    # Add key first
    client.post("/apikeys/add", data={"description": "delete me"}, follow_redirects=True)
    # ServiceApiKey id=2 (since conftest seeds id=1)
    res = client.post("/apikeys/delete/2", follow_redirects=True)
    assert res.status_code == 200
