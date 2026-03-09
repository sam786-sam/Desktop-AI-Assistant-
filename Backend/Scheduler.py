# --- START OF FILE Scheduler.py ---

import time
import schedule
import threading
from rich import print

def SetReminder(reminder_time: str, message: str):
    """
    Sets a reminder for a specific time.

    Args:
        reminder_time (str): The time to set the reminder (e.g., "10:30", "14:00").
        message (str): The message for the reminder.
    """
    try:
        schedule.every().day.at(reminder_time).do(play_reminder_sound_and_notify, message)
        print(f"[Scheduler] Reminder set for {reminder_time} with message: '{message}'")
        return True
    except schedule.ScheduleValueError as e:
        print(f"[Scheduler] Invalid time format for reminder: {e}")
        return False
    except Exception as e:
        print(f"[Scheduler] Error setting reminder: {e}")
        return False

def ScheduleTask(task_time: str, task_func, *args):
    """
    Schedules a one-time or recurring task.

    Args:
        task_time (str): Time for the task (e.g., "10:30", "15:00").
        task_func (function): The function to be executed.
        *args: Arguments for the function.
    """
    try:
        schedule.every().day.at(task_time).do(task_func, *args)
        print(f"[Scheduler] Task scheduled at {task_time}")
        return True
    except schedule.ScheduleValueError as e:
        print(f"[Scheduler] Invalid time format for task: {e}")
        return False
    except Exception as e:
        print(f"[Scheduler] Error scheduling task: {e}")
        return False

def run_pending_schedules():
    """Continuously runs pending scheduled jobs in a separate thread."""
    while True:
        try:
            schedule.run_pending()
            time.sleep(1) # Wait a second before checking again
        except Exception as e:
            print(f"[Scheduler] Error during schedule run: {e}")
            time.sleep(5) # Wait longer on error

def start_scheduler():
    """Starts the scheduler thread."""
    scheduler_thread = threading.Thread(target=run_pending_schedules, daemon=True)
    scheduler_thread.start()
    print("[Scheduler] Scheduler thread started.")

def play_reminder_sound_and_notify(message):
    """Play reminder sound and show notification with TextToSpeech integration."""
    try:
        print(f"\n[Scheduler] 🔔 REMINDER: {message}")
        
        # Try to integrate with TextToSpeech
        try:
            import asyncio
            from TextToSpeech import TextToSpeech
            from Frontend.GUI import SetAssistantStatus, ShowTextToScreen
            
            # Set GUI status
            SetAssistantStatus(f"Reminder: {message}")
            ShowTextToScreen(f"⏰ Reminder: {message}")
            
            # Create new event loop for TTS if needed
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, schedule the task
                    asyncio.create_task(TextToSpeech(f"Reminder: {message}"))
                else:
                    # If no loop is running, run it
                    asyncio.run(TextToSpeech(f"Reminder: {message}"))
            except:
                # Fallback to just running TTS
                asyncio.run(TextToSpeech(f"Reminder: {message}"))
                
        except ImportError:
            print("[Scheduler] TextToSpeech not available, using system notification")
            # Fallback to system notification
            try:
                import subprocess
                subprocess.run([
                    'powershell', '-Command',
                    f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("{message}", "Jarvis Reminder", "OK", "Information")'
                ], check=False)
            except:
                pass
        
        print(f"[Scheduler] ✅ Reminder notification sent: {message}")
        
    except Exception as e:
        print(f"[Scheduler] ❌ Error in reminder notification: {e}")
    
    return schedule.CancelJob

# Example usage for testing
if __name__ == "__main__":
    start_scheduler()
    SetReminder("20:00", "Take out the trash")
    # To keep the main thread alive for the scheduler to work
    while True:
        time.sleep(1)