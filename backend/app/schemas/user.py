from dataclasses import dataclass


@dataclass
class UserCreate:
    first_name: str
    last_name: str
    email: str
    password_hash: str
    avatar: str | None = None
    status: str | None = None


@dataclass
class UserUpdate:
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password_hash: str | None = None
    avatar: str | None = None
    status: str | None = None


@dataclass
class UserResponse:
    id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    avatar: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
