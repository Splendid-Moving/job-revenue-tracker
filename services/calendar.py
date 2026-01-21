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

def get_todays_jobs():
    """
    Fetches events from the primary calendar for the current day (Los Angeles time).
    Returns a list of simplified event objects with source information.
    """
    service = get_service('calendar', 'v3')

    # Get current time in Los Angeles timezone
    la_tz = ZoneInfo('America/Los_Angeles')
    today = datetime.now(la_tz)
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Format to RFC3339
    time_min = start_of_day.isoformat() + 'Z'
    time_max = end_of_day.isoformat() + 'Z'

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
