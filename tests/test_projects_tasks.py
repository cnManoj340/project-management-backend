from datetime import date, timedelta

from tests.conftest import API


def _task(client, h, project_id, **kw):
    body = {"title": "Design homepage", "project_id": project_id, **kw}
    return client.post(f"{API}/tasks", headers=h, json=body)


def test_project_visibility_and_crud(client, admin, pm, member, project):
    _, pm_h = pm
    _, member_h = member
    pid = project["id"]
    assert len(project["members"]) == 2
    assert client.get(f"{API}/projects/{pid}", headers=member_h).status_code == 200
    # a member cannot edit or delete
    assert client.patch(f"{API}/projects/{pid}", headers=member_h, json={"name": "Hack"}).status_code == 403
    assert client.delete(f"{API}/projects/{pid}", headers=member_h).status_code == 403
    # an outsider cannot see it
    client.post(f"{API}/auth/register", json={
        "email": "o@mail.com", "username": "outsider", "full_name": "O", "password": "Passw0rd1"})
    from tests.conftest import login
    out_h = login(client, "outsider", "Passw0rd1")
    assert client.get(f"{API}/projects/{pid}", headers=out_h).status_code == 403
    assert client.get(f"{API}/projects", headers=out_h).json()["total"] == 0
    # owner can edit; bad dates rejected
    assert client.patch(f"{API}/projects/{pid}", headers=pm_h, json={"name": "Renamed"}).json()["name"] == "Renamed"
    bad = client.patch(f"{API}/projects/{pid}", headers=pm_h,
                       json={"start_date": "2030-01-10", "end_date": "2030-01-01"})
    assert bad.status_code == 400
    assert client.delete(f"{API}/projects/{pid}", headers=pm_h).status_code == 204
    assert client.get(f"{API}/projects/{pid}", headers=admin).status_code == 404


def test_task_lifecycle_progress_and_stats(client, pm, member, project):
    _, pm_h = pm
    member_id, member_h = member
    pid = project["id"]
    t1 = _task(client, pm_h, pid, assignee_id=member_id, priority="high").json()
    t2 = _task(client, pm_h, pid, title="Write copy", priority="low").json()
    assert t1["status"] == "todo" and t1["assignee"]["username"] == "member"
    # member can move own task, but not edit other fields or other tasks
    assert client.patch(f"{API}/tasks/{t1['id']}/status", headers=member_h,
                        json={"status": "completed"}).json()["status"] == "completed"
    assert client.patch(f"{API}/tasks/{t1['id']}", headers=member_h, json={"priority": "low"}).status_code == 403
    assert client.patch(f"{API}/tasks/{t2['id']}/status", headers=member_h,
                        json={"status": "review"}).status_code == 403
    # progress = 1 of 2 completed
    p = client.get(f"{API}/projects/{pid}", headers=pm_h).json()
    assert p["total_tasks"] == 2 and p["progress"] == 50.0
    s = client.get(f"{API}/projects/{pid}/stats", headers=pm_h).json()
    assert s["by_status"]["completed"] == 1 and s["by_priority"]["high"] == 1
    # members cannot create or delete tasks
    assert _task(client, member_h, pid).status_code == 403
    assert client.delete(f"{API}/tasks/{t2['id']}", headers=member_h).status_code == 403
    assert client.delete(f"{API}/tasks/{t2['id']}", headers=pm_h).status_code == 204


def test_task_validation(client, pm, project, admin):
    _, pm_h = pm
    pid = project["id"]
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    r = _task(client, pm_h, pid, due_date=yesterday)
    assert r.status_code == 400 and "past" in r.json()["error"]["message"]
    # assignee that is not a project member
    other = client.post(f"{API}/users", headers=admin, json={
        "email": "z@mail.com", "username": "zed", "full_name": "Z", "password": "Passw0rd1"}).json()
    assert _task(client, pm_h, pid, assignee_id=other["id"]).status_code == 400
    assert _task(client, pm_h, pid, priority="urgent").status_code == 422
    assert _task(client, pm_h, 9999).status_code == 404


def test_filters_search_sort_pagination(client, pm, project):
    _, pm_h = pm
    pid = project["id"]
    today = date.today()
    for i, (title, prio, days) in enumerate([("Alpha bug", "critical", 5), ("Beta feature", "low", 2),
                                              ("Gamma bug", "high", 9)]):
        r = _task(client, pm_h, pid, title=title, priority=prio,
                  due_date=(today + timedelta(days=days)).isoformat())
        assert r.status_code == 201, r.text
    q = lambda qs: client.get(f"{API}/tasks?{qs}", headers=pm_h).json()
    assert q("search=bug")["total"] == 2
    assert q("priority=critical")["total"] == 1
    assert q("status=completed")["total"] == 0
    titles = [t["title"] for t in q("sort_by=due_date&order=asc")["items"]]
    assert titles == ["Beta feature", "Alpha bug", "Gamma bug"]
    page = q("size=2&page=2")
    assert page["total"] == 3 and page["pages"] == 2 and len(page["items"]) == 1


def test_my_tasks_comments_activity_dashboard(client, pm, member, project):
    _, pm_h = pm
    member_id, member_h = member
    pid = project["id"]
    t = _task(client, pm_h, pid, assignee_id=member_id).json()
    _task(client, pm_h, pid, title="Unassigned task")
    mine = client.get(f"{API}/tasks/me", headers=member_h).json()
    assert mine["total"] == 1 and mine["items"][0]["id"] == t["id"]

    c = client.post(f"{API}/tasks/{t['id']}/comments", headers=member_h, json={"content": "On it!"})
    assert c.status_code == 201 and c.json()["user"]["username"] == "member"
    assert client.get(f"{API}/tasks/{t['id']}/comments", headers=pm_h).json()["total"] == 1
    assert client.post(f"{API}/tasks/{t['id']}/comments", headers=pm_h, json={"content": ""}).status_code == 422

    client.patch(f"{API}/tasks/{t['id']}", headers=pm_h, json={"status": "in_progress", "priority": "critical"})
    actions = [a["action"] for a in client.get(f"{API}/tasks/{t['id']}/activity", headers=pm_h).json()["items"]]
    assert "created" in actions and "updated" in actions and "added" in actions

    d = client.get(f"{API}/dashboard", headers=pm_h).json()
    assert d["total_projects"] == 1 and d["total_tasks"] == 2
    assert d["in_progress_tasks"] == 1 and d["pending_tasks"] == 1
    assert len(d["recent_activities"]) > 0
