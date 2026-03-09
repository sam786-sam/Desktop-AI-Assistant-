#!/usr/bin/env python3
"""
Enhanced startup script for voice assistant with automatic fallback handling
"""

import sys
import os
import time
import subprocess

def start_voice_assistant():
    """Start the voice assistant with enhanced error handling"""
    print("🚀 STARTING ENHANCED VOICE ASSISTANT")
    print("=" * 60)
    print("Features:")
    print("  ✅ Chrome-based speech recognition (primary)")
    print("  ✅ Windows speech recognition (fallback)")
    print("  ✅ Automatic error detection and recovery")
    print("  ✅ Always-on voice recognition")
    print("  ✅ Multiple hardware control methods")
    print("=" * 60)
    
    try:
        # Change to the correct directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        
        print(f"📁 Working directory: {os.getcwd()}")
        
        # Check if Main.py exists
        if not os.path.exists("Main.py"):
            print("❌ Main.py not found in current directory!")
            return False
        
        print("🔧 Starting voice assistant...")
        print("   (If Chrome fails, will automatically switch to Windows Speech Recognition)")
        print("   (You should see fallback messages if Chrome has issues)")
        print("\n" + "=" * 60)
        
        # Start the main assistant
        # Use subprocess to better handle output
        process = subprocess.Popen(
            [sys.executable, "Main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line.rstrip())
            
            # Check for specific success/failure messages
            if "Successfully switched to fallback" in line:
                print("🎉 FALLBACK SPEECH RECOGNITION ACTIVATED!")
            elif "HTTPConnectionPool" in line and "refused" in line:
                print("⚠️ Chrome connection issue detected - fallback should activate soon...")
            elif "🎙️ Detected:" in line:
                print("✅ VOICE RECOGNITION IS WORKING!")
        
        process.wait()
        return True
        
    except KeyboardInterrupt:
        print("\n🛑 Voice assistant stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting voice assistant: {e}")
        return False

def main():
    """Main function"""
    print("🎤 ENHANCED VOICE ASSISTANT LAUNCHER")
    print("Auto-fallback to Windows Speech Recognition if Chrome fails")
    print()
    
    # Quick environment check
    try:
        import speech_recognition
        import pyaudio
        print("✅ Fallback speech recognition ready")
    except ImportError as e:
        print(f"⚠️ Fallback modules missing: {e}")
        print("Run: pip install speechrecognition pyaudio")
    
    print()
    
    # Start the assistant
    if start_voice_assistant():
        print("\n✅ Voice assistant session completed")
    else:
        print("\n❌ Voice assistant failed to start")
        print("\nTroubleshooting:")
        print("1. Check if Main.py exists")
        print("2. Install missing dependencies: pip install speechrecognition pyaudio")
        print("3. Check microphone permissions")

if __name__ == "__main__":
    main()