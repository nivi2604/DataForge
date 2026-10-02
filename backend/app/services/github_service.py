import base64
import json
import httpx
from fastapi import HTTPException, status
from app.repositories.github_repository import GithubConnectionRepository
from app.models.github_connection import GithubConnection
from app.schemas.github import (
    GithubConnectionCreate, GithubConnectionResponse, GithubBranch,
    GithubCommit, GithubPullRequest, GithubPullRequestCreate, GithubCommitCreate
)
from app.core.encryption import encrypt_value, decrypt_value

class GithubService:
    def __init__(self):
        self.repo = GithubConnectionRepository()
        
    def _get_client(self, token: str) -> httpx.Client:
        return httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            timeout=10.0
        )
        
    def create_connection(self, user_id: str, payload: GithubConnectionCreate) -> GithubConnectionResponse:
        # Validate connection
        try:
            with self._get_client(payload.token) as client:
                res = client.get(f"/repos/{payload.repository_name}")
                if res.status_code in [401, 403]:
                    raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
                elif res.status_code != 200:
                    raise HTTPException(status_code=400, detail="Invalid repository or token")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to communicate with GitHub")
            
        conn = GithubConnection(
            user_id=user_id,
            repository_name=payload.repository_name,
            encrypted_token=encrypt_value(payload.token)
        )
        saved = self.repo.create_connection(conn)
        return GithubConnectionResponse(
            id=saved.id,
            repository_name=saved.repository_name,
            created_at=saved.created_at
        )
        
    def list_connections(self, user_id: str) -> list[GithubConnectionResponse]:
        conns = self.repo.get_connections_for_user(user_id)
        return [
            GithubConnectionResponse(
                id=c.id,
                repository_name=c.repository_name,
                created_at=c.created_at
            ) for c in conns
        ]
        
    def get_connection_model(self, user_id: str, connection_id: str) -> GithubConnection:
        conn = self.repo.get_connection(connection_id)
        if not conn or conn.user_id != user_id:
            raise HTTPException(status_code=404, detail="Connection not found")
        return conn

    def delete_connection(self, user_id: str, connection_id: str):
        self.get_connection_model(user_id, connection_id)
        self.repo.delete_connection(connection_id)
        
    def get_branches(self, user_id: str, connection_id: str) -> list[GithubBranch]:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.get(f"/repos/{conn.repository_name}/branches")
            if res.status_code == 200:
                return [GithubBranch(name=b["name"]) for b in res.json()]
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail="Failed to fetch branches")

    def create_branch(self, user_id: str, connection_id: str, new_branch: str, base_branch: str) -> GithubBranch:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            # get base ref
            res = client.get(f"/repos/{conn.repository_name}/git/refs/heads/{base_branch}")
            if res.status_code != 200:
                raise HTTPException(status_code=400, detail="Base branch not found")
            sha = res.json()["object"]["sha"]
            
            # create new ref
            res = client.post(
                f"/repos/{conn.repository_name}/git/refs",
                json={"ref": f"refs/heads/{new_branch}", "sha": sha}
            )
            if res.status_code == 201:
                return GithubBranch(name=new_branch)
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail="Failed to create branch")

    def create_commit(self, user_id: str, connection_id: str, payload: GithubCommitCreate) -> GithubCommit:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            # 1. get current file sha if exists
            sha = None
            res = client.get(f"/repos/{conn.repository_name}/contents/{payload.file_path}?ref={payload.branch}")
            if res.status_code == 200:
                sha = res.json()["sha"]
                
            # 2. update file
            content_str = payload.content if isinstance(payload.content, str) else json.dumps(payload.content, indent=2)
            content_b64 = base64.b64encode(content_str.encode()).decode()
            
            data = {
                "message": payload.message,
                "content": content_b64,
                "branch": payload.branch
            }
            if sha:
                data["sha"] = sha
                
            res = client.put(f"/repos/{conn.repository_name}/contents/{payload.file_path}", json=data)
            if res.status_code in [200, 201]:
                commit_info = res.json()["commit"]
                return GithubCommit(
                    sha=commit_info["sha"],
                    message=commit_info["message"],
                    url=commit_info["html_url"]
                )
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail=f"Failed to create commit: {res.text}")

    def list_pull_requests(self, user_id: str, connection_id: str) -> list[GithubPullRequest]:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.get(f"/repos/{conn.repository_name}/pulls?state=all")
            if res.status_code == 200:
                prs = []
                for pr in res.json():
                    prs.append(GithubPullRequest(
                        number=pr["number"],
                        title=pr["title"],
                        state=pr["state"],
                        html_url=pr["html_url"],
                        head_branch=pr["head"]["ref"],
                        base_branch=pr["base"]["ref"],
                        author=pr["user"]["login"] if pr.get("user") else None
                    ))
                return prs
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail="Failed to fetch PRs")

    def create_pull_request(self, user_id: str, connection_id: str, payload: GithubPullRequestCreate) -> GithubPullRequest:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.post(
                f"/repos/{conn.repository_name}/pulls",
                json={
                    "title": payload.title,
                    "head": payload.head,
                    "base": payload.base,
                    "body": payload.body
                }
            )
            if res.status_code == 201:
                pr = res.json()
                return GithubPullRequest(
                    number=pr["number"],
                    title=pr["title"],
                    state=pr["state"],
                    html_url=pr["html_url"],
                    head_branch=pr["head"]["ref"],
                    base_branch=pr["base"]["ref"],
                    author=pr["user"]["login"] if pr.get("user") else None
                )
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail=f"Failed to create PR: {res.text}")

    def merge_pull_request(self, user_id: str, connection_id: str, pr_number: int):
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.put(f"/repos/{conn.repository_name}/pulls/{pr_number}/merge")
            if res.status_code not in [200, 201]:
                if res.status_code in [401, 403]:
                    raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
                raise HTTPException(status_code=res.status_code, detail="Failed to merge PR")
                
    def close_pull_request(self, user_id: str, connection_id: str, pr_number: int):
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.patch(
                f"/repos/{conn.repository_name}/pulls/{pr_number}",
                json={"state": "closed"}
            )
            if res.status_code not in [200, 201]:
                if res.status_code in [401, 403]:
                    raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
                raise HTTPException(status_code=res.status_code, detail="Failed to close PR")

    def fetch_file_content(self, user_id: str, connection_id: str, file_path: str, branch: str) -> str:
        conn = self.get_connection_model(user_id, connection_id)
        token = decrypt_value(conn.encrypted_token)
        with self._get_client(token) as client:
            res = client.get(f"/repos/{conn.repository_name}/contents/{file_path}?ref={branch}")
            if res.status_code == 200:
                data = res.json()
                if data.get("encoding") == "base64":
                    return base64.b64decode(data["content"]).decode('utf-8')
                return data.get("content", "")
            if res.status_code in [401, 403]:
                raise HTTPException(status_code=400, detail="GitHub authentication failed. Please update your token.")
            raise HTTPException(status_code=res.status_code, detail=f"Failed to fetch file: {res.text}")

