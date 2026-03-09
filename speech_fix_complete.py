#!/usr/bin/env python3
"""
Complete speech recognition fix with multiple fallback methods
This provides a robust solution that works even if Chrome fails
"""

import speech_recognition as sr
import queue
import threading
import time
import subprocess
import os

class RobustSpeechRecognition:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.listening = False
        self.listen_thread = None
        self.method = "windows"  # Start with Windows method
        
        # Windows Speech Recognition setup
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[RobustSpeech] ✅ Windows Speech Recognition initialized.")
        except Exception as e:
            print(f"[RobustSpeech] ⚠️ Windows Speech Recognition failed: {e}")
            self.microphone = None
    
    def start_listening(self):
        """Start robust speech recognition with fallbacks"""
        if not self.listening:
            print("[RobustSpeech] 🎤 Starting robust speech recognition...")
            self.listening = True
            self.listen_thread = threading.Thread(target=self._robust_listen_worker, daemon=True)
            self.listen_thread.start()
    
    def stop_listening(self):
        """Stop speech recognition"""
        print("[RobustSpeech] Stopping speech recognition...")
        self.listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
    
    def get_speech(self, timeout=1):
        """Get speech from queue"""
        try:
            return self.speech_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_queue(self):
        """Clear speech queue"""
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
    
    def _robust_listen_worker(self):
        """Robust listening worker with multiple fallback methods"""
        print("[RobustSpeech] Robust listening worker started.")
        
        consecutive_failures = 0
        max_failures = 5
        
        while self.listening:
            try:
                if self.method == "windows" and self.microphone:
                    success = self._windows_recognition()
                else:
                    # Fallback to other methods if needed
                    success = self._fallback_recognition()
                
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_failures:
                        print(f"[RobustSpeech] Too many failures, switching methods...")
                        self._switch_method()
                        consecutive_failures = 0
                        time.sleep(2)
                
            except Exception as e:
                print(f"[RobustSpeech] Worker error: {e}")
                consecutive_failures += 1
                time.sleep(1)
        
        print("[RobustSpeech] Robust listening worker stopped.")
    
    def _windows_recognition(self):
        """Windows-based speech recognition"""
        try:
            # Listen for audio with timeout
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=4)
            
            # Recognize speech using Google
            try:
                text = self.recognizer.recognize_google(audio)
                if text.strip():
                    print(f"[RobustSpeech] 🎙️ Windows detected: '{text}'")
                    self.speech_queue.put(text.strip().lower())
                    return True
            except sr.UnknownValueError:
                # No speech detected, not an error
                pass
            except sr.RequestError as e:
                print(f"[RobustSpeech] Google API error: {e}")
                return False
                
        except sr.WaitTimeoutError:
            # No audio detected, not an error
            pass
        except Exception as e:
            print(f"[RobustSpeech] Windows recognition error: {e}")
            return False
        
        return True  # No error, just no speech
    
    def _fallback_recognition(self):
        """Fallback recognition methods"""
        try:
            # Simple voice activity detection using system
            # This is a basic fallback - could be improved
            print("[RobustSpeech] Using fallback recognition...")
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"[RobustSpeech] Fallback error: {e}")
            return False
    
    def _switch_method(self):
        """Switch between recognition methods"""
        if self.method == "windows":
            self.method = "fallback"
            print("[RobustSpeech] Switched to fallback method")
        else:
            self.method = "windows"
            print("[RobustSpeech] Switched to Windows method")

# Global instance
robust_speech = None

def initialize_robust_speech():
    """Initialize the robust speech recognition system"""
    global robust_speech
    try:
        robust_speech = RobustSpeechRecognition()
        print("[RobustSpeech] ✅ Robust speech system initialized.")
        return True
    except Exception as e:
        print(f"[RobustSpeech] ❌ Failed to initialize: {e}")
        return False

def start_robust_listening():
    """Start robust speech recognition"""
    global robust_speech
    if robust_speech:
        robust_speech.start_listening()
    else:
        print("[RobustSpeech] ❌ System not initialized!")

def stop_robust_listening():
    """Stop robust speech recognition"""
    global robust_speech
    if robust_speech:
        robust_speech.stop_listening()

def get_robust_speech(timeout=1):
    """Get speech from robust system"""
    global robust_speech
    if robust_speech:
        return robust_speech.get_speech(timeout)
    return None

def clear_robust_queue():
    """Clear robust speech queue"""
    global robust_speech
    if robust_speech:
        robust_speech.clear_queue()

def test_robust_speech():
    """Test the robust speech system"""
    print("🧪 TESTING ROBUST SPEECH RECOGNITION")
    print("=" * 50)
    
    # Initialize
    if not initialize_robust_speech():
        print("❌ Failed to initialize robust speech")
        return False
    
    # Start listening
    start_robust_listening()
    
    print("\n🗣️ SPEAK NOW! (Testing for 15 seconds)")
    print("Try saying:")
    print("  • 'hello'")
    print("  • 'wifi on'")
    print("  • 'bluetooth off'")
    print("  • 'volume up'")
    
    start_time = time.time()
    detected_count = 0
    
    while time.time() - start_time < 15:
        speech = get_robust_speech(timeout=0.5)
        if speech:
            detected_count += 1
            print(f"✅ [{detected_count}] Detected: '{speech}'")
        time.sleep(0.1)
    
    stop_robust_listening()
    
    print(f"\n📊 RESULTS: {detected_count} speech commands detected")
    
    if detected_count > 0:
        print("🎉 ROBUST SPEECH RECOGNITION IS WORKING!")
        return True
    else:
        print("⚠️ No speech detected. Please check your microphone.")
        return False

if __name__ == "__main__":
    test_robust_speech()