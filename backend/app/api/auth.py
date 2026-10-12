"""Authentication, Keycloak OIDC metadata, and local demo session endpoints."""
from typing import Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.core.config import settings
from app.core.security import AuthenticatedUser, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class DemoLoginRequest(BaseModel):
    role: Literal["viewer", "analyst", "admin"] = "analyst"
    username: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int
    user_id: str
    roles: List[str]


@router.get("/me")
def get_user_profile(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns the current authenticated user identity and effective roles."""
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "roles": user.roles,
        "is_demo": user.is_demo,
    }


@router.get("/config")
def get_auth_config():
    """Returns operator OIDC and Keycloak configuration parameters."""
    return {
        "demo_mode": settings.demo_mode,
        "environment": settings.environment,
        "oidc_configured": bool(settings.oidc_issuer_url and settings.oidc_client_id),
        "oidc_issuer_url": settings.oidc_issuer_url,
        "oidc_client_id": settings.oidc_client_id,
        "oidc_audience": settings.oidc_audience,
        "supported_roles": ["viewer", "analyst", "admin"],
        "saml_brokering": "Supported upstream via Keycloak Identity Providers",
    }


@router.post("/demo-login", response_model=TokenResponse)
def demo_login(payload: DemoLoginRequest):
    """Generates a demo JWT access token for local development. Strictly blocked in production."""
    if not settings.demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled. Please authenticate through the configured Keycloak OIDC provider.",
        )
    if settings.environment in {"production", "prod"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is forbidden in production environments.",
        )

    uname = payload.username or f"demo-{payload.role}"
    # Assign hierarchical roles
    if payload.role == "admin":
        roles = ["admin", "analyst", "viewer"]
    elif payload.role == "analyst":
        roles = ["analyst", "viewer"]
    else:
        roles = ["viewer"]

    token = create_access_token(
        subject=uname,
        roles=roles,
        email=f"{uname}@orbit.local",
    )

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        user_id=uname,
        roles=roles,
    )


@router.post("/logout")
def logout(user: AuthenticatedUser = Depends(get_current_user)):
    """Explicit logout endpoint."""
    return {"status": "logged_out", "user_id": user.user_id}
