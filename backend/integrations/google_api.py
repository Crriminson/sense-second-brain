"""
Google API Integration Layer.
Provides simplified wrappers for Calendar, Keep (via Drive), etc.
Handles token refreshing automatically.
"""

import time
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import datetime

from store.sql.credentials import get_credentials, save_credentials
from config import settings

class GoogleAPIError(Exception):
    pass

async def _get_valid_google_credentials() -> Credentials:
    """Get active credentials, refreshing them if necessary."""
    creds_data = await get_credentials()
    if not creds_data:
        raise GoogleAPIError("No Google credentials found. Please login first.")
    
    expires_at = creds_data.get("expires_at", 0)
    access_token = creds_data.get("access_token")
    refresh_token = creds_data.get("refresh_token")
    email = creds_data.get("email")
    
    # If expired, we must refresh
    if time.time() > expires_at:
        if not refresh_token:
            raise GoogleAPIError("Token expired and no refresh token available. Re-login required.")
            
        # Perform refresh
        token_url = "https://oauth2.googleapis.com/token"
        resp = requests.post(token_url, data={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        })
        
        if resp.status_code != 200:
            raise GoogleAPIError(f"Failed to refresh token: {resp.text}")
            
        data = resp.json()
        access_token = data.get("access_token")
        new_expires_in = data.get("expires_in", 3599)
        expires_at = time.time() + new_expires_in
        
        # Save updated tokens
        await save_credentials(
            access_token=access_token,
            refresh_token=refresh_token, # keep the old one
            expires_at=expires_at,
            email=email
        )
        
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET
    )

async def get_upcoming_calendar_events(max_results: int = 5) -> list[dict]:
    """Fetch the next few upcoming events from the user's primary calendar."""
    try:
        creds = await _get_valid_google_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        formatted = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            formatted.append({
                "summary": event.get('summary', 'Untitled Event'),
                "start": start,
                "end": end,
                "link": event.get('htmlLink', '')
            })
            
        return formatted
    except Exception as e:
        print(f"[GOOGLE] Calendar Error: {e}")
        return []

async def create_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> dict:
    """
    Create an event in the user's primary calendar.
    start_time and end_time MUST be in ISO format (e.g. '2023-10-31T09:00:00-07:00' or '2023-10-31T09:00:00Z').
    """
    try:
        creds = await _get_valid_google_credentials()
        service = build('calendar', 'v3', credentials=creds)
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
            },
            'end': {
                'dateTime': end_time,
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return {
            "status": "success",
            "summary": created_event.get('summary'),
            "link": created_event.get('htmlLink')
        }
    except Exception as e:
        print(f"[GOOGLE] Calendar Create Error: {e}")
        return {"status": "error", "message": str(e)}
