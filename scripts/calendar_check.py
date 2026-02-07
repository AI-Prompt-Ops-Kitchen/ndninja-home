#!/usr/bin/env python3
"""
Calendar Check - Query iCloud CalDAV for upcoming events.

Usage:
    python3 calendar_check.py                    # Next 7 days
    python3 calendar_check.py --days 3           # Next 3 days
    python3 calendar_check.py --calendar "Content Creation"  # Specific calendar
    python3 calendar_check.py --today            # Today only
    python3 calendar_check.py --tomorrow         # Tomorrow only
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Load environment
env_file = Path(__file__).parent.parent / ".env.calendar"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

try:
    import caldav
    from caldav.elements import dav
except ImportError:
    print("Error: caldav not installed. Run: pip install caldav")
    sys.exit(1)

def get_calendars(client):
    """Get all calendars from the principal."""
    principal = client.principal()
    return principal.calendars()

def get_events(calendar, start_date, end_date):
    """Get events from a calendar within date range."""
    try:
        events = calendar.search(start=start_date, end=end_date, expand=True)
        return events
    except Exception as e:
        return []

def parse_event(event):
    """Parse a caldav event into a simple dict."""
    try:
        vevent = event.vobject_instance.vevent
        
        summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "No title"
        
        # Handle all-day vs timed events
        dtstart = vevent.dtstart.value
        if hasattr(dtstart, 'hour'):
            start_str = dtstart.strftime("%Y-%m-%d %I:%M %p")
            start_date = dtstart.strftime("%Y-%m-%d")
            start_time = dtstart.strftime("%I:%M %p")
        else:
            start_str = dtstart.strftime("%Y-%m-%d") + " (all day)"
            start_date = dtstart.strftime("%Y-%m-%d")
            start_time = "all day"
        
        return {
            "summary": summary,
            "start": start_str,
            "start_date": start_date,
            "start_time": start_time,
            "raw_start": dtstart
        }
    except Exception as e:
        return None

def main():
    parser = argparse.ArgumentParser(description="Check calendar for upcoming events")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look ahead")
    parser.add_argument("--calendar", type=str, help="Filter by calendar name")
    parser.add_argument("--today", action="store_true", help="Today only")
    parser.add_argument("--tomorrow", action="store_true", help="Tomorrow only")
    parser.add_argument("--list-calendars", action="store_true", help="List available calendars")
    args = parser.parse_args()
    
    # Connect
    url = os.environ.get("CALDAV_URL", "https://caldav.icloud.com/")
    username = os.environ.get("CALDAV_USERNAME")
    password = os.environ.get("CALDAV_PASSWORD")
    
    if not username or not password:
        print("Error: CALDAV_USERNAME and CALDAV_PASSWORD required")
        sys.exit(1)
    
    try:
        client = caldav.DAVClient(url=url, username=username, password=password)
        calendars = get_calendars(client)
    except Exception as e:
        print(f"Error connecting to calendar: {e}")
        sys.exit(1)
    
    if args.list_calendars:
        print("Available calendars:")
        for cal in calendars:
            print(f"  - {cal.name}")
        return
    
    # Date range
    now = datetime.now()
    if args.today:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        range_desc = "today"
    elif args.tomorrow:
        start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        range_desc = "tomorrow"
    else:
        start_date = now
        end_date = now + timedelta(days=args.days)
        range_desc = f"next {args.days} days"
    
    # Collect events
    all_events = []
    for cal in calendars:
        if args.calendar and args.calendar.lower() not in cal.name.lower():
            continue
        
        events = get_events(cal, start_date, end_date)
        for event in events:
            parsed = parse_event(event)
            if parsed:
                parsed["calendar"] = cal.name
                all_events.append(parsed)
    
    # Sort by start time
    all_events.sort(key=lambda x: str(x.get("raw_start", "")))
    
    # Output
    print(f"📅 Calendar events ({range_desc}):")
    print(f"   Current time: {now.strftime('%A, %B %d, %Y %I:%M %p')}")
    print()
    
    if not all_events:
        print("   No events found.")
    else:
        current_date = None
        for evt in all_events:
            if evt["start_date"] != current_date:
                current_date = evt["start_date"]
                # Parse and format the date nicely
                date_obj = datetime.strptime(current_date, "%Y-%m-%d")
                print(f"📆 {date_obj.strftime('%A, %B %d')}:")
            
            print(f"   • {evt['start_time']}: {evt['summary']} [{evt['calendar']}]")
    
    print()

if __name__ == "__main__":
    main()
