#!/usr/bin/env python3
"""
Calendar Integration for AI Assistant
Handles calendar commands and reminder functionality
"""

import re
from datetime import datetime
from Backend.CalendarSystem import CalendarSystem

class CalendarIntegration:
    def __init__(self):
        self.calendar = CalendarSystem()
    
    def process_calendar_command(self, command: str) -> str:
        """Process calendar-related commands"""
        command_lower = command.lower()
        
        # Check if the command is about adding/reminding events
        if any(word in command_lower for word in ['remind', 'remember', 'meet', 'appointment', 'event', 'schedule', 'add']):
            # Try to extract date and event from the command
            result = self.extract_and_add_event(command)
            return result
        
        elif 'show' in command_lower or 'list' in command_lower or 'events' in command_lower:
            return self.calendar.list_all_events()
        
        else:
            return "Calendar command not recognized. You can say things like 'remind me to meet John on March 5th' or 'show my events'."
    
    def extract_and_add_event(self, command: str) -> str:
        """Extract date and event from command and add to calendar"""
        # Pattern 1: "remind me to [event] on [date]"
        pattern1 = r'(?:remind me to|remember to|add event to|schedule to|meet|appointment to|event to)\s+(.*?)(?:\s+on\s+|\s+at\s+|\s+for\s+)(.*)'
        
        # Pattern 2: "[event] on [date]"
        pattern2 = r'(.*?)(?:\s+on\s+|\s+at\s+|\s+for\s+)(.*)'
        
        # Try pattern 1 first
        match = re.search(pattern1, command, re.IGNORECASE)
        if not match:
            # Try pattern 2
            match = re.search(pattern2, command, re.IGNORECASE)
        
        if match:
            event_description = match.group(1).strip()
            date_part = match.group(2).strip()
            
            # Clean up the event description if it's too generic
            if not event_description or event_description.lower() in ['to', 'me', 'my']:
                # Try to extract from the original command differently
                # Look for "meet [person]" or similar
                person_match = re.search(r'(?:meet|see|call|visit)\s+(.+?)(?:\s+on|\s+at|$)', command, re.IGNORECASE)
                if person_match:
                    event_description = f"Meet {person_match.group(1).strip()}"
                else:
                    event_description = command.replace(date_part, '').replace('remind me', '').replace('remember', '').strip()
                    event_description = event_description.replace('to', '').strip()
            
            if event_description and date_part:
                success = self.calendar.add_event(date_part, event_description)
                if success:
                    return f"I've added '{event_description}' to your calendar on {date_part}. I'll remind you a day before and on the day of the event."
                else:
                    return f"Sorry, I couldn't understand the date '{date_part}'. Please try formats like 'March 5' or '5 March'."
            else:
                return "I couldn't identify the event or date in your command. Please be more specific like 'remind me to meet John on March 5'."
        else:
            return "I couldn't identify the event or date in your command. Please say something like 'remind me to meet John on March 5'."
    
    def check_daily_reminders(self) -> str:
        """Check for daily reminders and return appropriate message"""
        reminders = self.calendar.check_upcoming_reminders()
        if not reminders:
            return ""
        
        messages = []
        for reminder in reminders:
            messages.append(reminder['message'])
            # Mark this reminder as sent
            event_date = reminder['event']['date']
            event_desc = reminder['event']['description']
            reminder_type = reminder['reminder_type']
            self.calendar.mark_reminder_sent(event_date, event_desc, reminder_type)
        
        return " | ".join(messages)


# Example usage
if __name__ == "__main__":
    cal_integration = CalendarIntegration()
    
    # Test adding an event
    result = cal_integration.process_calendar_command("remind me to meet friend on 5 March")
    print(result)
    
    # Test listing events
    print("\nAll events:")
    print(cal_integration.calendar.list_all_events())
    
    # Test checking daily reminders
    print("\nDaily reminders:")
    print(cal_integration.check_daily_reminders())