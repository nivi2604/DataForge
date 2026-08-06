from dataclasses import dataclass


@dataclass
class LoginRequest:
    email: str
    password: str


@dataclass
class RegisterRequest:
    first_name: str
    last_name: str
    email: str
    password: str


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
