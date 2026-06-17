"""Email account OAuth + management endpoints."""

from __future__ import annotations

import secrets
import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy import select
from starlette.responses import RedirectResponse

from app.api.deps import CurrentUser, SessionDep
from app.config import settings
from app.models.email_account import EmailAccount
from app.schemas.account import EmailAccountOut, OAuthStartOut
from app.services.connectors.gmail import encrypt_refresh_token
from app.services.connectors.outlook import OutlookConnector

router = APIRouter(prefix="/accounts", tags=["accounts"])

# Per-process state map; production should use Redis with TTL.
_oauth_states: dict[str, dict[str, str]] = {}


def _require_oauth_config(provider: str) -> None:
    if provider == "gmail":
        missing = [
            name
            for name, value in {
                "GOOGLE_CLIENT_ID": settings.google_client_id,
                "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
                "GOOGLE_REDIRECT_URI": settings.google_redirect_uri,
            }.items()
            if not value
        ]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Gmail OAuth is not configured. Missing: {', '.join(missing)}.",
            )
    if provider == "outlook":
        missing = [
            name
            for name, value in {
                "MS_CLIENT_ID": settings.ms_client_id,
                "MS_CLIENT_SECRET": settings.ms_client_secret,
                "MS_REDIRECT_URI": settings.ms_redirect_uri,
            }.items()
            if not value
        ]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Outlook OAuth is not configured. Missing: {', '.join(missing)}.",
            )


@router.get("", response_model=list[EmailAccountOut])
async def list_accounts(user: CurrentUser, db: SessionDep) -> list[EmailAccountOut]:
    res = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == user.id)
    )
    return [EmailAccountOut.model_validate(a) for a in res.scalars().all()]


@router.delete(
    "/{account_id}",
    status_code=204,
    response_class=Response,
    response_model=None,
)
async def disconnect(account_id: uuid.UUID, user: CurrentUser, db: SessionDep):
    acc = await db.get(EmailAccount, account_id)
    if not acc or acc.user_id != user.id:
        raise HTTPException(status_code=404, detail="not found")
    await db.delete(acc)
    await db.commit()
    return Response(status_code=204)


# --- Gmail OAuth ----------------------------------------------------------
@router.get("/gmail/start", response_model=OAuthStartOut)
async def gmail_start(user: CurrentUser) -> OAuthStartOut:
    _require_oauth_config("gmail")
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = {"user_id": str(user.id), "provider": "gmail"}
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(
            [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.modify",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ]
        ),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return OAuthStartOut(authorize_url=url, state=state)


@router.get("/gmail/callback")
async def gmail_callback(
    db: SessionDep,
    code: str = Query(...),
    state: str = Query(...),
) -> RedirectResponse:
    """Exchanges code for tokens. In production, use FastAPI BackgroundTasks."""
    info = _oauth_states.pop(state, None)
    if not info:
        raise HTTPException(status_code=400, detail="invalid state")
    import httpx

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.google_redirect_uri,
                },
            )
            r.raise_for_status()
            data = r.json()
            profile_r = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {data['access_token']}"},
            )
            profile_r.raise_for_status()
            profile = profile_r.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json().get("error_description") or exc.response.text
        except Exception:  # noqa: BLE001
            detail = exc.response.text
        raise HTTPException(status_code=400, detail=f"Gmail OAuth failed: {detail}") from exc

    user_id = uuid.UUID(info["user_id"])
    email_address = profile.get("email")
    if not email_address:
        raise HTTPException(status_code=400, detail="Gmail profile did not return an email address")

    refresh_token = (
        encrypt_refresh_token(data.get("refresh_token", ""))
        if data.get("refresh_token")
        else None
    )
    acc = (
        await db.execute(
            select(EmailAccount).where(
                EmailAccount.user_id == user_id,
                EmailAccount.provider == "gmail",
                EmailAccount.email_address == email_address,
            )
        )
    ).scalar_one_or_none()

    if acc:
        acc.display_name = profile.get("name")
        acc.access_token = data["access_token"]
        if refresh_token:
            acc.refresh_token = refresh_token
        acc.token_expires_at = str(data.get("expires_in"))
        acc.scope = data.get("scope")
        acc.is_active = True
    else:
        acc = EmailAccount(
            user_id=user_id,
            provider="gmail",
            email_address=email_address,
            display_name=profile.get("name"),
            access_token=data["access_token"],
            refresh_token=refresh_token,
            token_expires_at=str(data.get("expires_in")),
            scope=data.get("scope"),
            is_active=True,
        )
        db.add(acc)

    await db.commit()
    return RedirectResponse(f"{settings.app_base_url}/inbox?gmail=connected", status_code=302)


# --- Outlook OAuth --------------------------------------------------------
@router.get("/outlook/start", response_model=OAuthStartOut)
async def outlook_start(user: CurrentUser) -> OAuthStartOut:
    _require_oauth_config("outlook")
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = {"user_id": str(user.id), "provider": "outlook"}
    params = {
        "client_id": settings.ms_client_id,
        "response_type": "code",
        "redirect_uri": settings.ms_redirect_uri,
        "response_mode": "query",
        "scope": "offline_access User.Read Mail.Read",
        "state": state,
    }
    url = (
        f"https://login.microsoftonline.com/{settings.ms_tenant}/oauth2/v2.0/authorize?"
        + urlencode(params)
    )
    return OAuthStartOut(authorize_url=url, state=state)


@router.get("/outlook/callback")
async def outlook_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: SessionDep = None,
) -> dict:
    info = _oauth_states.pop(state, None)
    if not info:
        raise HTTPException(status_code=400, detail="invalid state")
    import httpx

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"https://login.microsoftonline.com/{settings.ms_tenant}/oauth2/v2.0/token",
            data={
                "client_id": settings.ms_client_id,
                "client_secret": settings.ms_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.ms_redirect_uri,
            },
        )
        r.raise_for_status()
        data = r.json()
        me_r = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {data['access_token']}"},
        )
        me = me_r.json()

    async with db:  # type: ignore[misc]
        acc = EmailAccount(
            user_id=uuid.UUID(info["user_id"]),
            provider="outlook",
            email_address=me.get("userPrincipalName") or me.get("mail"),
            display_name=me.get("displayName"),
            access_token=data["access_token"],
            refresh_token=encrypt_refresh_token(data.get("refresh_token", "")) if data.get("refresh_token") else None,
            token_expires_at=str(data.get("expires_in")),
            scope=data.get("scope"),
            is_active=True,
        )
        db.add(acc)
        await db.commit()
        await db.refresh(acc)
        return {"ok": True, "account_id": str(acc.id)}
