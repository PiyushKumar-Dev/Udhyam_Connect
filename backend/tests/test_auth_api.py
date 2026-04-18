from __future__ import annotations


def test_auth_me_returns_selected_demo_user(client) -> None:
    response = client.get("/api/auth/me", headers={"X-Demo-User": "admin.demo", "X-User-Role": "admin"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin.demo"
    assert payload["role"] == "admin"


def test_viewer_cannot_access_review_queue(client) -> None:
    response = client.get("/api/matches/pending", headers={"X-Demo-User": "viewer.demo", "X-User-Role": "viewer"})
    assert response.status_code == 403
