"""
Google OAuth integration routes.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from config import settings
from store.sql.credentials import save_credentials, get_credentials, delete_credentials
import time

router = APIRouter()

oauth = OAuth(Config(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET
}))

# Register the google client
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events https://www.googleapis.com/auth/drive.readonly',
        # Request offline access to get a refresh token
        'prompt': 'consent',
        'access_type': 'offline'
    }
)

@router.get("/google/login")
async def login_google(request: Request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
         return {"error": "Google Client ID/Secret missing in config."}
    
    # Needs to match the URL configured in GCP console exactly
    redirect_uri = request.url_for('auth_google_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        return {"error": f"Authorization failed: {e}"}
        
    user = token.get('userinfo')
    if user:
        email = user.get('email', '')
        # Convert expires_in (relative seconds) to absolute expiry
        expires_at = time.time() + token.get('expires_in', 3599)
        
        await save_credentials(
            access_token=token.get('access_token'),
            refresh_token=token.get('refresh_token', ''), # Refresh token only present on first prompt=consent
            expires_at=expires_at,
            email=email
        )
        # Redirect to frontend dashboard instead of closing
        frontend_url = "http://localhost:5173/#/dashboard"
        return RedirectResponse(url=frontend_url)
    return {"error": "No user info"}

@router.get("/google/status")
async def auth_google_status():
    creds = await get_credentials()
    if creds:
        # Check if valid
        is_refreshable = bool(creds.get("refresh_token"))
        is_expired = time.time() > creds.get("expires_at", 0)
        
        status = "connected"
        if is_expired and not is_refreshable:
            status = "expired"
        elif is_expired:
            status = "needs_refresh"
            
        return {
            "status": status,
            "email": creds.get("email"),
            "expires_at": creds.get("expires_at"),
            "has_refresh": is_refreshable
        }
    return {"status": "unconnected"}

@router.post("/google/logout")
async def auth_google_logout():
    await delete_credentials()
    return {"status": "ok"}
