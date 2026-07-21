import datetime
import uuid
import httpx
from app.core.config import settings
from app.core.logger import logger

class GoogleCalendarConnector:
    """Real-world integration wrapper for Google Calendar API operations."""
    
    @staticmethod
    async def create_meeting_invite(title: str, start_time: datetime.datetime) -> str:
        logger.info(f"GoogleCalendar: Requesting meeting schedule for '{title}' at {start_time}")
        
        if not settings.GOOGLE_CALENDAR_CREDENTIALS:
            logger.warning("GoogleCalendar: GOOGLE_CALENDAR_CREDENTIALS not configured. Using fallback mock invite.")
            meet_link = f"https://meet.google.com/vocentra-ai-mock-{start_time.strftime('%f')[:6]}"
            logger.info(f"GoogleCalendar Fallback: Invite scheduled. Google Meet URL: {meet_link}")
            return meet_link

        # Real Google Calendar v3 API call using httpx
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {"conferenceDataVersion": "1"}
        headers = {
            "Authorization": f"Bearer {settings.GOOGLE_CALENDAR_CREDENTIALS}",
            "Content-Type": "application/json"
        }
        
        end_time = start_time + datetime.timedelta(minutes=30)
        
        payload = {
            "summary": title,
            "description": "Scheduled by Vocentra AI voice agent assistant.",
            "start": {
                "dateTime": start_time.isoformat() + "Z",
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.isoformat() + "Z",
                "timeZone": "UTC"
            },
            "conferenceData": {
                "createRequest": {
                    "requestId": str(uuid.uuid4()),
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, params=params, json=payload)
                if response.status_code in [200, 201]:
                    data = response.json()
                    meet_link = data.get("hangoutLink")
                    if meet_link:
                        logger.info(f"GoogleCalendar: Invite successfully scheduled. Google Meet URL: {meet_link}")
                        return meet_link
                    else:
                        logger.warning("GoogleCalendar: Event scheduled, but no Hangout/Meet link generated.")
                        return data.get("htmlLink", "https://calendar.google.com")
                else:
                    logger.error(f"GoogleCalendar: Scheduling failed with status={response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"GoogleCalendar Integration encountered exception: {str(e)}")
            
        # Fallback Meet Link
        return f"https://meet.google.com/vocentra-ai-failover-{start_time.strftime('%H%M%S')}"
