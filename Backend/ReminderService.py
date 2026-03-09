#!/usr/bin/env python3
"""
Daily Reminder Checker for AI Assistant
Checks for upcoming events and sends reminders
"""

import time
import threading
import asyncio
from datetime import datetime
from Backend.CalendarIntegration import CalendarIntegration
from Backend.TextToSpeech import TextToSpeech

class DailyReminderChecker:
    def __init__(self):
        self.calendar_integration = CalendarIntegration()
        self.running = False
        self.reminder_thread = None
    
    def start_reminder_service(self):
        """Start the reminder service in a background thread"""
        if not self.running:
            self.running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()
            print("[Reminder Service] Started daily reminder checker")
    
    def stop_reminder_service(self):
        """Stop the reminder service"""
        self.running = False
        if self.reminder_thread:
            self.reminder_thread.join(timeout=2)
        print("[Reminder Service] Stopped daily reminder checker")
    
    def _reminder_loop(self):
        """Main loop that checks for reminders periodically"""
        while self.running:
            try:
                # Check for reminders every 10 minutes (600 seconds)
                # You could adjust this frequency as needed
                reminder_msg = self.calendar_integration.check_daily_reminders()
                
                if reminder_msg:
                    print(f"[Reminder Service] Triggering reminder: {reminder_msg}")
                    # Speak the reminder
                    try:
                        # Run in a new event loop to avoid conflicts with existing loops
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(TextToSpeech(reminder_msg))
                        loop.close()
                    except Exception as e:
                        # If TTS fails, just print the message
                        print(f"[Reminder] {reminder_msg}")
                        print(f"[Reminder] TTS Error: {e}")
                
                # Wait for 10 minutes before next check
                for _ in range(600):  # 600 seconds = 10 minutes
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[Reminder Service] Error in reminder loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying if there's an error
    
    def check_reminders_now(self):
        """Manually check for reminders now"""
        reminder_msg = self.calendar_integration.check_daily_reminders()
        if reminder_msg:
            print(f"[Manual Check] {reminder_msg}")
            try:
                # Run in a new event loop to avoid conflicts with existing loops
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(TextToSpeech(reminder_msg))
                loop.close()
            except Exception as e:
                print(f"[Manual Check] {reminder_msg}")
                print(f"[Manual Check] TTS Error: {e}")
        else:
            print("[Manual Check] No upcoming reminders")


# Global instance for the reminder service
reminder_service = DailyReminderChecker()

def start_reminder_service():
    """Start the daily reminder service"""
    reminder_service.start_reminder_service()

def stop_reminder_service():
    """Stop the daily reminder service"""
    reminder_service.stop_reminder_service()

def check_reminders_now():
    """Manually check for reminders"""
    reminder_service.check_reminders_now()


if __name__ == "__main__":
    print("Testing reminder service...")
    
    # Start the service
    start_reminder_service()
    
    print("Reminder service started. Checking for any immediate reminders...")
    check_reminders_now()
    
    try:
        # Keep the service running for testing
        print("Service is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping reminder service...")
        stop_reminder_service()
        print("Reminder service stopped.")