from typing import Any
from pydantic import BaseModel, Field

class GithubConnectionCreate(BaseModel):
    repository_name: str = Field(..., description="Format: owner/repo")
    token: str = Field(..., description="GitHub Personal Access Token")

class GithubConnectionResponse(BaseModel):
    id: str
    repository_name: str
    created_at: str | None = None
    
class GithubBranch(BaseModel):
    name: str

class GithubCommit(BaseModel):
    sha: str
    message: str | None = None
    url: str | None = None

class GithubPullRequest(BaseModel):
    number: int
    title: str
    state: str
    html_url: str
    head_branch: str
    base_branch: str
    author: str | None = None
    
class GithubPullRequestCreate(BaseModel):
    title: str
    head: str
    base: str
    body: str | None = None

class GithubCommitCreate(BaseModel):
    branch: str
    message: str
    content: str | dict | list # The JSON config of the pipeline version
    file_path: str = "pipeline.json"
