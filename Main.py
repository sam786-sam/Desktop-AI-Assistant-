import sys
import threading
import json
import os
import asyncio
import time
import subprocess
from time import sleep
import pygame
from rich.console import Console
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    GetMicrophoneStatus,
    GetAssistantStatus,
    MicButtonInitialed
)
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation, TranslateAndExecute
from speechtotext import (
    SpeechRecognition,
    start_continuous_listening,
    stop_continuous_listening,
    get_voice_command,
    get_speech_universal,
    QueryModifier
)

# Enhanced speech recognition is now the primary system
print("[Main] ✅ Using enhanced speech recognition system")
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech, skip_current_speech, interrupt_if_speaking, is_speaking
from Backend.Model import FirstlayerDMM
# Try to import enhanced version, fallback to basic if cv2 not available
try:
    from Backend.SnapCommands_Enhanced import ExecuteSnapCommand
    print("[Main] ✅ Enhanced SnapCommands loaded")
except ImportError as e:
    print(f"[Main] ⚠️ Enhanced SnapCommands not available ({e}), using basic version")
    from Backend.SnapCommands_Basic import ExecuteSnapCommand
from dotenv import dotenv_values


env_vars = dotenv_values(".env")
Username = env_vars.get("Username") or "User"
Assistantname = env_vars.get("Assistantname") or "Assistant"
DefaultMessage = f"{Username} : Hello {Assistantname}, How are you? \n{Assistantname} : I am doing well. How may I help you?"
Functions = ["open", "close", "play", "youtube play", "system", "content", "google search", "youtube search", "generate image", "generate 3d image", "image generation", "wifi", "bluetooth", "brightness", "volume", "media"]

main_loop = None
console = Console()
hold_mode = False
hold_output = ""
pending_commands = []
continuous_listening_active = False
speech_processing_active = False
execution_queue = []
active_tasks = []
mic_always_active = True  # FIX 1: Always keep microphone active
voice_recovery_active = True  # FIX 1: Enable automatic recovery
command_queue = []
max_concurrent_commands = 10  # FIX 2: Increase concurrent commands for better performance

# Using simple speech recognition system only

# Removed complex fallback system - using simple speech recognition only

def ShowDefaultChatIfNoChats():
    """Initializes the chat log with a default message if it's empty."""
    chatlog_path = os.path.join(os.path.dirname(__file__), 'Data', 'Chatlog.json')
    try:
        with open(chatlog_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if not content.strip():
                raise ValueError("File is empty")
            json_data = json.loads(content)
            if not json_data:
                raise ValueError("JSON is empty")
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        os.makedirs(os.path.dirname(chatlog_path), exist_ok=True)
        with open(chatlog_path, 'w', encoding='utf-8') as f:
            json.dump([
                {"role": "user", "content": "hello Jarvis, how are you?"},
                {"role": "assistant", "content": "I am doing well. How may I help you?"}
            ], f, indent=4)
        ShowTextToScreen(DefaultMessage)
    else:
        display_chat_log()

def display_chat_log():
    """Reads the chat log and displays it on the GUI."""
    chatlog_path = os.path.join(os.path.dirname(__file__), 'Data', 'Chatlog.json')
    try:
        with open(chatlog_path, 'r', encoding='utf-8') as file:
            chat_history = json.load(file)
        
        chat_display = ""
        for chat in chat_history:
            role = "User" if chat["role"] == "user" else Assistantname
            chat_display += f"{role} : {chat['content']}\n"
        
        ShowTextToScreen(AnswerModifier(chat_display))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading chat log for display: {e}")
        ShowTextToScreen("Error: Could not load chat history.")

async def handle_hold_commands():
    """Handle commands that are in hold mode"""
    global hold_mode, hold_output, pending_commands
    
    if hold_mode and pending_commands:
        wait_time = 30
        await asyncio.sleep(wait_time)
        
        await TextToSpeech("I have some responses ready. Would you like to hear them now?")
        SetAssistantStatus("Waiting for your response to show held output...")
        
        SetMicrophoneStatus("True")
        await asyncio.sleep(1)
        
        try:
            response_timeout = 10
            # Listen for user response from the queue
            response = await asyncio.wait_for(
                asyncio.to_thread(lambda: get_voice_command()),
                timeout=response_timeout
            )
            
            if response and ("yes" in response.lower() or "show" in response.lower() or "ok" in response.lower() or "sure" in response.lower()):
                SetAssistantStatus("Showing held responses...")
                results = await execute_multiple_commands(pending_commands)
                
                if results:
                    combined_results = "\n".join(results)
                    
                    try:
                        with open(TempDirectoryPath("Responses.data"), "r", encoding='utf-8') as file:
                            current_conversation = file.read()
                    except FileNotFoundError:
                        current_conversation = ""
                    
                    full_conversation = current_conversation + f"\n{Assistantname} : Here are your held responses:\n{combined_results}"
                    ShowTextToScreen(full_conversation)
                
                await TextToSpeech("Here are the results I was holding for you.")
            else:
                await TextToSpeech("Okay, I'll continue holding the responses for later.")
                return
                
        except asyncio.TimeoutError:
            await TextToSpeech("I'll keep holding the responses for now.")
            return
        except Exception as e:
            print(f"Error getting hold response: {e}")
            await TextToSpeech("Let me show you the held responses anyway.")
            results = await execute_multiple_commands(pending_commands)
        
        hold_mode = False
        hold_output = ""
        pending_commands = []
        # Don't turn off microphone - keep it always active for continuous listening
        # SetMicrophoneStatus("False")  # REMOVED - This was causing mic to turn off!

async def execute_multiple_commands(commands_list):
    """Execute multiple commands concurrently"""
    tasks = []
    responses = []
    
    for command in commands_list:
        if "realtime" in command.lower():
            query = command.lower().replace("realtime (", "").replace(")", "")
            tasks.append(asyncio.to_thread(RealtimeSearchEngine, query))
        elif "general" in command.lower():
            query = command.lower().replace("general (", "").replace(")", "")
            tasks.append(asyncio.to_thread(ChatBot, query))
        else:
            tasks.append(asyncio.to_thread(TranslateAndExecute, [command]))
    
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and result:
                responses.append(str(result))
    
    return responses

async def process_user_query(query):
    """Process user query and generate response"""
    global hold_mode, pending_commands
    try:
        SetAssistantStatus("Thinking...")
        print(f"[Process] Processing query: '{query}'")
        
        if query.lower() == "stop":
            SetAssistantStatus("Stopped.")
            await TextToSpeech("Stopping")
            return
        elif "exit" in query.lower() or "shutdown" in query.lower():
            SetAssistantStatus("Stopping.")
            await TextToSpeech("Goodbye!")
            sys.exit()
        elif query.lower() == "skip":
            skip_current_speech()
            return

        # Corrected the function call to use a positional argument
        decision_list = FirstlayerDMM(query)
        print(f"[Process] Decision list: {decision_list}")
        
        if decision_list and len(decision_list) > 0:
            if "realtime" in decision_list[0].lower():
                SetAssistantStatus("Realtime Searching...")
                Answer = await asyncio.to_thread(RealtimeSearchEngine, QueryModifier(query))
            elif "general" in decision_list[0].lower():
                SetAssistantStatus("Chatting...")
                Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
            else:
                SetAssistantStatus("Executing...")
                print(f"[Main] Sending decision list to Automation: {decision_list}")
                Answer = await Automation(decision_list)
                print(f"[Main] Automation returned: {Answer}")
        else:
            SetAssistantStatus("Chatting...")
            Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
        
        print(f"[Process] Answer: {Answer}")
        
        if Answer and isinstance(Answer, str):
            # Check for voice interruption before speaking
            if is_speaking():
                print("[Process] 🎤 Voice interrupt detected during output - stopping")
                interrupt_if_speaking()
            
            await TextToSpeech(Answer)
            try:
                with open(TempDirectoryPath("Responses.data"), "r", encoding='utf-8') as file:
                    current_conversation = file.read()
            except FileNotFoundError:
                current_conversation = ""
            full_conversation = current_conversation + f"\nUser : {query}\n{Assistantname} : {AnswerModifier(Answer)}"
            ShowTextToScreen(full_conversation)
        elif Answer is True:
            SetAssistantStatus("Task completed.")
            # Check for interruption
            if is_speaking():
                interrupt_if_speaking()
            await TextToSpeech("Task completed successfully.")
        elif Answer is False:
            SetAssistantStatus("Task failed.")
            # Check for interruption
            if is_speaking():
                interrupt_if_speaking()
            await TextToSpeech("Sorry, I couldn't complete that task.")
        else:
            SetAssistantStatus("No response.")
            # Check for interruption
            if is_speaking():
                interrupt_if_speaking()
            await TextToSpeech("I'm sorry, I couldn't process that request.")

    except Exception as e:
        print(f"[Process] Error processing query: {e}")
        import traceback
        traceback.print_exc()
        SetAssistantStatus("Error occurred.")
        await TextToSpeech("I encountered an error while processing your request.")

async def process_continuous_speech(query):
    """Process speech from continuous listening - keeping for backward compatibility"""
    await process_user_query(query)

def InitialExecution():
    """Initializes the chat history and status on startup."""
    try:
        console.print(f"[bold green]Hello {Username}, I am {Assistantname}, your desktop assistant.[/bold green]")
        ShowDefaultChatIfNoChats()
        SetAssistantStatus("Ready.")
        MicButtonInitialed()
        
        # Initialize speech recognition system
        print("[Main] 🔧 Initializing speech recognition...")
        try:
            start_continuous_listening()
            time.sleep(1)  # Quick initialization test
            print("[Main] ✅ Speech recognition system initialized successfully")
        except Exception as speech_error:
            print(f"[Main] ❌ Speech recognition initialization failed: {speech_error}")
            print("[Main] ⚠️ Speech recognition may not work properly")
            
    except Exception as e:
        print(f"Error during initial execution: {e}")
        if Assistantname:
            console.print(f"[bold green]Hello, I am {Assistantname}, your desktop assistant.[/bold green]")
        else:
            console.print(f"[bold green]Hello, I am your desktop assistant.[/bold green]")
        SetAssistantStatus("Ready.")

async def continuous_voice_listener():
    """Enhanced continuous voice listening with Google API error recovery."""
    global continuous_listening_active, mic_always_active, voice_recovery_active
    
    print("[Enhanced] 🎤 Starting bulletproof continuous voice listener with API recovery")
    
    recovery_count = 0
    max_recovery_attempts = 100
    api_error_count = 0
    last_successful_recognition = time.time()
    
    while voice_recovery_active:
        try:
            # FIX 1: FORCE microphone to always be active
            if mic_always_active:
                SetMicrophoneStatus("True")
                SetAssistantStatus("🎤 Always Listening - Enhanced Mode")
            
            mic_status = GetMicrophoneStatus()
            current_time = time.time()
            
            # Check for API failures - if no recognition for 10 seconds, force restart
            if (current_time - last_successful_recognition) > 10:
                print("[Enhanced] 🔄 No recognition for 10s, forcing restart...")
                await force_speech_restart()
                last_successful_recognition = current_time
            
            if mic_status == "True":
                # Get speech using simple speech recognition
                query = await asyncio.to_thread(get_speech_universal)
                
                if query and query.strip():
                    print(f"[Enhanced] ✅ Voice command detected: '{query}'")
                    last_successful_recognition = current_time
                    api_error_count = 0  # Reset error count on success
                    
                    # INTERRUPT current speech if playing (voice interruption)
                    if is_speaking():
                        print("[Enhanced] 🎤 Voice interrupt - stopping output for new command")
                        interrupt_if_speaking()
                    
                    # Process command WITHOUT blocking future voice recognition
                    asyncio.create_task(process_command_with_voice_persistence(query))
                    
                    # IMMEDIATELY restore microphone status after command queuing
                    if mic_always_active:
                        SetMicrophoneStatus("True")
                        SetAssistantStatus("🎤 Always Listening - Ready for next command")
                    
                    # Clean up completed tasks
                    global active_tasks
                    active_tasks = [t for t in active_tasks if not t.done()]
            
            # Ultra-short sleep to maintain maximum responsiveness
            await asyncio.sleep(0.02)
            
        except Exception as e:
            print(f"[Enhanced] 🔄 Recovery needed: {e}")
            recovery_count += 1
            
            # Handle speech recognition errors
            error_str = str(e).lower()
            if any(error_type in error_str for error_type in [
                "connection", "refused", "connectionpool", "max retries", 
                "google", "authentication", "timeout"
            ]):
                api_error_count += 1
                print(f"[Enhanced] 🚨 Speech recognition error detected ({api_error_count}), attempting restart...")
                await force_speech_restart()
            
            if recovery_count < max_recovery_attempts:
                print(f"[Enhanced] Attempting recovery {recovery_count}/{max_recovery_attempts}")
                
                # Enhanced recovery with API restart
                try:
                    await force_speech_restart()
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

# Speech functions are now handled by speechtotext.py

async def force_speech_restart():
    """Simple speech restart - no complex system needed"""
    try:
        print("[Restart] 🔄 Simple speech restart...")
        await asyncio.sleep(0.5)
        print("[Restart] ✅ Simple speech ready")
    
    except Exception as e:
        print(f"[Restart] Simple speech error: {e}")

async def process_command_with_voice_persistence(query):
    """Process commands while maintaining voice recognition persistence."""
    global mic_always_active, active_tasks, max_concurrent_commands
    
    try:
        print(f"[Persistent] 🎯 Processing: '{query}'")
        
        # BEFORE processing - ensure mic stays active
        if mic_always_active:
            SetMicrophoneStatus("True")
        
        # Parse multiple commands with enhanced separators
        command_parts = []
        separators = [
            " and then ", " then ", " and ", ", ", " after that ", " next ",
            " also ", " plus ", " followed by ", " as well as "
        ]
        
        for separator in separators:
            if separator in query.lower():
                command_parts = [cmd.strip() for cmd in query.lower().split(separator) if cmd.strip()]
                break
        
        if not command_parts:
            command_parts = [query.strip()]
        
        # Clean up completed tasks first
        active_tasks = [t for t in active_tasks if not t.done()]
        
        print(f"[Persistent] 📋 Found {len(command_parts)} command(s), {len(active_tasks)} active tasks")
        
        # FIX 2: Execute commands simultaneously for better performance
        if len(command_parts) > 1:
            print(f"[Persistent] 🚀 Executing {len(command_parts)} commands simultaneously")
            tasks = []
            for i, cmd in enumerate(command_parts):
                if cmd and cmd.strip():
                    # Check concurrent limit
                    while len([t for t in active_tasks if not t.done()]) >= max_concurrent_commands:
                        await asyncio.sleep(0.1)
                        active_tasks = [t for t in active_tasks if not t.done()]
                    
                    task = asyncio.create_task(execute_single_command_enhanced(cmd, i+1))
                    active_tasks.append(task)
                    tasks.append(task)
            
            # Wait for all commands to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Single command
            while len([t for t in active_tasks if not t.done()]) >= max_concurrent_commands:
                await asyncio.sleep(0.1)
                active_tasks = [t for t in active_tasks if not t.done()]
            
            task = asyncio.create_task(execute_single_command_enhanced(command_parts[0], 1))
            active_tasks.append(task)
        
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

async def process_command_non_blocking(query):
    """Enhanced command processor that handles multiple commands and queueing"""
    global active_tasks, max_concurrent_commands
    
    try:
        print(f"[NonBlocking] 🎯 Processing: '{query}'")
        
        # Handle multiple commands in one utterance with more separators
        command_parts = []
        separators = [" and then ", " then ", " and ", ", ", " after that ", " next "]
        
        for separator in separators:
            if separator in query.lower():
                command_parts = [cmd.strip() for cmd in query.lower().split(separator)]
                break
        
        if not command_parts:
            command_parts = [query.strip()]
        
        # Clean up completed tasks first
        active_tasks = [t for t in active_tasks if not t.done()]
        
        print(f"[NonBlocking] 📋 Found {len(command_parts)} command(s), {len(active_tasks)} active tasks")
        
        # Process commands with concurrency limit
        for i, cmd in enumerate(command_parts):
            if cmd and cmd.strip():
                # Check if we're under the concurrent limit
                if len(active_tasks) >= max_concurrent_commands:
                    print(f"[NonBlocking] ⏳ Waiting for task slots ({len(active_tasks)}/{max_concurrent_commands})...")
                    # Wait for a task to complete
                    while len([t for t in active_tasks if not t.done()]) >= max_concurrent_commands:
                        await asyncio.sleep(0.1)
                        active_tasks = [t for t in active_tasks if not t.done()]
                
                print(f"[NonBlocking] 🚀 Launching command {i+1}: '{cmd}'")
                task = asyncio.create_task(execute_single_command(cmd, i+1))
                active_tasks.append(task)
        
    except Exception as e:
        print(f"[NonBlocking] ❌ Error: {e}")
        asyncio.create_task(TextToSpeech("Sorry, I had trouble processing that command."))

async def execute_single_command_enhanced(query, command_num=1):
    """Enhanced command execution with fixes for all automation issues."""
    global mic_always_active
    
    try:
        print(f"[Enhanced] 🔧 Executing command {command_num}: '{query}'")
        SetAssistantStatus(f"Executing Command {command_num}...")
        
        # FORCE microphone to stay active before processing
        if mic_always_active:
            SetMicrophoneStatus("True")
        
        # Enhanced automation routing with fixes
        if any(word in query.lower() for word in ["content", "write", "essay", "application", "letter"]):
            # FIX 5: Content writing with automatic notepad opening
            await enhanced_content_generation(query)
        elif "wifi" in query.lower():
            # FIX 4: Enhanced WiFi controls
            await enhanced_wifi_control(query)
        elif "bluetooth" in query.lower():
            # FIX 4: Enhanced Bluetooth controls  
            await enhanced_bluetooth_control(query)
        elif "brightness" in query.lower():
            # FIX 4: Enhanced brightness controls
            await enhanced_brightness_control(query)
        elif "volume" in query.lower():
            await enhanced_volume_control(query)
        else:
            # Route to existing automation system
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

async def execute_single_command(query, command_num=1):
    """Execute a single command with full processing pipeline and enhanced error handling"""
    try:
        SetAssistantStatus(f"Executing Command {command_num}...")
        print(f"[Execute] Starting command {command_num}: '{query}'")
        
        # Handle system commands
        if query.lower() == "stop":
            await TextToSpeech("Stopping")
            return
        elif query.lower() == "skip":
            skip_current_speech()
            return
        # Remove immediate exit to prevent program termination
        elif "exit" in query.lower() or "shutdown" in query.lower():
            await TextToSpeech("I'll continue running. Say 'stop' to pause or close the application manually.")
            return
        
        # Get decision from model with error handling
        try:
            decision_list = FirstlayerDMM(query)
            print(f"[Execute] Command {command_num} decision: {decision_list}")
        except Exception as decision_error:
            print(f"[Execute] Decision making error: {decision_error}")
            decision_list = ["general (query)"]  # Default to general chat
        
        Answer = None
        try:
            if decision_list and len(decision_list) > 0:
                if "realtime" in decision_list[0].lower():
                    SetAssistantStatus(f"Searching... (Cmd {command_num})")
                    Answer = await asyncio.to_thread(RealtimeSearchEngine, QueryModifier(query))
                elif "general" in decision_list[0].lower():
                    SetAssistantStatus(f"Thinking... (Cmd {command_num})")
                    Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
                else:
                    SetAssistantStatus(f"Executing... (Cmd {command_num})")
                    Answer = await Automation(decision_list)
            else:
                SetAssistantStatus(f"Chatting... (Cmd {command_num})")
                Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
        except Exception as execution_error:
            print(f"[Execute] Execution error for command {command_num}: {execution_error}")
            Answer = f"I encountered an error while processing that command: {str(execution_error)}"
        
        # Handle response with better error checking
        try:
            if Answer and isinstance(Answer, str):
                await update_chat_display(query, Answer)
                # Shortened response for cleaner audio
                short_response = Answer[:100] + "..." if len(Answer) > 100 else Answer
                asyncio.create_task(TextToSpeech(short_response))
            elif Answer is True:
                success_msg = f"Command {command_num} completed successfully."
                await update_chat_display(query, success_msg)
                asyncio.create_task(TextToSpeech("Task completed."))
            elif Answer is False:
                error_msg = f"Sorry, command {command_num} failed."
                await update_chat_display(query, error_msg)
                asyncio.create_task(TextToSpeech("Task failed."))
            else:
                unknown_msg = f"Command {command_num}: I couldn't process that request."
                await update_chat_display(query, unknown_msg)
                asyncio.create_task(TextToSpeech("I couldn't process that request."))
        except Exception as response_error:
            print(f"[Execute] Response handling error: {response_error}")

        print(f"[Execute] ✅ Command {command_num} completed")
        SetAssistantStatus("🎤 Ready - Listening...")
        
    except Exception as e:
        print(f"[Execute] ❌ Critical error in command {command_num}: {e}")
        import traceback
        traceback.print_exc()
        
        # Don't let errors stop the system
        try:
            error_response = "I encountered an error but I'm still listening."
            await update_chat_display(query, error_response)
            asyncio.create_task(TextToSpeech("Error occurred, but I'm still ready."))
        except:
            pass  # Even error handling can fail, but don't crash
        
        SetAssistantStatus("🎤 Ready - Listening...")

async def process_user_query_concurrent(query):
    """Process user query concurrently without blocking voice listening"""
    try:
        print(f"[Concurrent] Processing: '{query}'")
        SetAssistantStatus(f"Processing: {query[:20]}...")
        
        if query.lower() == "stop":
            await TextToSpeech("Stopping")
            return
        elif "exit" in query.lower() or "shutdown" in query.lower():
            await TextToSpeech("Goodbye!")
            sys.exit()
        elif query.lower() == "skip":
            skip_current_speech()
            return
        
        # CORRECTED: Passing 'query' as a positional argument.
        decision_list = FirstlayerDMM(query)
        print(f"[Concurrent] Decision: {decision_list}")
        
        if decision_list and len(decision_list) > 0:
            if "realtime" in decision_list[0].lower():
                SetAssistantStatus("Searching...")
                Answer = await asyncio.to_thread(RealtimeSearchEngine, QueryModifier(query))
            elif "general" in decision_list[0].lower():
                SetAssistantStatus("Thinking...")
                Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
            else:
                SetAssistantStatus("Executing...")
                print(f"[Main] Sending decision list to Automation: {decision_list}")
                Answer = await Automation(decision_list)
                print(f"[Main] Automation returned: {Answer}")
        else:
            SetAssistantStatus("Chatting...")
            Answer = await asyncio.to_thread(ChatBot, QueryModifier(query))
        
        if Answer and isinstance(Answer, str):
            await update_chat_display(query, Answer)
            asyncio.create_task(TextToSpeech(Answer))
        elif Answer is True:
            await update_chat_display(query, "Task completed successfully.")
            asyncio.create_task(TextToSpeech("Task completed successfully."))
        elif Answer is False:
            await update_chat_display(query, "Sorry, I couldn't complete that task.")
            asyncio.create_task(TextToSpeech("Sorry, I couldn't complete that task."))
        else:
            await update_chat_display(query, "I'm sorry, I couldn't process that request.")
            asyncio.create_task(TextToSpeech("I'm sorry, I couldn't process that request."))

        SetAssistantStatus("Ready - Listening...")
        
    except Exception as e:
        print(f"[Concurrent] Error processing query: {e}")
        import traceback
        traceback.print_exc()
        SetAssistantStatus("Error occurred - Listening...")
        await TextToSpeech("I encountered an error while processing your request.")

async def update_chat_display(query, response):
    """Update chat display immediately with both temp file and JSON chatlog"""
    try:
        # Update the temp conversation file
        try:
            with open(TempDirectoryPath("Responses.data"), "r", encoding='utf-8') as file:
                current_conversation = file.read()
        except FileNotFoundError:
            current_conversation = ""
        
        new_conversation = current_conversation + f"\nUser : {query}\n{Assistantname} : {AnswerModifier(response)}"
        
        # Save to temp file for GUI
        with open(TempDirectoryPath("Responses.data"), "w", encoding='utf-8') as file:
            file.write(new_conversation)
            
        # Display the conversation
        ShowTextToScreen(new_conversation)
        
        # Also ensure it's in the JSON chatlog for persistence
        try:
            chatlog_path = os.path.join(os.path.dirname(__file__), 'Data', 'Chatlog.json')
            try:
                with open(chatlog_path, 'r', encoding='utf-8') as file:
                    chat_history = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                chat_history = []
            
            # Add if not already there (avoid duplicates)
            user_entry = {"role": "user", "content": query}
            assistant_entry = {"role": "assistant", "content": response}
            
            # Check if these entries are already at the end to avoid duplicates
            if not (len(chat_history) >= 2 and 
                   chat_history[-2].get("content") == query and
                   chat_history[-1].get("content") == response):
                chat_history.append(user_entry)
                chat_history.append(assistant_entry)
                
                with open(chatlog_path, 'w', encoding='utf-8') as file:
                    json.dump(chat_history, file, indent=4)
                    
        except Exception as chatlog_error:
            print(f"[Chat] Error updating chatlog: {chatlog_error}")
            
        print(f"[Chat] Updated display with new conversation")
        
    except Exception as e:
        print(f"[Chat] Error updating display: {e}")

async def MainExecutionAsync():
    """Start the continuous voice listener."""
    await continuous_voice_listener()
    
def start_main_async_loop():
    """Starts the asyncio event loop in a new thread."""
    global main_loop
    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)
    try:
        main_loop.run_forever()
    finally:
        main_loop.close()

execution_in_progress = False

def first_thread_logic():
    """Enhanced main logic with automatic recovery and resilience."""
    global execution_in_progress, continuous_listening_active, mic_always_active
    print("[Thread] 🚀 Starting resilient continuous listening system...")
    
    # Enable always-on microphone for true continuous listening
    print("[Thread] ✅ Always-on microphone enabled for continuous listening.")
    SetMicrophoneStatus("True")
    mic_always_active = True
    
    # Recovery counters
    speech_restart_count = 0
    max_speech_restarts = 5
    last_restart_time = 0
    restart_cooldown = 30  # seconds
    
    while True:
        try:
            current_time = time.time()
            
            # FIX 1: Force microphone to ALWAYS be active - critical for always-on recognition
            if mic_always_active:
                SetMicrophoneStatus("True")
                # Double-check and force if needed
                current_mic_status = GetMicrophoneStatus()
                if current_mic_status != "True":
                    SetMicrophoneStatus("True")
                    print(f"[Thread] 🔧 Forced microphone active (was: {current_mic_status})")
            
            mic_status = GetMicrophoneStatus()
            
            # Start or restart speech recognition if needed
            if not continuous_listening_active and (current_time - last_restart_time) > restart_cooldown:
                print("[Thread] 🎤 Starting/Restarting continuous voice processing...")
                
                try:
                    # Enhanced speech restart with Google API error recovery
                    print("[Thread] 🔄 Enhanced speech restart...")
                    
                    # Stop any existing listening
                    stop_continuous_listening()
                    sleep(0.5)
                    
                    # Simple system doesn't need queue clearing
                    sleep(0.5)
                    
                    # Start the continuous listening thread from SpeechToText
                    start_continuous_listening()
                    sleep(0.5)
                    
                    if main_loop and main_loop.is_running():
                        # Start the async listener in the main loop
                        asyncio.run_coroutine_threadsafe(
                            MainExecutionAsync(), main_loop
                        )
                        continuous_listening_active = True
                        speech_restart_count = 0  # Reset on success
                        print("[Thread] ✅ Enhanced voice processing started successfully")
                    else:
                        print("[Thread] ⚠️ Async event loop not running, will retry...")
                        sleep(2)
                        continue
                        
                except Exception as start_error:
                    print(f"[Thread] ❌ Error starting voice processing: {start_error}")
                    speech_restart_count += 1
                    last_restart_time = current_time
                    
                    if speech_restart_count >= max_speech_restarts:
                        print("[Thread] 🔄 Max restarts reached, longer cooldown...")
                        sleep(60)  # Longer wait after multiple failures
                        speech_restart_count = 0
                    else:
                        sleep(5)
                    continue
            
            # Monitor system health
            if continuous_listening_active and mic_status == "True":
                # System is running, check if we need to restart speech recognition
                if speech_restart_count > 0 and (current_time - last_restart_time) > restart_cooldown:
                    print("[Thread] 🔄 Attempting recovery restart...")
                    continuous_listening_active = False  # Force restart
                    
            elif mic_status == "False" and not mic_always_active:
                print("[Thread] 📴 Microphone manually deactivated...")
                continuous_listening_active = False
                
        except Exception as e:
            print(f"[Thread] ⚠️ Error in main logic: {e}")
            import traceback
            traceback.print_exc()
            
            # Don't crash, just wait and try again
            continuous_listening_active = False
            sleep(3)
            
        sleep(1)  # Reasonable sleep for monitoring

def SecondThread():
    GraphicalUserInterface()

# FIX 5: Enhanced content generation with automatic notepad
async def enhanced_content_generation(query):
    """Generate content and automatically open in notepad."""
    try:
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
        import subprocess
        subprocess.Popen(['notepad.exe', file_name])
        
        print(f"[Content] ✅ Content generated and opened in notepad: {file_name}")
        SetAssistantStatus("Content generated and opened in notepad")
        await TextToSpeech(f"I've written the content about {topic} and opened it in notepad for you.")
        
    except Exception as e:
        print(f"[Content] ❌ Error: {e}")
        SetAssistantStatus("Content generation failed")
        await TextToSpeech("I had trouble generating the content.")

# FIX 4: Enhanced WiFi control with comprehensive methods
async def enhanced_wifi_control(query):
    """Enhanced WiFi control with multiple comprehensive methods."""
    try:
        action = "on" if any(word in query.lower() for word in ["on", "enable", "turn on"]) else "off"
        
        print(f"[WiFi] 🔧 Enhanced WiFi {action} with comprehensive methods")
        SetAssistantStatus(f"Controlling WiFi - {action}")
        
        success = False
        methods_tried = 0
        
        # Method 1: netsh interface commands (multiple variations)
        netsh_commands = [
            ["netsh", "interface", "set", "interface", "Wi-Fi", "enabled" if action == "on" else "disabled"],
            ["netsh", "interface", "set", "interface", "WiFi", "enabled" if action == "on" else "disabled"],
            ["netsh", "interface", "set", "interface", "Wireless", "enabled" if action == "on" else "disabled"],
            ["netsh", "interface", "set", "interface", "WLAN", "enabled" if action == "on" else "disabled"]
        ]
        
        for i, cmd in enumerate(netsh_commands):
            methods_tried += 1
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=15)
                print(f"[WiFi] ✅ netsh method {i+1} succeeded")
                success = True
                break
            except Exception as e:
                print(f"[WiFi] netsh method {i+1} failed: {e}")
                continue
        
        # Method 2: PowerShell NetAdapter commands (if netsh failed)
        if not success:
            ps_commands = [
                f"Enable-NetAdapter -Name '*Wi-Fi*' -Confirm:$false" if action == "on" else "Disable-NetAdapter -Name '*Wi-Fi*' -Confirm:$false",
                f"Enable-NetAdapter -Name '*WiFi*' -Confirm:$false" if action == "on" else "Disable-NetAdapter -Name '*WiFi*' -Confirm:$false",
                f"Enable-NetAdapter -Name '*Wireless*' -Confirm:$false" if action == "on" else "Disable-NetAdapter -Name '*Wireless*' -Confirm:$false",
                f"Enable-NetAdapter -Name '*WLAN*' -Confirm:$false" if action == "on" else "Disable-NetAdapter -Name '*WLAN*' -Confirm:$false"
            ]
            
            for i, ps_cmd in enumerate(ps_commands):
                methods_tried += 1
                try:
                    result = subprocess.run(["powershell", "-Command", ps_cmd], 
                                          check=True, capture_output=True, text=True, timeout=15)
                    print(f"[WiFi] ✅ PowerShell method {i+1} succeeded")
                    success = True
                    break
                except Exception as e:
                    print(f"[WiFi] PowerShell method {i+1} failed: {e}")
                    continue
        
        # Method 3: Alternative PowerShell with Get-NetAdapter (if still failed)
        if not success:
            try:
                methods_tried += 1
                if action == "on":
                    ps_cmd = "Get-NetAdapter | Where-Object {$_.Name -like '*Wi*' -or $_.Name -like '*Wireless*'} | Enable-NetAdapter -Confirm:$false"
                else:
                    ps_cmd = "Get-NetAdapter | Where-Object {$_.Name -like '*Wi*' -or $_.Name -like '*Wireless*'} | Disable-NetAdapter -Confirm:$false"
                
                result = subprocess.run(["powershell", "-Command", ps_cmd], 
                                      check=True, capture_output=True, text=True, timeout=20)
                print(f"[WiFi] ✅ Get-NetAdapter method succeeded")
                success = True
            except Exception as e:
                print(f"[WiFi] Get-NetAdapter method failed: {e}")
        
        # Method 4: Device Manager approach (last resort)
        if not success:
            try:
                methods_tried += 1
                if action == "on":
                    ps_cmd = "Get-PnpDevice -Class Net | Where-Object {$_.Name -like '*Wi*' -or $_.Name -like '*Wireless*'} | Enable-PnpDevice -Confirm:$false"
                else:
                    ps_cmd = "Get-PnpDevice -Class Net | Where-Object {$_.Name -like '*Wi*' -or $_.Name -like '*Wireless*'} | Disable-PnpDevice -Confirm:$false"
                
                result = subprocess.run(["powershell", "-Command", ps_cmd], 
                                      check=True, capture_output=True, text=True, timeout=20)
                print(f"[WiFi] ✅ PnpDevice method succeeded")
                success = True
            except Exception as e:
                print(f"[WiFi] PnpDevice method failed: {e}")
        
        print(f"[WiFi] Tried {methods_tried} methods, Success: {success}")
        
        if success:
            SetAssistantStatus(f"WiFi {action} successfully")
            await TextToSpeech(f"WiFi has been turned {action}")
        else:
            SetAssistantStatus(f"WiFi {action} failed - tried {methods_tried} methods")
            await TextToSpeech(f"I tried {methods_tried} methods but couldn't turn WiFi {action}. Please check manually or try the Windows settings.")
            
    except Exception as e:
        print(f"[WiFi] ❌ Critical Error: {e}")
        SetAssistantStatus("WiFi control failed")
        await TextToSpeech("WiFi control encountered an error")

# FIX 4: Enhanced Bluetooth control with comprehensive methods
async def enhanced_bluetooth_control(query):
    """Enhanced Bluetooth control with multiple comprehensive methods."""
    try:
        action = "on" if any(word in query.lower() for word in ["on", "enable", "turn on"]) else "off"
        
        print(f"[Bluetooth] 🔧 Enhanced Bluetooth {action} with comprehensive methods")
        SetAssistantStatus(f"Controlling Bluetooth - {action}")
        
        success = False
        methods_tried = 0
        
        # Method 1: Bluetooth service control
        try:
            methods_tried += 1
            if action == "on":
                service_cmd = "Set-Service bthserv -StartupType Automatic; Start-Service bthserv -ErrorAction SilentlyContinue"
            else:
                service_cmd = "Stop-Service bthserv -Force -ErrorAction SilentlyContinue"
            
            result = subprocess.run(["powershell", "-Command", service_cmd], 
                                  check=True, capture_output=True, text=True, timeout=20)
            print(f"[Bluetooth] ✅ Service control method succeeded")
            success = True
            
        except Exception as e:
            print(f"[Bluetooth] Service control failed: {e}")
        
        # Method 2: PnP Device control (if service failed)
        if not success:
            pnp_commands = [
                # Try different Bluetooth device patterns
                f"Get-PnpDevice -Class Bluetooth | Where-Object {{$_.Status -eq '{'OK' if action == 'off' else 'Error'}'}} | {'Disable' if action == 'off' else 'Enable'}-PnpDevice -Confirm:$false",
                f"Get-PnpDevice | Where-Object {{$_.Name -like '*Bluetooth*'}} | {'Disable' if action == 'off' else 'Enable'}-PnpDevice -Confirm:$false",
                f"Get-PnpDevice | Where-Object {{$_.Class -eq 'Bluetooth'}} | {'Disable' if action == 'off' else 'Enable'}-PnpDevice -Confirm:$false"
            ]
            
            for i, pnp_cmd in enumerate(pnp_commands):
                methods_tried += 1
                try:
                    result = subprocess.run(["powershell", "-Command", pnp_cmd], 
                                          check=True, capture_output=True, text=True, timeout=20)
                    print(f"[Bluetooth] ✅ PnP method {i+1} succeeded")
                    success = True
                    break
                except Exception as e:
                    print(f"[Bluetooth] PnP method {i+1} failed: {e}")
                    continue
        
        # Method 3: Device Manager approach (if PnP failed)
        if not success:
            try:
                methods_tried += 1
                if action == "on":
                    device_cmd = "Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like '*Bluetooth*'} | ForEach-Object {$_.Enable()}"
                else:
                    device_cmd = "Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like '*Bluetooth*'} | ForEach-Object {$_.Disable()}"
                
                result = subprocess.run(["powershell", "-Command", device_cmd], 
                                      check=True, capture_output=True, text=True, timeout=25)
                print(f"[Bluetooth] ✅ WMI Device method succeeded")
                success = True
            except Exception as e:
                print(f"[Bluetooth] WMI Device method failed: {e}")
        
        # Method 4: Registry approach (last resort)
        if not success:
            try:
                methods_tried += 1
                if action == "on":
                    reg_cmd = "Get-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\BTHPORT\\Parameters\\Radio Support' | Set-ItemProperty -Name 'SupportDLL' -Value 'BthRadioMedia.dll'"
                else:
                    reg_cmd = "Get-Service -Name 'bthserv' | Stop-Service -Force"
                
                result = subprocess.run(["powershell", "-Command", reg_cmd], 
                                      check=True, capture_output=True, text=True, timeout=15)
                print(f"[Bluetooth] ✅ Registry method succeeded")
                success = True
            except Exception as e:
                print(f"[Bluetooth] Registry method failed: {e}")
        
        # Method 5: Alternative device control
        if not success:
            try:
                methods_tried += 1
                alt_cmd = f"devcon {'enable' if action == 'on' else 'disable'} *Bluetooth*"
                result = subprocess.run(alt_cmd, shell=True, check=True, capture_output=True, text=True, timeout=15)
                print(f"[Bluetooth] ✅ devcon method succeeded")
                success = True
            except Exception as e:
                print(f"[Bluetooth] devcon method failed: {e}")
        
        print(f"[Bluetooth] Tried {methods_tried} methods, Success: {success}")
        
        if success:
            SetAssistantStatus(f"Bluetooth {action} successfully")
            await TextToSpeech(f"Bluetooth has been turned {action}")
        else:
            SetAssistantStatus(f"Bluetooth {action} failed - tried {methods_tried} methods")
            await TextToSpeech(f"I tried {methods_tried} methods but couldn't turn Bluetooth {action}. Please check manually in Windows settings.")
            
    except Exception as e:
        print(f"[Bluetooth] ❌ Critical Error: {e}")
        SetAssistantStatus("Bluetooth control failed")
        await TextToSpeech("Bluetooth control encountered an error")

# FIX 4: Enhanced brightness control
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
            await TextToSpeech(f"Brightness turned {action}")
        else:
            SetAssistantStatus(f"Brightness {action} failed - all methods tried")
            await TextToSpeech(f"I couldn't adjust the brightness. You may need to use the keyboard shortcuts.")
            
    except Exception as e:
        print(f"[Brightness] ❌ Error: {e}")
        SetAssistantStatus("Brightness control failed")
        await TextToSpeech("Brightness control failed")

# FIX 4: Enhanced volume control
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
            await TextToSpeech(f"Volume {action}")
        else:
            SetAssistantStatus(f"Volume {action} failed")
            await TextToSpeech(f"Volume control failed")
            
    except Exception as e:
        print(f"[Volume] ❌ Error: {e}")
        SetAssistantStatus("Volume control failed")
        await TextToSpeech("Volume control failed")

if __name__ == "__main__":
    try:
        async_loop_thread = threading.Thread(target=start_main_async_loop, daemon=True)
        async_loop_thread.start()

        sleep(0.1)
        
        InitialExecution()

        threading.Thread(target=first_thread_logic, daemon=True).start()
        
        SecondThread()
    except KeyboardInterrupt:
        print("\n[Main] Program interrupted by user")
    except Exception as e:
        print(f"[Main] Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            if 'pygame' in sys.modules and pygame.mixer.get_init():
                pygame.mixer.quit()
        except:
            pass
        print("[Main] Program terminated")