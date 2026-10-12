"""Security, OIDC token decoding, and role-based authorization."""
import datetime as dt
from typing import Dict, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

ROLE_HIERARCHY: Dict[str, int] = {
    "viewer": 1,
    "analyst": 2,
    "admin": 3,
}


class AuthenticatedUser(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    roles: List[str]
    is_demo: bool = False

    def has_role(self, required_role: str) -> bool:
        required_level = ROLE_HIERARCHY.get(required_role, 999)
        user_max_level = max([ROLE_HIERARCHY.get(r, 0) for r in self.roles], default=0)
        return user_max_level >= required_level


def create_access_token(
    subject: str,
    roles: List[str],
    email: Optional[str] = None,
    expires_delta: Optional[dt.timedelta] = None,
) -> str:
    """Creates a signed JWT access token for local/demo/testing use."""
    now = dt.datetime.now(dt.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + dt.timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "email": email or f"{subject}@orbit.local",
        "roles": roles,
        "iss": settings.oidc_issuer_url or "orbit-workbench",
        "aud": settings.oidc_audience or "orbit-frontend",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> AuthenticatedUser:
    """Decodes and validates JWT token without logging secret values."""
    try:
        # In production with OIDC, decode with audience/issuer checks
        verify_claims = {"verify_exp": True, "verify_signature": True}
        options = {"verify_aud": bool(settings.oidc_audience)}
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options=options,
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Support both standard Keycloak realm_access.roles and top-level roles claim
        roles: List[str] = []
        if "roles" in payload and isinstance(payload["roles"], list):
            roles = payload["roles"]
        elif "realm_access" in payload and isinstance(payload["realm_access"], dict):
            realm_roles = payload["realm_access"].get("roles", [])
            for r in realm_roles:
                if r in ROLE_HIERARCHY:
                    roles.append(r)

        if not roles:
            roles = ["viewer"]

        return AuthenticatedUser(
            user_id=str(user_id),
            username=str(user_id),
            email=payload.get("email"),
            roles=roles,
            is_demo=False,
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authorization token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AuthenticatedUser:
    """Resolves authenticated user from Bearer header or demo credentials."""
    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        token = credentials.credentials.strip()
        # Explicit test helper token recognition in demo mode
        if settings.demo_mode and token.startswith("demo-token-"):
            role_hint = token.replace("demo-token-", "")
            assigned_role = role_hint if role_hint in ROLE_HIERARCHY else "analyst"
            return AuthenticatedUser(
                user_id=f"demo-{assigned_role}",
                username=f"Demo {assigned_role.capitalize()}",
                email=f"demo-{assigned_role}@orbit.local",
                roles=[assigned_role],
                is_demo=True,
            )
        return decode_jwt_token(token)

    # When no token is passed, demo mode can fallback to default viewer if configured,
    # but ONLY on localhost non-production environments.
    if settings.demo_mode and settings.environment in {"development", "test"}:
        return AuthenticatedUser(
            user_id="demo-analyst",
            username="Local Demo Analyst",
            email="demo-analyst@orbit.local",
            roles=["analyst", "viewer"],
            is_demo=True,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: str):
    """Dependency factory checking required role."""
    def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: '{required_role}'. Your roles: {user.roles}",
            )
        return user
    return role_checker
