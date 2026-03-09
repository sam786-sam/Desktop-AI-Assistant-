#!/usr/bin/env python3
"""
Calendar and Reminder System for AI Assistant
Features:
- Save events with dates
- Daily check for upcoming events
- Reminders 1 day before and on the event day
- Persistent storage using JSON
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

class CalendarSystem:
    def __init__(self, data_file="Backend/CalendarEvents.data"):
        self.data_file = data_file
        self.events = self.load_events()
        
    def load_events(self) -> Dict[str, List[Dict]]:
        """Load events from the data file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_events(self):
        """Save events to the data file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        # Try different formats
        formats = [
            "%d %B",      # "5 March"
            "%B %d",      # "March 5"
            "%d %b",      # "5 Mar"
            "%b %d",      # "Mar 5"
            "%d/%m/%Y",   # "05/03/2026"
            "%d-%m-%Y",   # "05-03-2026"
            "%Y-%m-%d",   # "2026-03-05"
            "%d/%m",      # "05/03" (current year)
            "%d-%m",      # "05-03" (current year)
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If year is not specified, use current year
                if dt.year == 1900:  # Default year when not specified
                    current_year = datetime.now().year
                    dt = dt.replace(year=current_year)
                return dt
            except ValueError:
                continue
        
        # Try to extract date from natural language
        # Look for patterns like "5 march", "march 5", etc.
        date_patterns = [
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
            r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str.lower())
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # Check which group is the day and which is the month
                    if groups[0].isdigit():
                        day, month = groups[0], groups[1]
                    else:
                        month, day = groups[0], groups[1]
                    
                    # Convert month name to number
                    month_map = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12,
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                        'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                        'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    
                    month_num = month_map.get(month.lower())
                    if month_num:
                        try:
                            year = datetime.now().year
                            dt = datetime(year, month_num, int(day))
                            return dt
                        except ValueError:
                            continue
        
        return None
    
    def add_event(self, date_str: str, event_description: str) -> bool:
        """Add an event to the calendar"""
        event_date = self.parse_date(date_str)
        if not event_date:
            print(f"Could not parse date: {date_str}")
            return False
        
        # Format date as YYYY-MM-DD for storage
        date_key = event_date.strftime('%Y-%m-%d')
        
        # Create event entry
        event_entry = {
            "date": date_key,
            "description": event_description,
            "added_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "reminded_before": False,  # Will be reminded 1 day before
            "reminded_on_day": False   # Will be reminded on the day
        }
        
        # Add to events dict
        if date_key not in self.events:
            self.events[date_key] = []
        self.events[date_key].append(event_entry)
        
        # Save to file
        self.save_events()
        
        print(f"Event added: '{event_description}' on {date_key}")
        return True
    
    def get_events_for_date(self, date: datetime) -> List[Dict]:
        """Get events for a specific date"""
        date_key = date.strftime('%Y-%m-%d')
        return self.events.get(date_key, [])
    
    def get_events_for_range(self, start_date: datetime, end_date: datetime) -> Dict[str, List[Dict]]:
        """Get events for a date range"""
        result = {}
        current = start_date
        while current <= end_date:
            date_key = current.strftime('%Y-%m-%d')
            events = self.events.get(date_key, [])
            if events:
                result[date_key] = events
            current += timedelta(days=1)
        return result
    
    def check_upcoming_reminders(self) -> List[Dict]:
        """Check for events that need reminders (today and tomorrow)"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        upcoming_events = []
        
        # Check for today's events
        today_events = self.get_events_for_date(datetime.combine(today, datetime.min.time()))
        for event in today_events:
            if not event.get('reminded_on_day', False):
                upcoming_events.append({
                    "event": event,
                    "reminder_type": "today",
                    "message": f"Today is {event['date']}: {event['description']}"
                })
        
        # Check for tomorrow's events (remind 1 day before)
        tomorrow_events = self.get_events_for_date(datetime.combine(tomorrow, datetime.min.time()))
        for event in tomorrow_events:
            if not event.get('reminded_before', False):
                upcoming_events.append({
                    "event": event,
                    "reminder_type": "tomorrow",
                    "message": f"Tomorrow ({event['date']}): {event['description']}"
                })
        
        return upcoming_events
    
    def mark_reminder_sent(self, event_date: str, event_description: str, reminder_type: str):
        """Mark that a reminder has been sent for an event"""
        events = self.events.get(event_date, [])
        for event in events:
            if event['description'] == event_description:
                if reminder_type == "today":
                    event['reminded_on_day'] = True
                elif reminder_type == "tomorrow":
                    event['reminded_before'] = True
        
        self.save_events()
    
    def list_all_events(self) -> str:
        """Return a formatted string of all events"""
        if not self.events:
            return "No events scheduled in the calendar."
        
        result = "Scheduled Events:\n"
        sorted_dates = sorted(self.events.keys())
        
        for date_key in sorted_dates:
            events = self.events[date_key]
            date_obj = datetime.strptime(date_key, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            result += f"\n{formatted_date}:\n"
            
            for i, event in enumerate(events, 1):
                status = []
                if event.get('reminded_before', False):
                    status.append("✓ Pre-reminded")
                if event.get('reminded_on_day', False):
                    status.append("✓ Day-reminded")
                
                status_str = f" ({', '.join(status)})" if status else ""
                result += f"  {i}. {event['description']}{status_str}\n"
        
        return result


# Example usage and testing
if __name__ == "__main__":
    # Create calendar instance
    calendar = CalendarSystem()
    
    # Test adding events
    print("Adding test events...")
    calendar.add_event("5 March", "Meet friend")
    calendar.add_event("March 10", "Team meeting")
    calendar.add_event("15/03", "Doctor appointment")
    
    # List all events
    print("\nAll events:")
    print(calendar.list_all_events())
    
    # Check for upcoming reminders
    print("\nUpcoming reminders:")
    reminders = calendar.check_upcoming_reminders()
    for reminder in reminders:
        print(f"- {reminder['message']}")