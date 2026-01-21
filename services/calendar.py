from datetime import datetime, timedelta, timezone
from services.auth import get_service
import config
from zoneinfo import ZoneInfo

# Color to source mapping
COLOR_SOURCE_MAP = {
    '6': 'Yelp',        # #ffb878 (orange)
    '2': 'Google LSA',  # #7ae7bf (teal/mint)
}

def get_color_hex(service, color_id):
    """Get hex color code for a given color ID"""
    try:
        colors = service.colors().get().execute()
        return colors['event'].get(color_id, {}).get('background', '')
    except:
        return ''

def get_todays_jobs(date_str=None):
    """
    Fetches events from the primary calendar for the specified day (Los Angeles time).
    If date_str is None, uses today.
    Returns a list of simplified event objects with source information.
    """
    service = get_service('calendar', 'v3')

    # Get current time in Los Angeles timezone
    la_tz = ZoneInfo('America/Los_Angeles')
    
    if date_str:
        try:
            # Parse provided date string (YYYY-MM-DD)
            # Create a naive datetime then replace with LA tz info
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            query_date = dt.replace(tzinfo=la_tz)
        except ValueError:
            from utils.logger import log_warning
            log_warning(f"Invalid date format: {date_str}, falling back to today")
            query_date = datetime.now(la_tz)
    else:
        query_date = datetime.now(la_tz)
        
    start_of_day = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Convert to UTC for API (Google Calendar API expects UTC)
    time_min = start_of_day.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    time_max = end_of_day.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    print(f"Fetching events from {time_min} to {time_max}...")

    events_result = service.events().list(
        calendarId=config.CALENDAR_ID, 
        timeMin=time_min, 
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime',
        fields='items(id,summary,start,end,location,colorId,description)'
    ).execute()
    
    events = events_result.get('items', [])
    
    jobs = []
    for event in events:
        summary = event.get('summary', 'Untitled Job')
        color_id = event.get('colorId', None)
        
        # Determine source based on color
        if color_id in config.COLOR_SOURCE_MAP:
            source = config.COLOR_SOURCE_MAP[color_id]
        else:
            source = 'Other'
        
        jobs.append({
            'id': event['id'],
            'summary': summary,
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'location': event.get('location', 'No Location'),
            'colorId': color_id,
            'source': source
        })
        
    return jobs
