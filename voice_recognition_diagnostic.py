#!/usr/bin/env python3
"""
Voice Recognition Diagnostic Tool
This script helps diagnose why voice recognition stops working after executing commands.
"""

import asyncio
import sys
import os
import time
import threading
import json
from datetime import datetime

# Add paths
sys.path.append(os.path.dirname(__file__))

# Import modules
from speechtotext import (
    speech_queue, continuous_active,
    get_speech_from_queue, clear_speech_queue,
    start_continuous_listening, stop_continuous_listening
)

from Main import (
    active_tasks, continuous_listening_active,
    process_command_non_blocking
)

from Frontend.GUI import (
    GetMicrophoneStatus, SetMicrophoneStatus,
    GetAssistantStatus, SetAssistantStatus
)

class VoiceRecognitionDiagnostic:
    """Diagnostic tool for voice recognition issues."""
    
    def __init__(self):
        self.log_entries = []
        self.monitoring = False
        self.start_time = datetime.now()
    
    def log(self, message, level="INFO"):
        """Log diagnostic information."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "continuous_active": continuous_active,
            "driver_ready": driver_ready,
            "continuous_listening_active": continuous_listening_active,
            "mic_status": GetMicrophoneStatus(),
            "assistant_status": GetAssistantStatus(),
            "queue_size": speech_queue.qsize(),
            "active_tasks_count": len(active_tasks)
        }
        self.log_entries.append(entry)
        print(f"[{timestamp}] {level}: {message}")
    
    async def start_monitoring(self):
        """Start monitoring voice recognition system."""
        self.log("Starting voice recognition monitoring", "SYSTEM")
        self.monitoring = True
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_system_state())
        
        return monitor_task
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
        self.log("Stopping voice recognition monitoring", "SYSTEM")
    
    async def _monitor_system_state(self):
        """Monitor system state continuously."""
        last_states = {}
        
        while self.monitoring:
            current_states = {
                "continuous_active": continuous_active,
                "driver_ready": driver_ready,
                "continuous_listening_active": continuous_listening_active,
                "mic_status": GetMicrophoneStatus(),
                "queue_size": speech_queue.qsize(),
                "active_tasks_count": len(active_tasks)
            }
            
            # Log state changes
            for key, value in current_states.items():
                if key not in last_states or last_states[key] != value:
                    self.log(f"State change: {key} = {value}", "STATE")
            
            last_states = current_states.copy()
            
            # Check for potential issues
            await self._check_for_issues(current_states)
            
            await asyncio.sleep(0.5)  # Monitor every 500ms
    
    async def _check_for_issues(self, states):
        """Check for potential issues in the current state."""
        
        # Issue 1: Driver ready but continuous not active
        if states["driver_ready"] and not states["continuous_active"]:
            self.log("ISSUE: Driver ready but continuous listening not active", "WARNING")
        
        # Issue 2: Microphone on but no continuous listening
        if states["mic_status"] == "True" and not states["continuous_listening_active"]:
            self.log("ISSUE: Microphone on but continuous listening not active", "WARNING")
        
        # Issue 3: Queue growing without being processed
        if states["queue_size"] > 5:
            self.log(f"ISSUE: Speech queue growing: {states['queue_size']} items", "WARNING")
        
        # Issue 4: Too many active tasks
        if states["active_tasks_count"] > 10:
            self.log(f"ISSUE: Too many active tasks: {states['active_tasks_count']}", "WARNING")
        
        # Issue 5: Continuous listening should be active but isn't
        if states["mic_status"] == "True" and not any([
            states["continuous_active"],
            states["continuous_listening_active"]
        ]):
            self.log("ISSUE: Microphone active but no listening threads active", "ERROR")
    
    async def run_diagnostic_sequence(self):
        """Run a diagnostic sequence to test voice recognition."""
        self.log("Starting diagnostic sequence", "DIAGNOSTIC")
        
        # Start monitoring
        monitor_task = await self.start_monitoring()
        
        try:
            # Test 1: Basic voice recognition setup
            await self._test_basic_setup()
            
            # Test 2: Command processing
            await self._test_command_processing()
            
            # Test 3: Recovery after commands
            await self._test_recovery_after_commands()
            
            # Test 4: Stress test with multiple commands
            await self._test_multiple_commands()
            
        finally:
            self.stop_monitoring()
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _test_basic_setup(self):
        """Test basic voice recognition setup."""
        self.log("Testing basic voice recognition setup", "TEST")
        
        # Check initial state
        self.log(f"Initial continuous_active: {continuous_active}")
        self.log(f"Initial driver_ready: {driver_ready}")
        self.log(f"Initial mic status: {GetMicrophoneStatus()}")
        
        # Try to start voice recognition
        SetMicrophoneStatus("True")
        await asyncio.sleep(0.5)
        
        # Check if voice recognition started
        if not continuous_active:
            self.log("Voice recognition not starting automatically", "WARNING")
            try:
                start_continuous_listening()
                await asyncio.sleep(1)
                self.log("Manually started continuous listening", "INFO")
            except Exception as e:
                self.log(f"Failed to start continuous listening: {e}", "ERROR")
    
    async def _test_command_processing(self):
        """Test command processing impact on voice recognition."""
        self.log("Testing command processing impact", "TEST")
        
        # Add test commands to queue
        test_commands = ["test command 1", "test command 2", "test command 3"]
        
        for i, cmd in enumerate(test_commands):
            self.log(f"Processing test command {i+1}: {cmd}")
            
            # Add to speech queue
            speech_queue.put(cmd)
            
            # Process the command
            try:
                await process_command_non_blocking(cmd)
                self.log(f"Command {i+1} processed successfully")
            except Exception as e:
                self.log(f"Command {i+1} processing failed: {e}", "ERROR")
            
            # Check voice recognition state after each command
            await asyncio.sleep(0.5)
            self._check_voice_recognition_health()
    
    async def _test_recovery_after_commands(self):
        """Test voice recognition recovery after commands."""
        self.log("Testing voice recognition recovery", "TEST")
        
        # Wait a bit after previous commands
        await asyncio.sleep(2)
        
        # Check if voice recognition is still responsive
        test_input = "recovery test input"
        speech_queue.put(test_input)
        
        # Try to retrieve it
        retrieved = get_speech_from_queue(timeout=1.0)
        if retrieved == test_input:
            self.log("Voice recognition recovery: SUCCESS", "SUCCESS")
        else:
            self.log(f"Voice recognition recovery: FAILED - Expected '{test_input}', got '{retrieved}'", "ERROR")
    
    async def _test_multiple_commands(self):
        """Test with multiple rapid commands (reproducing the reported issue)."""
        self.log("Testing multiple rapid commands", "TEST")
        
        # Simulate the reported problem scenario
        rapid_commands = [
            "open notepad",
            "google search test",
            "volume up",
            "close notepad",
            "youtube search music",
            "brightness up"
        ]
        
        for i, cmd in enumerate(rapid_commands):
            self.log(f"Rapid command {i+1}: {cmd}")
            
            speech_queue.put(cmd)
            
            # Process with minimal delay (simulating rapid user input)
            try:
                await process_command_non_blocking(cmd)
            except Exception as e:
                self.log(f"Rapid command {i+1} failed: {e}", "ERROR")
            
            # Very short delay
            await asyncio.sleep(0.1)
            
            # Check voice recognition health
            if not self._check_voice_recognition_health():
                self.log(f"Voice recognition failed after rapid command {i+1}", "ERROR")
                break
        
        # Final check
        await asyncio.sleep(1)
        final_test = "final test after rapid commands"
        speech_queue.put(final_test)
        final_result = get_speech_from_queue(timeout=1.0)
        
        if final_result == final_test:
            self.log("Voice recognition survived rapid commands: SUCCESS", "SUCCESS")
        else:
            self.log("Voice recognition failed after rapid commands: FAILURE", "ERROR")
    
    def _check_voice_recognition_health(self):
        """Check if voice recognition is healthy."""
        health_issues = []
        
        # Check if continuous listening is active
        if not continuous_active and GetMicrophoneStatus() == "True":
            health_issues.append("Continuous listening not active")
        
        # Check if driver is ready
        if not driver_ready and GetMicrophoneStatus() == "True":
            health_issues.append("Driver not ready")
        
        # Check queue responsiveness
        test_item = f"health_check_{time.time()}"
        speech_queue.put(test_item)
        retrieved = get_speech_from_queue(timeout=0.1)
        if retrieved != test_item:
            health_issues.append("Speech queue not responsive")
        
        if health_issues:
            self.log(f"Voice recognition health issues: {', '.join(health_issues)}", "WARNING")
            return False
        else:
            self.log("Voice recognition health: OK", "INFO")
            return True
    
    def save_diagnostic_report(self):
        """Save diagnostic report to file."""
        report_path = os.path.join(os.path.dirname(__file__), "voice_diagnostic_report.json")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "session_duration": str(datetime.now() - self.start_time),
            "total_log_entries": len(self.log_entries),
            "log_entries": self.log_entries
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\nDiagnostic report saved to: {report_path}")
        return report_path
    
    def print_summary(self):
        """Print diagnostic summary."""
        print("\n" + "="*60)
        print("🔍 VOICE RECOGNITION DIAGNOSTIC SUMMARY")
        print("="*60)
        
        # Count log levels
        error_count = sum(1 for entry in self.log_entries if entry["level"] == "ERROR")
        warning_count = sum(1 for entry in self.log_entries if entry["level"] == "WARNING")
        success_count = sum(1 for entry in self.log_entries if entry["level"] == "SUCCESS")
        
        print(f"📊 Log Summary:")
        print(f"   Total entries: {len(self.log_entries)}")
        print(f"   Errors: {error_count}")
        print(f"   Warnings: {warning_count}")
        print(f"   Successes: {success_count}")
        
        # Show recent issues
        recent_issues = [entry for entry in self.log_entries[-20:] 
                        if entry["level"] in ["ERROR", "WARNING"]]
        
        if recent_issues:
            print(f"\n⚠️  Recent Issues:")
            for issue in recent_issues[-5:]:  # Show last 5 issues
                print(f"   [{issue['timestamp']}] {issue['level']}: {issue['message']}")
        else:
            print("\n✅ No recent issues detected")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if error_count > 0:
            print("   🔴 Critical issues found - voice recognition may be unstable")
            print("   🔧 Review error logs and check browser driver status")
        elif warning_count > 0:
            print("   🟡 Warning issues found - monitor voice recognition closely")
            print("   🔧 Check state synchronization between components")
        else:
            print("   🟢 Voice recognition appears to be working correctly")

async def run_voice_diagnostic():
    """Run the voice recognition diagnostic."""
    print("🔍 Voice Recognition Diagnostic Tool")
    print("===================================")
    print("This tool will help identify why voice recognition stops after executing commands.\n")
    
    diagnostic = VoiceRecognitionDiagnostic()
    
    try:
        await diagnostic.run_diagnostic_sequence()
    except KeyboardInterrupt:
        print("\n\n👋 Diagnostic interrupted by user")
    except Exception as e:
        diagnostic.log(f"Diagnostic error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        diagnostic.print_summary()
        diagnostic.save_diagnostic_report()

if __name__ == "__main__":
    try:
        asyncio.run(run_voice_diagnostic())
    except KeyboardInterrupt:
        print("\n\n👋 Diagnostic interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnostic tool error: {e}")
        import traceback
        traceback.print_exc()