from __future__ import annotations

import base64
import json
from typing import Callable, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.api.schemas import LoginRequest, UserProfile, UserRole


MOCK_USERS: Dict[str, Dict[str, str]] = {
    "admin": {
        "password": "admin123",
        "display_name": "Admin User",
        "role": UserRole.ADMIN.value,
    },
    "pharmacist": {
        "password": "ops123",
        "display_name": "Pharmacist Ops",
        "role": UserRole.PHARMACIST.value,
    },
    "executive": {
        "password": "exec123",
        "display_name": "Executive User",
        "role": UserRole.EXECUTIVE.value,
    },
}

bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_user(credentials: LoginRequest) -> UserProfile:
    user = MOCK_USERS.get(credentials.username.lower())
    if not user or credentials.password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    return UserProfile(
        username=credentials.username.lower(),
        display_name=user["display_name"],
        role=UserRole(user["role"]),
    )


def create_mock_token(user: UserProfile) -> str:
    payload = {
        "username": user.username,
        "display_name": user.display_name,
        "role": user.role.value,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def parse_mock_token(token: str) -> UserProfile:
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        payload = json.loads(raw.decode("utf-8"))
        username = payload["username"]
        configured = MOCK_USERS[username]
        return UserProfile(
            username=username,
            display_name=payload.get("display_name") or configured["display_name"],
            role=UserRole(payload["role"]),
        )
    except Exception as exc:  # noqa: BLE001 - auth boundary
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserProfile:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )
    return parse_mock_token(credentials.credentials)


def require_roles(*roles: UserRole) -> Callable[[UserProfile], UserProfile]:
    def _dependency(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This role is not allowed to access the requested resource.",
            )
        return user

    return _dependency

