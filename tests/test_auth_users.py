from tests.conftest import API, login, make_user


def test_register_login_me(client):
    r = client.post(f"{API}/auth/register", json={
        "email": "a@mail.com", "username": "alice", "full_name": "Alice", "password": "Passw0rd1"})
    assert r.status_code == 201
    assert r.json()["role"]["name"] == "team_member"
    h = login(client, "a@mail.com", "Passw0rd1")
    assert client.get(f"{API}/auth/me", headers=h).json()["username"] == "alice"


def test_duplicate_and_weak_password(client):
    body = {"email": "a@mail.com", "username": "alice", "full_name": "A", "password": "Passw0rd1"}
    assert client.post(f"{API}/auth/register", json=body).status_code == 201
    assert client.post(f"{API}/auth/register", json=body).status_code == 409
    weak = {**body, "email": "b@mail.com", "username": "bob", "password": "short"}
    r = client.post(f"{API}/auth/register", json=weak)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


def test_wrong_password_and_no_token(client):
    r = client.post(f"{API}/auth/login/json", json={"identifier": "admin", "password": "nope12345"})
    assert r.status_code == 401
    assert client.get(f"{API}/auth/me").status_code == 401


def test_rbac_user_management(client, admin, member):
    _, member_h = member
    assert client.get(f"{API}/users", headers=member_h).status_code == 403
    assert client.get(f"{API}/users", headers=admin).status_code == 200
    r = client.post(f"{API}/users", headers=member_h, json={
        "email": "x@mail.com", "username": "xx", "full_name": "X", "password": "Passw0rd1"})
    assert r.status_code == 403


def test_deactivate_user_blocks_login_and_role_change(client, admin, member):
    uid, _ = member
    assert client.patch(f"{API}/users/{uid}/role", headers=admin,
                        json={"role": "project_manager"}).json()["role"]["name"] == "project_manager"
    assert client.patch(f"{API}/users/{uid}/status", headers=admin, json={"is_active": False}).status_code == 200
    r = client.post(f"{API}/auth/login/json", json={"identifier": "member", "password": "Passw0rd123"})
    assert r.status_code == 403


def test_profile_update(client, member):
    _, h = member
    r = client.patch(f"{API}/users/me", headers=h, json={"full_name": "New Name"})
    assert r.json()["full_name"] == "New Name"
    bad = client.patch(f"{API}/users/me", headers=h,
                       json={"current_password": "wrong", "new_password": "Another123"})
    assert bad.status_code == 400
