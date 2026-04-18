from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException


@dataclass(frozen=True, slots=True)
class AuthUser:
    username: str
    display_name: str
    role: str


DEMO_USERS: dict[str, AuthUser] = {
    "viewer.demo": AuthUser(username="viewer.demo", display_name="Viewer Demo", role="viewer"),
    "analyst.demo": AuthUser(username="analyst.demo", display_name="Analyst Demo", role="analyst"),
    "admin.demo": AuthUser(username="admin.demo", display_name="Admin Demo", role="admin"),
}


def get_current_user(
    x_demo_user: str | None = Header(default=None),
    x_user_role: str | None = Header(default=None),
) -> AuthUser:
    username = (x_demo_user or "analyst.demo").strip().lower()
    user = DEMO_USERS.get(username)
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown demo user.")
    if x_user_role and x_user_role.strip().lower() != user.role:
        raise HTTPException(status_code=403, detail="Role header does not match selected user.")
    return user


def require_roles(*roles: str):
    allowed = {role.lower() for role in roles}

    def _require(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role.lower() not in allowed:
            raise HTTPException(status_code=403, detail="You do not have access to this action.")
        return user

    return _require
