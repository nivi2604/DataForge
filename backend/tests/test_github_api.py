import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def auth_headers():
    # Register and login to get a valid token
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "github_test@example.com",
        "password": "StrongPassword123!",
    }
    client.post("/auth/register", json=payload)
    login_res = client.post("/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_github_connection_flow(auth_headers, monkeypatch):
    # Mock httpx.Client to return success
    class MockResponse:
        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self._json = json_data
            self.text = ""
        def json(self):
            return self._json
            
    class MockClient:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        
        def get(self, url):
            if "/branches" in url:
                return MockResponse(200, [{"name": "main"}])
            elif "/pulls" in url:
                return MockResponse(200, [{"number": 1, "title": "Test PR", "state": "open", "html_url": "url", "head": {"ref": "feat"}, "base": {"ref": "main"}, "user": {"login": "test"}}])
            elif "/git/refs" in url:
                return MockResponse(200, {"object": {"sha": "mocksha123"}})
            elif "/contents/" in url:
                return MockResponse(404, {})
            return MockResponse(200, {})
            
        def post(self, url, json=None):
            if "/pulls" in url:
                return MockResponse(201, {"number": 2, "title": "New PR", "state": "open", "html_url": "url", "head": {"ref": "feat"}, "base": {"ref": "main"}, "user": {"login": "test"}})
            elif "/git/refs" in url:
                return MockResponse(201, {})
            return MockResponse(201, {})
            
        def put(self, url, json=None):
            if "/contents/" in url:
                return MockResponse(201, {"commit": {"sha": "abc1234", "message": "commit", "html_url": "url"}})
            return MockResponse(200, {})
            
    monkeypatch.setattr("app.services.github_service.httpx.Client", MockClient)

    # 1. Create connection
    res = client.post("/github/connections", json={
        "repository_name": "owner/repo",
        "token": "fake_token"
    }, headers=auth_headers)
    assert res.status_code == 201
    conn_id = res.json()["id"]

    # 2. List connections
    res = client.get("/github/connections", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 3. List branches
    res = client.get(f"/github/connections/{conn_id}/branches", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()[0]["name"] == "main"
    
    # 4. Create branch
    res = client.post(f"/github/connections/{conn_id}/branches", json={
        "new_branch": "feat",
        "base_branch": "main"
    }, headers=auth_headers)
    assert res.status_code == 200
    
    # 5. Create commit
    res = client.post(f"/github/connections/{conn_id}/commits", json={
        "branch": "feat",
        "message": "test commit",
        "content": {"test": "data"},
        "file_path": "test.json"
    }, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["sha"] == "abc1234"
    
    # 6. Create PR
    res = client.post(f"/github/connections/{conn_id}/pulls", json={
        "title": "Test PR",
        "head": "feat",
        "base": "main",
        "body": "body"
    }, headers=auth_headers)
    assert res.status_code == 200
    
    # 7. Merge PR
    res = client.post(f"/github/connections/{conn_id}/pulls/2/merge", headers=auth_headers)
    assert res.status_code == 200
