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
    
    import time
    events_result = {}
    max_retries = 3
    
    for attempt in range(1, max_retries + 1):
        try:
            events_result = service.events().list(
                calendarId=config.CALENDAR_ID, 
                timeMin=time_min, 
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                fields='items(id,summary,start,end,location,colorId,description)'
            ).execute()
            break # Success
        except Exception as e:
            if attempt < max_retries:
                print(f"⚠️ Calendar API failed (Attempt {attempt}/{max_retries}): {e}. Retrying...")
                time.sleep(2)
            else:
                print(f"❌ Calendar API failed after {max_retries} attempts.")
                raise e
    
    events = events_result.get('items', [])
    
    import re
    
    jobs = []
    for event in events:
        summary = event.get('summary', 'Untitled Job')
        color_id = event.get('colorId', None)
        description = event.get('description', '')
        
        source = None
        
        # 1. Try to parse from Description (New Method)
        # Look for "Source: Value" (case insensitive)
        source_match = re.search(r'Source:\s*(.*)', description, re.IGNORECASE)
        if source_match:
            source_val = source_match.group(1).strip().lower()
            if 'yelp' in source_val:
                source = 'Yelp'
            elif 'local service' in source_val or 'lsa' in source_val:
                source = 'Google LSA'
            else:
                source = 'Other'
                
        # 2. Fallback to Color (Legacy Method)
        if not source:
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


def get_tomorrows_jobs():
    """
    Fetches events from the calendar for tomorrow (Los Angeles time).
    This is used by the 7 PM pre-population job.
    """
    la_tz = ZoneInfo('America/Los_Angeles')
    tomorrow = datetime.now(la_tz) + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    return get_todays_jobs(date_str=tomorrow_str)


def update_event_description(event_id, form_url):
    """
    Appends the form URL to the event description.
    If a form URL already exists, it will be replaced.
    """
    service = get_service('calendar', 'v3')
    
    try:
        # Get current event
        event = service.events().get(
            calendarId=config.CALENDAR_ID,
            eventId=event_id
        ).execute()
        
        current_description = event.get('description', '')
        
        # Check if form link already exists
        import re
        form_link_pattern = r'\n?📋 Form: https?://[^\s]+'
        
        if re.search(form_link_pattern, current_description):
            # Replace existing form link
            new_description = re.sub(form_link_pattern, f'\n📋 Form: {form_url}', current_description)
        else:
            # Append form link
            new_description = current_description + f'\n\n📋 Form: {form_url}'
        
        # Update event
        event['description'] = new_description.strip()
        service.events().update(
            calendarId=config.CALENDAR_ID,
            eventId=event_id,
            body=event
        ).execute()
        
        print(f"Updated event {event_id} with form URL")
        return True
        
    except Exception as e:
        print(f"Error updating event description: {e}")
        return False

