import speech_recognition as sr
import os
import mtranslate as mt
import threading
import time
import queue
import numpy as np
from dotenv import dotenv_values
import asyncio
from rich import print

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-IN")
AssistantName = env_vars.get("Assistantname", "Jarvis")
WakeWords = env_vars.get("WakeWords", f"{AssistantName.lower()},hey {AssistantName.lower()},ok {AssistantName.lower()}").split(",")

# Define the path for temporary files.
current_dir = os.getcwd()
TempDirPath = rf"{current_dir}/Frontend/Files"

# Voice recognition settings
VOICE_CONFIDENCE_THRESHOLD = 0.7
AMBIENT_NOISE_DURATION = 0.5  # Reduced for faster start
LISTEN_TIMEOUT = 5  # Reduced timeout for better responsiveness
PHRASE_TIME_LIMIT = 10  # Increased phrase limit for longer sentences
ENERGY_THRESHOLD = 300
DYNAMIC_ENERGY_THRESHOLD = True  # Enable dynamic threshold adjustment

# Voice processing state
is_listening = False
voice_queue = queue.Queue()
wake_word_detected = False
continuous_mode = False

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    """Writes the assistant's current status to a file."""
    try:
        with open(rf"{TempDirPath}/Status.data", "w", encoding='utf-8') as file:
            file.write(Status)
        print(f"[VoiceToText] Status: {Status}")
    except FileNotFoundError:
        print(f"[VoiceToText] Status file not found at: {TempDirPath}/Status.data")

# Enhanced query modification with voice-specific improvements
def QueryModifier(Query):
    """Enhanced query modification for voice commands."""
    if not Query or not Query.strip():
        return None
        
    new_query = Query.lower().strip()
    
    # Remove wake words from the beginning
    for wake_word in WakeWords:
        if new_query.startswith(wake_word.lower()):
            new_query = new_query[len(wake_word):].strip()
            break
    
    # Remove common voice artifacts
    voice_artifacts = ["um", "uh", "ah", "er", "like"]
    for artifact in voice_artifacts:
        new_query = new_query.replace(f" {artifact} ", " ")
    
    # Handle common voice command patterns
    command_patterns = {
        "please": "",
        "can you": "",
        "could you": "",
        "would you": "",
        "i want you to": "",
        "i need you to": "",
    }
    
    for pattern, replacement in command_patterns.items():
        new_query = new_query.replace(pattern, replacement).strip()
    
    # Question detection for voice
    question_words = [
        "how", "what", "who", "where", "when", "why", "which", "whose", "whom", 
        "can you", "what's", "what is", "tell me", "show me", "explain", "describe"
    ]

    if any(word in new_query for word in question_words):
        if new_query[-1] not in ['.', '?', '!']:
            new_query += "?"
    else:
        if new_query[-1] not in ['.', '?', '!']:
            new_query += "."
    
    return new_query.capitalize()

# Enhanced translation with language detection
def UniversalTranslator(Text, source_lang="auto", target_lang="en"):
    """Enhanced translation with better error handling."""
    try:
        if not Text or not Text.strip():
            return Text
            
        # Skip translation if already in English
        if source_lang == "en" or (source_lang == "auto" and detect_language(Text) == "en"):
            return Text
            
        english_translation = mt.translate(Text, target_lang, source_lang)
        return english_translation.capitalize()
    except Exception as e:
        print(f"[VoiceToText] Translation error: {e}")
        return Text

def detect_language(text):
    """Simple language detection based on common words."""
    hindi_words = ["है", "हूं", "करो", "क्या", "कैसे", "कहां", "कब", "क्यों"]
    telugu_words = ["అవును", "లేదు", "ఎలా", "ఎక్కడ", "ఎప్పుడు", "ఎందుకు"]
    
    if any(word in text for word in hindi_words):
        return "hi"
    elif any(word in text for word in telugu_words):
        return "te"
    else:
        return "en"

# Wake word detection
def detect_wake_word(text):
    """Detect if wake word is present in the text."""
    if not text:
        return False
        
    text_lower = text.lower()
    for wake_word in WakeWords:
        if wake_word.lower() in text_lower:
            return True
    return False

# Enhanced speech recognition with multiple attempts and noise handling
def EnhancedSpeechRecognition(timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT):
    """Enhanced speech recognition with improved voice processing."""
    r = sr.Recognizer()
    
    # Configure recognizer for better voice detection
    r.energy_threshold = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
    r.dynamic_energy_adjustment_damping = 0.1
    r.dynamic_energy_ratio = 2.0
    r.pause_threshold = 0.6  # Shorter pause threshold for faster response
    r.operation_timeout = timeout
    r.non_speaking_duration = 0.3  # Reduce non-speaking duration
    
    with sr.Microphone() as source:
        print("[VoiceToText] 🎤 Listening for voice...")
        SetAssistantStatus("🎤 Listening...")
        
        try:
            # Adjust for ambient noise with shorter duration for responsiveness
            r.adjust_for_ambient_noise(source, duration=AMBIENT_NOISE_DURATION)
            
            # Listen with timeout and phrase limit
            print("[VoiceToText] 👂 Active listening...")
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            print("[VoiceToText] 🔍 Recognizing speech...")
            SetAssistantStatus("🔍 Recognizing...")

            # Multiple language recognition attempts
            recognition_attempts = [
                {"language": "en-IN", "name": "English"},
                {"language": "hi-IN", "name": "Hindi"},
                {"language": "te-IN", "name": "Telugu"},
                {"language": "en-US", "name": "English (US)"},
            ]
            
            for attempt in recognition_attempts:
                try:
                    text = r.recognize_google(audio, language=attempt["language"])
                    if text and text.strip():
                        print(f"[VoiceToText] ✅ Detected ({attempt['name']}): '{text}'")
                        
                        # Translate if not English
                        if attempt["language"] not in ["en-IN", "en-US"]:
                            SetAssistantStatus("🌐 Translating...")
                            english_text = UniversalTranslator(text)
                            return QueryModifier(english_text)
                        else:
                            return QueryModifier(text)
                            
                except sr.UnknownValueError:
                    continue  # Try next language
                except sr.RequestError as e:
                    print(f"[VoiceToText] ❌ API Error for {attempt['name']}: {e}")
                    continue
            
            # If all attempts failed
            print("[VoiceToText] ❌ Could not understand audio in any supported language.")
            SetAssistantStatus("❓ Couldn't understand - please try again...")
            return None

        except sr.WaitTimeoutError:
            print("[VoiceToText] ⏰ Listening timeout")
            SetAssistantStatus("⏰ Listening timeout")
            return None
        except sr.RequestError as e:
            print(f"[VoiceToText] 🌐 Network error: {e}")
            SetAssistantStatus("🌐 Network error - check connection")
            return None
        except Exception as e:
            print(f"[VoiceToText] ❌ Unexpected error: {e}")
            SetAssistantStatus("❌ Voice recognition error")
            return None

# Continuous voice recognition
def continuous_voice_recognition():
    """Continuous voice recognition in background thread with auto-restart."""
    global is_listening, continuous_mode
    
    print("[VoiceToText] 🔄 Starting continuous voice recognition...")
    error_count = 0
    max_errors = 5
    last_success_time = time.time()
    
    while continuous_mode:
        try:
            if not is_listening:
                time.sleep(0.1)
                continue
            
            # Auto-restart if no success for 15 seconds
            if (time.time() - last_success_time) > 15:
                print("[VoiceToText] 🔄 No recognition for 15s, forcing restart...")
                SetAssistantStatus("🔄 Reinitializing microphone...")
                time.sleep(0.5)  # Brief pause before restart
                last_success_time = time.time()
            
            # Use shorter timeout for continuous mode but longer phrase limit
            text = EnhancedSpeechRecognition(timeout=4, phrase_time_limit=8)
            
            if text:
                error_count = 0  # Reset error count on success
                last_success_time = time.time()
                
                # Check for wake word if needed
                if detect_wake_word(text):
                    # Remove wake word from text
                    for wake_word in WakeWords:
                        text = text.replace(wake_word, "").strip()
                    
                    if text:  # Only add non-empty text
                        voice_queue.put(text)
                        print(f"[VoiceToText] 📝 Queued: '{text}'")
                        SetAssistantStatus("✅ Command received")
            else:
                error_count += 1
                if error_count >= max_errors:
                    print("[VoiceToText] ⚠️ Multiple failures, brief pause...")
                    time.sleep(1)  # Brief pause after multiple failures
                    error_count = 0
                    
        except Exception as e:
            print(f"[VoiceToText] Continuous recognition error: {e}")
            error_count += 1
            if error_count >= max_errors:
                print("[VoiceToText] 🔄 Recovery mode - restarting...")
                time.sleep(2)  # Longer pause on errors
                error_count = 0

# Voice command processing
def start_continuous_listening():
    """Start continuous voice listening."""
    global continuous_mode, is_listening
    
    if not continuous_mode:
        continuous_mode = True
        is_listening = True
        
        # Start background thread
        voice_thread = threading.Thread(target=continuous_voice_recognition, daemon=True)
        voice_thread.start()
        
        print("[VoiceToText] ✅ Continuous listening started")
        SetAssistantStatus("🎤 Continuous listening active")
    else:
        print("[VoiceToText] ⚠️ Continuous listening already active")

def stop_continuous_listening():
    """Stop continuous voice listening."""
    global continuous_mode, is_listening
    
    continuous_mode = False
    is_listening = False
    
    print("[VoiceToText] 🛑 Continuous listening stopped")
    SetAssistantStatus("🔇 Voice recognition stopped")

def pause_listening():
    """Pause voice listening without stopping thread."""
    global is_listening
    is_listening = False
    print("[VoiceToText] ⏸️ Voice listening paused")

def resume_listening():
    """Resume voice listening."""
    global is_listening
    is_listening = True
    print("[VoiceToText] ▶️ Voice listening resumed")

def get_voice_command(timeout=1):
    """Get voice command from queue."""
    try:
        return voice_queue.get(timeout=timeout)
    except queue.Empty:
        return None

def clear_voice_queue():
    """Clear all pending voice commands."""
    while not voice_queue.empty():
        try:
            voice_queue.get_nowait()
        except queue.Empty:
            break
    print("[VoiceToText] 🗑️ Voice queue cleared")

# Voice activity detection
def detect_voice_activity(duration=2):
    """Simple voice activity detection."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=duration, phrase_time_limit=duration)
            
            # Convert audio to numpy array for analysis
            audio_data = np.frombuffer(audio.frame_data, dtype=np.int16)
            
            # Calculate RMS (Root Mean Square) for volume level
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Voice detected if RMS above threshold
            return rms > ENERGY_THRESHOLD
            
        except Exception as e:
            print(f"[VoiceToText] Voice activity detection error: {e}")
            return False

# Smart voice recognition that waits for voice activity
def smart_voice_recognition(max_wait=30):
    """Wait for voice activity before starting recognition."""
    print("[VoiceToText] 👂 Waiting for voice activity...")
    SetAssistantStatus("👂 Waiting for voice...")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if detect_voice_activity(duration=1):
            print("[VoiceToText] 🎙️ Voice detected, starting recognition...")
            return EnhancedSpeechRecognition()
        
        time.sleep(0.5)
    
    print("[VoiceToText] ⏰ No voice activity detected within timeout")
    return None

# Main voice recognition function (backward compatible)
def SpeechRecognition():
    """Main speech recognition function - enhanced version."""
    return EnhancedSpeechRecognition()

# Voice command validator
def is_valid_voice_command(text):
    """Check if the recognized text is a valid command."""
    if not text or len(text.strip()) < 2:
        return False
    
    # Filter out common false positives
    false_positives = ["the", "a", "an", "and", "or", "but", "hmm", "um", "ah"]
    
    words = text.lower().split()
    if len(words) == 1 and words[0] in false_positives:
        return False
    
    return True

# Advanced voice processing
async def process_voice_command_async():
    """Async voice command processing."""
    while continuous_mode:
        command = get_voice_command(timeout=0.1)
        if command and is_valid_voice_command(command):
            print(f"[VoiceToText] 🎯 Processing command: '{command}'")
            yield command
        await asyncio.sleep(0.1)

# Test and diagnostic functions
def test_microphone():
    """Test microphone functionality."""
    print("[VoiceToText] 🎤 Testing microphone...")
    
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Say something...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=5, phrase_time_limit=3)
            
            text = r.recognize_google(audio)
            print(f"✅ Microphone test successful: '{text}'")
            return True
            
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False

def get_available_microphones():
    """List available microphones."""
    print("[VoiceToText] 🎤 Available microphones:")
    for i, microphone_name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {i}: {microphone_name}")

# Usage examples and testing
if __name__ == "__main__":
    print("[VoiceToText] 🚀 Enhanced Voice Recognition System")
    print("=" * 60)
    
    # Test microphone
    if test_microphone():
        print("\n🎤 Microphone working correctly")
    
    # Get available microphones
    get_available_microphones()
    
    # Test different modes
    while True:
        print("\nChoose test mode:")
        print("1. Single voice recognition")
        print("2. Continuous listening")
        print("3. Smart voice detection")
        print("4. Exit")
        
        choice = input("Enter choice (1-4): ")
        
        if choice == "1":
            text = SpeechRecognition()
            if text:
                print(f"Result: {text}")
        
        elif choice == "2":
            start_continuous_listening()
            print("Continuous listening started. Press Enter to stop...")
            input()
            stop_continuous_listening()
        
        elif choice == "3":
            text = smart_voice_recognition()
            if text:
                print(f"Smart recognition result: {text}")
        
        elif choice == "4":
            stop_continuous_listening()
            break
        
        else:
            print("Invalid choice")

    print("[VoiceToText] 👋 Enhanced voice recognition system stopped")