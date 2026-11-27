"""Authentication and authorisation."""

from __future__ import annotations


def test_signup_returns_token_and_user_role(client):
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Parag",
            "email": "parag@example.com",
            "password": "correct-horse-7",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "user"
    assert body["access_token"]


def test_signup_cannot_self_assign_admin(client):
    """The role field is ignored even when supplied."""
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Mallory",
            "email": "mallory@example.com",
            "password": "correct-horse-7",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"


def test_weak_password_rejected(client):
    response = client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "a@example.com", "password": "password"},
    )
    assert response.status_code == 422


def test_duplicate_email_conflicts(client):
    payload = {
        "name": "A",
        "email": "dupe@example.com",
        "password": "correct-horse-7",
    }
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    assert client.post("/api/auth/signup", json=payload).status_code == 409


def test_login_rejects_wrong_password(client):
    client.post(
        "/api/auth/signup",
        json={
            "name": "A",
            "email": "login@example.com",
            "password": "correct-horse-7",
        },
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "wrong-horse-7"},
    )
    assert response.status_code == 401


def test_login_does_not_reveal_whether_account_exists(client):
    missing = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "correct-horse-7"},
    )
    client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "real@example.com", "password": "correct-horse-7"},
    )
    wrong = client.post(
        "/api/auth/login",
        json={"email": "real@example.com", "password": "nope-nope-77"},
    )
    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]


def test_passwords_are_not_stored_in_recoverable_form(client):
    import hashlib

    from app.config import get_settings
    from app.db import Database

    secret = "correct-horse-7"
    client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "hash@example.com", "password": secret},
    )
    db = Database(get_settings().sqlite_path)
    with db.connect() as connection:
        stored = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("hash@example.com",)
        ).fetchone()["password_hash"]

    assert secret not in stored
    # The old scheme would have produced exactly this value.
    assert stored != hashlib.sha256(secret.encode()).hexdigest()
    assert stored.startswith("$2")


def test_admin_route_requires_token(client):
    response = client.post(
        "/api/products",
        json={"name": "X", "sku": "X1", "category": "phone", "price": 1.0},
    )
    assert response.status_code == 401


def test_admin_route_rejects_plain_user(client):
    signup = client.post(
        "/api/auth/signup",
        json={"name": "A", "email": "plain@example.com", "password": "correct-horse-7"},
    ).json()
    response = client.post(
        "/api/products",
        json={"name": "X", "sku": "X1", "category": "phone", "price": 1.0},
        headers={"Authorization": f"Bearer {signup['access_token']}"},
    )
    assert response.status_code == 403


def test_admin_route_accepts_admin(client, admin_token):
    response = client.post(
        "/api/products",
        json={"name": "X", "sku": "X1", "category": "phone", "price": 1.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
