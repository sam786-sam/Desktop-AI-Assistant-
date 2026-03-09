#!/usr/bin/env python3
"""
Alternative speech recognition using Windows Speech API directly
This can be used as a fallback if Chrome-based recognition fails
"""

import speech_recognition as sr
import pyaudio
import queue
import threading
import time

class WindowsSpeechRecognition:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.speech_queue = queue.Queue()
        self.listening = False
        self.listen_thread = None
        
        # Adjust for ambient noise
        print("[WindowsSpeech] Adjusting for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("[WindowsSpeech] Ready for speech recognition.")
    
    def start_listening(self):
        """Start continuous speech recognition"""
        if not self.listening:
            print("[WindowsSpeech] Starting continuous listening...")
            self.listening = True
            self.listen_thread = threading.Thread(target=self._listen_worker, daemon=True)
            self.listen_thread.start()
    
    def stop_listening(self):
        """Stop speech recognition"""
        print("[WindowsSpeech] Stopping listening...")
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
    
    def _listen_worker(self):
        """Worker thread for continuous listening"""
        print("[WindowsSpeech] Listening worker started.")
        
        while self.listening:
            try:
                # Listen for audio with timeout
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                
                # Recognize speech
                try:
                    text = self.recognizer.recognize_google(audio)
                    if text.strip():
                        print(f"[WindowsSpeech] Recognized: '{text}'")
                        self.speech_queue.put(text.strip())
                except sr.UnknownValueError:
                    # No speech detected, continue
                    pass
                except sr.RequestError as e:
                    print(f"[WindowsSpeech] Recognition error: {e}")
                    time.sleep(1)
                    
            except sr.WaitTimeoutError:
                # No audio detected, continue
                pass
            except Exception as e:
                print(f"[WindowsSpeech] Unexpected error: {e}")
                time.sleep(1)
        
        print("[WindowsSpeech] Listening worker stopped.")

def test_windows_speech():
    """Test Windows speech recognition"""
    print("🎤 Testing Windows Speech Recognition...")
    
    try:
        # Check if microphone is available
        import pyaudio
        p = pyaudio.PyAudio()
        
        # List audio devices
        print("\n📱 Available audio devices:")
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"  {i}: {device_info['name']}")
        
        p.terminate()
        
        # Test speech recognition
        speech_rec = WindowsSpeechRecognition()
        speech_rec.start_listening()
        
        print("\n🗣️ Say something! (Will listen for 10 seconds)")
        print("Try saying: 'hello', 'wifi on', 'bluetooth off', etc.")
        
        start_time = time.time()
        detected_speech = False
        
        while time.time() - start_time < 10:
            speech = speech_rec.get_speech(timeout=0.5)
            if speech:
                print(f"✅ Detected: '{speech}'")
                detected_speech = True
            time.sleep(0.1)
        
        speech_rec.stop_listening()
        
        if detected_speech:
            print("🎉 Windows Speech Recognition is WORKING!")
            return True
        else:
            print("⚠️ No speech detected. Check your microphone.")
            return False
            
    except Exception as e:
        print(f"❌ Windows Speech Recognition failed: {e}")
        print("💡 You might need to install: pip install speechrecognition pyaudio")
        return False

if __name__ == "__main__":
    test_windows_speech()