import pygame
import random
import os
import threading
import asyncio
import edge_tts
from dotenv import dotenv_values
import time

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-US-AriaNeural")

# Global flag for TTS interruption, protected by a lock
tts_interrupt_flag = threading.Event()
tts_skip_flag = threading.Event()  # Global skip flag
interrupt_check_lock = threading.Lock()  # Lock for thread-safe interrupt checking

# Ensure Data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
os.makedirs(DATA_DIR, exist_ok=True)

# Create a lock for file access to prevent race conditions
file_lock = threading.Lock()

async def _generate_audio_file_async(text: str):
    """Generates the speech audio file asynchronously."""
    
    # Use a unique temporary file name to prevent conflicts
    unique_filename = f"speech_{int(time.time() * 1000)}_{random.randint(0, 1000)}.mp3"
    file_path = os.path.join(DATA_DIR, unique_filename)

    with file_lock:
        try:
            communicate = edge_tts.Communicate(text, AssistantVoice, pitch="+5Hz", rate="-10%")
            await communicate.save(file_path)
            return file_path
        except Exception as e:
            print(f"[TTS] Error generating audio file: {e}")
            return None

def _play_audio_sync(file_path: str):
    """Plays an audio file synchronously and handles deletion with interruption support."""
    try:
        # Use pygame.mixer.Sound for better file handling on short files
        sound = pygame.mixer.Sound(file_path)
        channel = sound.play()
        
        # Wait until the sound has finished playing or interrupt is detected
        start_time = time.time()
        max_play_time = 60  # Maximum play time in seconds
        
        while channel.get_busy() and not tts_skip_flag.is_set():
            # Check for interrupt flag every 50ms
            time.sleep(0.05)
            
            # Check if we should interrupt (timeout or interrupt flag)
            with interrupt_check_lock:
                if tts_interrupt_flag.is_set():
                    print("[TTS Player] ⚡ Interrupt detected - stopping playback")
                    tts_interrupt_flag.clear()
                    break
            
            # Timeout protection
            if time.time() - start_time > max_play_time:
                print("[TTS Player] ⏰ Max play time reached - stopping")
                break
            
    except pygame.error as e:
        print(f"[TTS Player] Pygame error playing audio: {e}")
    except Exception as e:
        print(f"[TTS Player] Error playing audio: {e}")
    finally:
        # Stop any ongoing playback and then quit the mixer
        if pygame.mixer.get_busy():
            pygame.mixer.stop()
        
        # Clear flags
        tts_skip_flag.clear()
        tts_interrupt_flag.clear()
        
        # Attempt to delete the file with retries
        for i in range(5):
            try:
                os.remove(file_path)
                print(f"[TTS Player] Deleted audio file: {file_path}")
                break
            except OSError as e:
                print(f"[TTS Player] Could not delete file {file_path}: {e}. Retrying...")
                time.sleep(0.1)

async def TextToSpeech(text: str):
    """Main TTS function to generate and play speech."""
    # Ensure mixer is initialized
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    
    # Check for skip flag and clear it if set
    if tts_skip_flag.is_set():
        tts_skip_flag.clear()
        return

    try:
        file_to_play = await _generate_audio_file_async(text)
        if file_to_play:
            await asyncio.to_thread(_play_audio_sync, file_to_play)
    except Exception as e:
        print(f"[TTS] Error during TTS process: {e}")

def skip_current_speech():
    """Sets a flag to interrupt the current TTS playback."""
    tts_skip_flag.set()
    tts_interrupt_flag.set()
    if pygame.mixer.get_init() and pygame.mixer.get_busy():
        pygame.mixer.stop()
    print("[TTS] ⚡ TTS playback skipped/interrupted.")

def is_speaking():
    """Check if TTS is currently speaking."""
    return pygame.mixer.get_init() and pygame.mixer.get_busy()

def interrupt_if_speaking():
    """Interrupt current speech if playing - used for voice interruption."""
    if is_speaking():
        print("[TTS] 🎤 Voice interrupt - stopping current speech")
        skip_current_speech()
        return True
    return False

if __name__ == "__main__":
    async def test_tts_function():
        pygame.mixer.init()
        print("TTS Test: Speaking a short phrase.")
        await TextToSpeech("Hello, this is a short test message.")
        await asyncio.sleep(2)
        
        print("TTS Test: Speaking a second phrase.")
        await TextToSpeech("This is a second test to check for file conflicts.")
        await asyncio.sleep(2)
        
        print("TTS Test: Done.")

    asyncio.run(test_tts_function())
    pygame.mixer.quit()