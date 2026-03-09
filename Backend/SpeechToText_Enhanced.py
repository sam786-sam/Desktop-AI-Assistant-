"""
Enhanced Speech-to-Text System with Multiple Recognition Methods
Combines web-based recognition, traditional speech_recognition, and enhanced voice processing
"""

import queue
import threading
import time
import os
import mtranslate as mt
from dotenv import dotenv_values
from rich import print
import asyncio

# Import enhanced voice recognition
from .VoiceToText_Enhanced import (
    EnhancedSpeechRecognition, 
    start_continuous_listening, 
    stop_continuous_listening,
    get_voice_command,
    clear_voice_queue,
    QueryModifier,
    SetAssistantStatus,
    detect_wake_word,
    smart_voice_recognition
)

# Original selenium-based recognition
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-IN")
AssistantName = env_vars.get("Assistantname", "Jarvis")

# Speech recognition modes
RECOGNITION_MODE = "enhanced"  # "web", "enhanced", "hybrid"

# Global variables for speech processing
speech_queue = queue.Queue()
continuous_listening_active = False
web_driver = None
recognition_thread = None

# Enhanced HTML with better voice recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Enhanced Speech Recognition</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #1a1a1a; color: white; }
        button { padding: 10px 20px; margin: 10px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; }
        #start { background: #4CAF50; color: white; }
        #stop { background: #f44336; color: white; }
        #clear { background: #ff9800; color: white; }
        #output { background: #333; padding: 15px; border-radius: 5px; margin-top: 20px; min-height: 100px; }
        .status { color: #4CAF50; font-weight: bold; }
        .error { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🎤 Enhanced Speech Recognition</h1>
    <div>
        <button id="start" onclick="startRecognition()">🎤 Start Recognition</button>
        <button id="stop" onclick="stopRecognition()">🛑 Stop Recognition</button>
        <button id="clear" onclick="clearOutput()">🗑️ Clear Output</button>
    </div>
    <div id="status" class="status">Ready</div>
    <div id="output"></div>
    <script>
        const output = document.getElementById('output');
        const statusDiv = document.getElementById('status');
        let recognition;
        let isRecognizing = false;
        let finalTranscript = '';
        
        // Wake word detection
        const wakeWords = ['{assistant_name}', 'hey {assistant_name}', 'ok {assistant_name}'];
        
        function updateStatus(message, isError = false) {{
            statusDiv.textContent = message;
            statusDiv.className = isError ? 'error' : 'status';
        }}

        function startRecognition() {{
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
                updateStatus('❌ Speech recognition not supported in this browser', true);
                return;
            }}
            
            try {{
                recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = '{language}';
                recognition.continuous = true;
                recognition.interimResults = true;
                recognition.maxAlternatives = 3;
                
                recognition.onstart = function() {{
                    isRecognizing = true;
                    updateStatus('🎤 Listening...');
                }};
                
                recognition.onresult = function(event) {{
                    let interimTranscript = '';
                    let finalText = '';
                    
                    for (let i = event.resultIndex; i < event.results.length; ++i) {{
                        const transcript = event.results[i][0].transcript;
                        
                        if (event.results[i].isFinal) {{
                            finalText += transcript;
                            finalTranscript += transcript + ' ';
                        }} else {{
                            interimTranscript += transcript;
                        }}
                    }}
                    
                    // Display both final and interim results
                    output.innerHTML = '<strong>Final:</strong> ' + finalTranscript + 
                                     '<br><em>Current:</em> ' + interimTranscript;
                    
                    if (finalText.trim()) {{
                        updateStatus('✅ Speech recognized: ' + finalText.trim());
                        
                        // Check for wake word
                        const lowerText = finalText.toLowerCase();
                        const hasWakeWord = wakeWords.some(word => lowerText.includes(word.toLowerCase()));
                        
                        if (hasWakeWord) {{
                            updateStatus('🎯 Wake word detected!');
                        }}
                    }}
                }};
                
                recognition.onerror = function(event) {{
                    updateStatus('❌ Recognition error: ' + event.error, true);
                    isRecognizing = false;
                }};
                
                recognition.onend = function() {{
                    updateStatus('🔄 Recognition ended, restarting...');
                    isRecognizing = false;
                    
                    // Auto-restart for continuous listening
                    setTimeout(() => {{
                        if (document.getElementById('start').textContent.includes('Stop')) {{
                            startRecognition();
                        }}
                    }}, 1000);
                }};
                
                recognition.start();
                document.getElementById('start').textContent = '🛑 Stop Recognition';
                
            }} catch (error) {{
                updateStatus('❌ Failed to start recognition: ' + error.message, true);
            }}
        }}
        
        function stopRecognition() {{
            if (recognition && isRecognizing) {{
                recognition.stop();
                updateStatus('🛑 Recognition stopped');
                document.getElementById('start').textContent = '🎤 Start Recognition';
            }}
        }}
        
        function clearOutput() {{
            output.textContent = '';
            finalTranscript = '';
            updateStatus('🗑️ Output cleared');
        }}
        
        // Auto-start recognition
        window.onload = function() {{
            setTimeout(startRecognition, 1000);
        }};
    </script>
</body>
</html>'''.format(language=InputLanguage, assistant_name=AssistantName.lower())

class EnhancedSpeechToText:
    """Enhanced Speech-to-Text system with multiple recognition modes"""
    
    def __init__(self, mode="enhanced"):
        self.mode = mode
        self.driver = None
        self.is_active = False
        
    def initialize_web_recognition(self):
        """Initialize web-based speech recognition"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--use-fake-ui-for-media-stream")
            chrome_options.add_argument("--use-fake-device-for-media-stream")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Load the HTML page
            self.driver.get("data:text/html;charset=utf-8," + HtmlCode)
            time.sleep(2)
            
            print("[SpeechToText] ✅ Web-based recognition initialized")
            return True
            
        except Exception as e:
            print(f"[SpeechToText] ❌ Failed to initialize web recognition: {e}")
            return False
    
    def get_web_recognition_result(self):
        """Get recognition result from web interface"""
        try:
            if not self.driver:
                return None
                
            output_element = self.driver.find_element(By.ID, "output")
            text = output_element.text
            
            if text and "Final:" in text:
                # Extract final text
                final_text = text.split("Final:")[1].split("Current:")[0].strip()
                if final_text:
                    # Clear the output
                    self.driver.execute_script("clearOutput();")
                    return QueryModifier(final_text)
            
            return None
            
        except Exception as e:
            print(f"[SpeechToText] Error getting web result: {e}")
            return None
    
    def start_recognition(self):
        """Start recognition based on selected mode"""
        global continuous_listening_active
        
        if self.mode == "web":
            return self.initialize_web_recognition()
        elif self.mode == "enhanced":
            start_continuous_listening()
            continuous_listening_active = True
            return True
        elif self.mode == "hybrid":
            # Use both methods
            web_success = self.initialize_web_recognition()
            start_continuous_listening()
            continuous_listening_active = True
            return web_success or continuous_listening_active
        
        return False
    
    def stop_recognition(self):
        """Stop all recognition methods"""
        global continuous_listening_active
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        
        if continuous_listening_active:
            stop_continuous_listening()
            continuous_listening_active = False
        
        print("[SpeechToText] 🛑 All recognition stopped")
    
    def get_speech_result(self, timeout=1):
        """Get speech result from active recognition method"""
        if self.mode == "web" and self.driver:
            return self.get_web_recognition_result()
        elif self.mode == "enhanced":
            return get_voice_command(timeout)
        elif self.mode == "hybrid":
            # Try enhanced first, then web
            result = get_voice_command(0.1)
            if not result and self.driver:
                result = self.get_web_recognition_result()
            return result
        
        return None

# Global enhanced speech-to-text instance
enhanced_stt = EnhancedSpeechToText(RECOGNITION_MODE)

# Backward compatibility functions
def start_continuous_listening_enhanced():
    """Start enhanced continuous listening"""
    global continuous_listening_active
    
    if not continuous_listening_active:
        success = enhanced_stt.start_recognition()
        if success:
            print("[SpeechToText] ✅ Enhanced continuous listening started")
            SetAssistantStatus("🎤 Enhanced listening active")
        return success
    else:
        print("[SpeechToText] ⚠️ Enhanced listening already active")
        return True

def stop_continuous_listening_enhanced():
    """Stop enhanced continuous listening"""
    enhanced_stt.stop_recognition()
    print("[SpeechToText] 🛑 Enhanced continuous listening stopped")

def get_speech_from_queue(timeout=1):
    """Get speech from queue with enhanced processing"""
    return enhanced_stt.get_speech_result(timeout)

def clear_speech_queue():
    """Clear the speech queue"""
    clear_voice_queue()
    
    # Also clear web-based queue if applicable
    try:
        speech_queue.queue.clear()
    except:
        pass
    
    print("[SpeechToText] 🗑️ All speech queues cleared")

# Smart recognition functions
async def smart_speech_recognition(max_wait=30):
    """Smart speech recognition that waits for voice activity"""
    print("[SpeechToText] 🧠 Smart recognition activated")
    
    if RECOGNITION_MODE == "enhanced":
        return smart_voice_recognition(max_wait)
    else:
        # Fallback to standard recognition
        return EnhancedSpeechRecognition()

def switch_recognition_mode(mode):
    """Switch between recognition modes"""
    global RECOGNITION_MODE, enhanced_stt
    
    # Stop current recognition
    enhanced_stt.stop_recognition()
    
    # Switch mode
    RECOGNITION_MODE = mode
    enhanced_stt = EnhancedSpeechToText(mode)
    
    print(f"[SpeechToText] 🔄 Switched to {mode} recognition mode")

# Voice command processing
async def process_voice_commands():
    """Process voice commands asynchronously"""
    while continuous_listening_active:
        try:
            command = get_speech_from_queue(timeout=0.1)
            if command:
                print(f"[SpeechToText] 🎯 Voice command: '{command}'")
                
                # Check for system commands
                if "switch to web recognition" in command.lower():
                    switch_recognition_mode("web")
                elif "switch to enhanced recognition" in command.lower():
                    switch_recognition_mode("enhanced")
                elif "switch to hybrid recognition" in command.lower():
                    switch_recognition_mode("hybrid")
                elif "clear voice queue" in command.lower():
                    clear_speech_queue()
                else:
                    # Add to processing queue
                    speech_queue.put(command)
                    
        except Exception as e:
            print(f"[SpeechToText] Voice command processing error: {e}")
        
        await asyncio.sleep(0.1)

# Test and diagnostic functions
def test_all_recognition_modes():
    """Test all available recognition modes"""
    print("[SpeechToText] 🧪 Testing all recognition modes...")
    
    modes = ["enhanced", "web", "hybrid"]
    results = {}
    
    for mode in modes:
        print(f"\n🔍 Testing {mode} mode...")
        test_stt = EnhancedSpeechToText(mode)
        
        try:
            success = test_stt.start_recognition()
            time.sleep(2)  # Wait for initialization
            
            if success:
                print(f"✅ {mode} mode initialized successfully")
                
                # Test getting result
                result = test_stt.get_speech_result(timeout=0.1)
                results[mode] = {"initialized": True, "test_result": result is not None}
            else:
                print(f"❌ {mode} mode failed to initialize")
                results[mode] = {"initialized": False, "test_result": False}
            
            test_stt.stop_recognition()
            
        except Exception as e:
            print(f"❌ {mode} mode error: {e}")
            results[mode] = {"initialized": False, "test_result": False}
    
    # Summary
    print("\n📊 Recognition Mode Test Results:")
    print("-" * 40)
    for mode, result in results.items():
        status = "✅ Working" if result["initialized"] else "❌ Failed"
        print(f"{mode:>10}: {status}")
    
    return results

# Main functions (backward compatibility)
def SpeechRecognition():
    """Main speech recognition function - backward compatible"""
    return EnhancedSpeechRecognition()

# Export enhanced functions with original names
start_continuous_listening = start_continuous_listening_enhanced
stop_continuous_listening = stop_continuous_listening_enhanced

# Usage example
if __name__ == "__main__":
    print("[SpeechToText] 🚀 Enhanced Speech-to-Text System")
    print("=" * 60)
    
    # Test all modes
    test_results = test_all_recognition_modes()
    
    # Interactive mode
    while True:
        print("\nChoose mode:")
        print("1. Enhanced recognition")
        print("2. Web-based recognition") 
        print("3. Hybrid recognition")
        print("4. Smart recognition")
        print("5. Exit")
        
        choice = input("Enter choice (1-5): ")
        
        if choice == "1":
            switch_recognition_mode("enhanced")
            start_continuous_listening_enhanced()
            print("Enhanced recognition active. Press Enter to stop...")
            input()
            stop_continuous_listening_enhanced()
        
        elif choice == "2":
            switch_recognition_mode("web")
            start_continuous_listening_enhanced()
            print("Web recognition active. Press Enter to stop...")
            input()
            stop_continuous_listening_enhanced()
        
        elif choice == "3":
            switch_recognition_mode("hybrid")
            start_continuous_listening_enhanced()
            print("Hybrid recognition active. Press Enter to stop...")
            input()
            stop_continuous_listening_enhanced()
        
        elif choice == "4":
            result = asyncio.run(smart_speech_recognition())
            if result:
                print(f"Smart recognition result: {result}")
        
        elif choice == "5":
            enhanced_stt.stop_recognition()
            break
        
        else:
            print("Invalid choice")
    
    print("[SpeechToText] 👋 Enhanced speech-to-text system stopped")