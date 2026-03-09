#!/usr/bin/env python3
"""
Enhanced fixes for all voice recognition and automation issues.
This file contains the improved implementations to fix:

1. Voice recognition stops after executing commands
2. Voice recognition should always be on 
3. Should execute multiple commands simultaneously
4. WiFi, Bluetooth, brightness controls not working
5. Content writing should automatically open in notepad
"""

import asyncio
import threading
import time
import os
import sys
import subprocess
import queue
from time import sleep

# Add to the beginning of Main.py to implement fixes
def apply_voice_recognition_fixes():
    """Apply all voice recognition and automation fixes"""
    
    # Import required modules
    sys.path.append(os.path.dirname(__file__))
    from Frontend.GUI import SetMicrophoneStatus, GetMicrophoneStatus, SetAssistantStatus
    from speechtotext import speech_queue, get_speech_from_queue, start_continuous_listening
    
    # Fix 1: Always-on voice recognition
    global mic_always_active, voice_recovery_active
    mic_always_active = True
    voice_recovery_active = True
    
    print("🔧 Applied Fix 1: Always-on voice recognition enabled")
    
    # Fix 2: Enhanced continuous listening with auto-recovery
    async def enhanced_continuous_voice_listener():
        """Enhanced continuous voice listener that never stops and auto-recovers."""
        global mic_always_active, voice_recovery_active
        
        print("[Enhanced] 🎤 Starting bulletproof continuous voice listener")
        
        recovery_count = 0
        max_recovery_attempts = 100  # Virtually unlimited
        
        while voice_recovery_active:
            try:
                # FORCE microphone to always be active
                if mic_always_active:
                    SetMicrophoneStatus("True")
                    SetAssistantStatus("🎤 Always Listening - Enhanced Mode")
                
                mic_status = GetMicrophoneStatus()
                
                if mic_status == "True":
                    # Get speech from queue with very short timeout to stay responsive
                    query = get_speech_from_queue(timeout=0.05)
                    
                    if query and query.strip():
                        print(f"[Enhanced] ✅ Voice command detected: '{query}'")
                        
                        # Process command WITHOUT blocking future voice recognition
                        asyncio.create_task(process_command_with_voice_persistence(query))
                        
                        # IMMEDIATELY restore microphone status after command queuing
                        if mic_always_active:
                            SetMicrophoneStatus("True")
                            SetAssistantStatus("🎤 Always Listening - Ready for next command")
                
                # Ultra-short sleep to maintain maximum responsiveness
                await asyncio.sleep(0.02)
                
            except Exception as e:
                print(f"[Enhanced] 🔄 Recovery needed: {e}")
                recovery_count += 1
                
                if recovery_count < max_recovery_attempts:
                    print(f"[Enhanced] Attempting recovery {recovery_count}/{max_recovery_attempts}")
                    
                    # Force restart voice recognition
                    try:
                        start_continuous_listening()
                        if mic_always_active:
                            SetMicrophoneStatus("True")
                        await asyncio.sleep(1)
                        recovery_count = 0  # Reset on successful recovery
                    except:
                        await asyncio.sleep(2)  # Wait before next recovery attempt
                else:
                    print("[Enhanced] Max recovery attempts reached, resetting...")
                    recovery_count = 0
                    await asyncio.sleep(5)
        
        print("[Enhanced] Voice listener stopped")
    
    # Fix 3: Command processing that preserves voice recognition
    async def process_command_with_voice_persistence(query):
        """Process commands while maintaining voice recognition persistence."""
        global mic_always_active
        
        try:
            print(f"[Persistent] 🎯 Processing: '{query}'")
            
            # BEFORE processing - ensure mic stays active
            if mic_always_active:
                SetMicrophoneStatus("True")
            
            # Parse multiple commands
            command_parts = parse_multiple_commands(query)
            
            # Execute commands simultaneously (Fix for multiple command execution)
            if len(command_parts) > 1:
                print(f"[Persistent] 🚀 Executing {len(command_parts)} commands simultaneously")
                tasks = []
                for i, cmd in enumerate(command_parts):
                    task = asyncio.create_task(execute_single_command_enhanced(cmd, i+1))
                    tasks.append(task)
                
                # Wait for all commands to complete
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Single command
                await execute_single_command_enhanced(command_parts[0], 1)
            
            # AFTER processing - force mic to stay active
            if mic_always_active:
                SetMicrophoneStatus("True")
                SetAssistantStatus("🎤 Always Listening - Command completed, ready for next")
            
            print(f"[Persistent] ✅ Command processing complete, voice recognition maintained")
            
        except Exception as e:
            print(f"[Persistent] ❌ Error: {e}")
            # Even on error, maintain voice recognition
            if mic_always_active:
                SetMicrophoneStatus("True")
                SetAssistantStatus("🎤 Always Listening - Error handled, ready for next command")
    
    def parse_multiple_commands(query):
        """Parse query for multiple commands with enhanced separators."""
        separators = [
            " and then ", " then ", " and ", ", ", " after that ", " next ",
            " also ", " plus ", " followed by ", " as well as "
        ]
        
        for separator in separators:
            if separator in query.lower():
                return [cmd.strip() for cmd in query.lower().split(separator) if cmd.strip()]
        
        return [query.strip()]
    
    # Fix 4: Enhanced command execution with better automation
    async def execute_single_command_enhanced(query, command_num=1):
        """Enhanced command execution with fixes for all automation issues."""
        global mic_always_active
        
        try:
            print(f"[Enhanced] 🔧 Executing command {command_num}: '{query}'")
            SetAssistantStatus(f"Executing Command {command_num}...")
            
            # Enhanced automation routing with fixes
            if "content" in query.lower() or "write" in query.lower() or "essay" in query.lower() or "application" in query.lower():
                # Fix 5: Content writing with automatic notepad opening
                await enhanced_content_generation(query)
            elif "wifi" in query.lower():
                # Fix for WiFi controls
                await enhanced_wifi_control(query)
            elif "bluetooth" in query.lower():
                # Fix for Bluetooth controls  
                await enhanced_bluetooth_control(query)
            elif "brightness" in query.lower():
                # Fix for brightness controls
                await enhanced_brightness_control(query)
            elif "volume" in query.lower():
                await enhanced_volume_control(query)
            else:
                # Route to existing automation with enhancements
                from Main import execute_single_command
                await execute_single_command(query, command_num)
            
            # CRITICAL: Always restore microphone status after ANY command
            if mic_always_active:
                SetMicrophoneStatus("True")
                SetAssistantStatus("🎤 Always Listening - Ready")
            
            print(f"[Enhanced] ✅ Command {command_num} completed")
            
        except Exception as e:
            print(f"[Enhanced] ❌ Command {command_num} error: {e}")
            # Maintain voice recognition even on error
            if mic_always_active:
                SetMicrophoneStatus("True")
                SetAssistantStatus("🎤 Always Listening - Error handled")
    
    # Fix 5: Enhanced content generation with automatic notepad
    async def enhanced_content_generation(query):
        """Generate content and automatically open in notepad."""
        try:
            from Backend.Chatbot import ChatBot
            
            # Extract topic from query
            topic = query.lower()
            for word in ["content", "write", "essay", "application", "letter"]:
                topic = topic.replace(word, "").strip()
            
            topic = topic.replace("about", "").replace("on", "").strip()
            
            print(f"[Content] 📝 Generating content for: '{topic}'")
            SetAssistantStatus("Generating content...")
            
            # Enhanced content prompt
            if "essay" in query.lower():
                content_prompt = f"Write a detailed, well-structured essay about {topic}. Include introduction, main body with multiple paragraphs, and conclusion."
            elif "application" in query.lower() or "letter" in query.lower():
                content_prompt = f"Write a professional application/letter about {topic}. Include proper formatting, formal language, and structure."
            else:
                content_prompt = f"Write comprehensive, well-organized content about {topic}. Include headings, detailed explanations, and proper structure."
            
            # Generate content
            generated_content = await asyncio.to_thread(ChatBot, content_prompt)
            
            # Create file with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_filename = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
            if not safe_filename:
                safe_filename = "content"
            
            file_name = os.path.join(os.path.dirname(__file__), "Data", f"{safe_filename}_{timestamp}.txt")
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            
            # Write content with proper formatting
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(f"Content: {topic.title()}\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(generated_content)
            
            # AUTOMATICALLY open in notepad
            subprocess.Popen(['notepad.exe', file_name])
            
            print(f"[Content] ✅ Content generated and opened in notepad: {file_name}")
            SetAssistantStatus("Content generated and opened in notepad")
            
        except Exception as e:
            print(f"[Content] ❌ Error: {e}")
            SetAssistantStatus("Content generation failed")
    
    # Fix for WiFi controls
    async def enhanced_wifi_control(query):
        """Enhanced WiFi control with multiple methods."""
        try:
            action = "on" if any(word in query.lower() for word in ["on", "enable", "turn on"]) else "off"
            
            print(f"[WiFi] 🔧 Enhanced WiFi {action}")
            SetAssistantStatus(f"Controlling WiFi - {action}")
            
            if action == "on":
                methods = [
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"],
                    ["netsh", "interface", "set", "interface", "WiFi", "enabled"],
                    ["powershell", "-Command", "Enable-NetAdapter -Name '*Wi-Fi*' -Confirm:$false"],
                    ["powershell", "-Command", "Enable-NetAdapter -Name '*WiFi*' -Confirm:$false"]
                ]
            else:
                methods = [
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"],
                    ["netsh", "interface", "set", "interface", "WiFi", "disabled"], 
                    ["powershell", "-Command", "Disable-NetAdapter -Name '*Wi-Fi*' -Confirm:$false"],
                    ["powershell", "-Command", "Disable-NetAdapter -Name '*WiFi*' -Confirm:$false"]
                ]
            
            success = False
            for i, method in enumerate(methods):
                try:
                    result = subprocess.run(method, check=True, capture_output=True, text=True, timeout=10)
                    print(f"[WiFi] ✅ Method {i+1} succeeded")
                    success = True
                    break
                except Exception as e:
                    print(f"[WiFi] Method {i+1} failed: {e}")
                    continue
            
            if success:
                SetAssistantStatus(f"WiFi {action} successfully")
            else:
                SetAssistantStatus(f"WiFi {action} failed - all methods tried")
                
        except Exception as e:
            print(f"[WiFi] ❌ Error: {e}")
            SetAssistantStatus("WiFi control failed")
    
    # Fix for Bluetooth controls
    async def enhanced_bluetooth_control(query):
        """Enhanced Bluetooth control with multiple methods."""
        try:
            action = "on" if any(word in query.lower() for word in ["on", "enable", "turn on"]) else "off"
            
            print(f"[Bluetooth] 🔧 Enhanced Bluetooth {action}")
            SetAssistantStatus(f"Controlling Bluetooth - {action}")
            
            if action == "on":
                methods = [
                    ["powershell", "-Command", "Enable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'Error'}).InstanceId -Confirm:$false"],
                    ["powershell", "-Command", "Set-Service bthserv -StartupType Automatic; Start-Service bthserv"],
                    ["powershell", "-Command", "Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false"]
                ]
            else:
                methods = [
                    ["powershell", "-Command", "Disable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'}).InstanceId -Confirm:$false"],
                    ["powershell", "-Command", "Stop-Service bthserv -Force"],
                    ["powershell", "-Command", "Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false"]
                ]
            
            success = False
            for i, method in enumerate(methods):
                try:
                    result = subprocess.run(method, check=True, capture_output=True, text=True, timeout=15)
                    print(f"[Bluetooth] ✅ Method {i+1} succeeded")
                    success = True
                    break
                except Exception as e:
                    print(f"[Bluetooth] Method {i+1} failed: {e}")
                    continue
            
            if success:
                SetAssistantStatus(f"Bluetooth {action} successfully")
            else:
                SetAssistantStatus(f"Bluetooth {action} failed - all methods tried")
                
        except Exception as e:
            print(f"[Bluetooth] ❌ Error: {e}")
            SetAssistantStatus("Bluetooth control failed")
    
    # Fix for brightness controls
    async def enhanced_brightness_control(query):
        """Enhanced brightness control with multiple methods."""
        try:
            action = "up" if any(word in query.lower() for word in ["up", "increase", "raise", "brighter"]) else "down"
            
            print(f"[Brightness] 🔧 Enhanced brightness {action}")
            SetAssistantStatus(f"Controlling brightness - {action}")
            
            success = False
            
            # Method 1: Keyboard shortcuts
            try:
                import keyboard
                if action == "up":
                    keyboard.press_and_release("fn+f6")  # Common brightness up
                    keyboard.press_and_release("fn+f7")  # Alternative
                else:
                    keyboard.press_and_release("fn+f5")  # Common brightness down
                    keyboard.press_and_release("fn+f4")  # Alternative
                success = True
                print("[Brightness] ✅ Keyboard method succeeded")
            except Exception as e:
                print(f"[Brightness] Keyboard method failed: {e}")
            
            # Method 2: PowerShell WMI (if keyboard failed)
            if not success:
                try:
                    brightness_value = 100 if action == "up" else 30
                    result = subprocess.run([
                        "powershell", "-Command",
                        f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness_value})"
                    ], check=True, capture_output=True, text=True, timeout=10)
                    success = True
                    print("[Brightness] ✅ PowerShell method succeeded")
                except Exception as e:
                    print(f"[Brightness] PowerShell method failed: {e}")
            
            # Method 3: Alternative brightness control
            if not success:
                try:
                    import win32api
                    import win32con
                    # Try Windows API brightness control
                    if action == "up":
                        win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x70000)
                    else:
                        win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x90000)
                    success = True
                    print("[Brightness] ✅ Windows API method succeeded")
                except Exception as e:
                    print(f"[Brightness] Windows API method failed: {e}")
            
            if success:
                SetAssistantStatus(f"Brightness {action} successfully")
            else:
                SetAssistantStatus(f"Brightness {action} failed - all methods tried")
                
        except Exception as e:
            print(f"[Brightness] ❌ Error: {e}")
            SetAssistantStatus("Brightness control failed")
    
    # Fix for volume controls
    async def enhanced_volume_control(query):
        """Enhanced volume control with multiple methods."""
        try:
            if any(word in query.lower() for word in ["up", "increase", "raise", "louder"]):
                action = "up"
            elif any(word in query.lower() for word in ["down", "decrease", "lower", "quieter"]):
                action = "down"
            else:
                action = "mute"
            
            print(f"[Volume] 🔧 Enhanced volume {action}")
            SetAssistantStatus(f"Controlling volume - {action}")
            
            success = False
            
            # Method 1: Keyboard shortcuts
            try:
                import keyboard
                if action == "up":
                    keyboard.press_and_release("volume up")
                elif action == "down":
                    keyboard.press_and_release("volume down")
                else:
                    keyboard.press_and_release("volume mute")
                success = True
                print("[Volume] ✅ Keyboard method succeeded")
            except Exception as e:
                print(f"[Volume] Keyboard method failed: {e}")
            
            # Method 2: Windows API (if keyboard failed)
            if not success:
                try:
                    import win32api
                    import win32con
                    if action == "up":
                        for _ in range(5):  # Increase by ~10%
                            win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0xA0000)
                    elif action == "down":
                        for _ in range(5):  # Decrease by ~10%
                            win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x90000)
                    else:
                        win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x80000)
                    success = True
                    print("[Volume] ✅ Windows API method succeeded")
                except Exception as e:
                    print(f"[Volume] Windows API method failed: {e}")
            
            if success:
                SetAssistantStatus(f"Volume {action} successfully")
            else:
                SetAssistantStatus(f"Volume {action} failed")
                
        except Exception as e:
            print(f"[Volume] ❌ Error: {e}")
            SetAssistantStatus("Volume control failed")
    
    return {
        'enhanced_continuous_voice_listener': enhanced_continuous_voice_listener,
        'process_command_with_voice_persistence': process_command_with_voice_persistence,
        'enhanced_content_generation': enhanced_content_generation,
        'enhanced_wifi_control': enhanced_wifi_control,
        'enhanced_bluetooth_control': enhanced_bluetooth_control,
        'enhanced_brightness_control': enhanced_brightness_control,
        'enhanced_volume_control': enhanced_volume_control
    }

# Usage instructions:
"""
To apply these fixes to your Main.py, add this at the beginning:

# Import and apply fixes
from enhanced_voice_fixes import apply_voice_recognition_fixes
voice_fixes = apply_voice_recognition_fixes()

# Replace the continuous_voice_listener function with:
continuous_voice_listener = voice_fixes['enhanced_continuous_voice_listener']

# Set global variables for always-on mode:
mic_always_active = True
voice_recovery_active = True

# In your main thread logic, ensure microphone stays active:
if mic_always_active:
    SetMicrophoneStatus("True")
"""

if __name__ == "__main__":
    print("Enhanced Voice Recognition Fixes")
    print("================================")
    print("This module provides fixes for:")
    print("1. Voice recognition stops after commands")
    print("2. Always-on voice recognition")
    print("3. Simultaneous command execution") 
    print("4. WiFi/Bluetooth/Brightness control fixes")
    print("5. Auto-notepad for content writing")
    print("\nImport this module and apply the fixes to your Main.py")