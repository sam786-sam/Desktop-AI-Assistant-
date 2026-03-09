#!/usr/bin/env python3
"""
Enhanced Jarvis Assistant - Full Feature Testing
This script demonstrates all working features of the Jarvis assistant.
"""

import asyncio
import sys
import os
import json

# Add paths
sys.path.append(os.path.dirname(__file__))

from Backend.Automation import Automation
from Backend.Model import FirstlayerDMM
from Backend.Chatbot import ChatBot
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from speechtotext import QueryModifier

class JarvisDemo:
    def __init__(self):
        self.Assistantname = "Jarvis"
        
    async def test_all_features(self):
        """Comprehensive test of all Jarvis features"""
        
        print("🚀 Starting Jarvis Enhanced Feature Demo")
        print("=" * 50)
        
        # Test automation features
        automation_tests = [
            ("Opening Apps", "open notepad"),
            ("Google Search", "google search latest AI news"),
            ("YouTube Search", "youtube search funny programming memes"),
            ("YouTube Play", "play relaxing music"),
            ("Content Generation", "content write essay about machine learning"),
            ("Image Generation", "generate image futuristic robot"),
            ("Volume Control", "volume up"),
            ("Brightness Control", "brightness up"),
            ("Media Control", "media pause"),
            ("WiFi Control", "wifi status"),  # Safe command that won't disconnect you
        ]
        
        print("\n🔧 Testing Automation Features:")
        print("-" * 30)
        
        for test_name, command in automation_tests:
            try:
                print(f"\n🎯 {test_name}: '{command}'")
                
                # Get decision
                decision_list = FirstlayerDMM(command)
                print(f"📋 Decision: {decision_list}")
                
                if decision_list and any("realtime" in d.lower() for d in decision_list):
                    # Realtime search
                    result = await asyncio.to_thread(RealtimeSearchEngine, QueryModifier(command))
                    print(f"🌐 Realtime Result: {result[:100]}..." if len(str(result)) > 100 else f"🌐 Realtime Result: {result}")
                elif decision_list and any("general" in d.lower() for d in decision_list):
                    # General chat
                    result = await asyncio.to_thread(ChatBot, QueryModifier(command))
                    print(f"💬 Chat Result: {result[:100]}..." if len(str(result)) > 100 else f"💬 Chat Result: {result}")
                else:
                    # Automation
                    result = await Automation(decision_list)
                    print(f"⚙️ Automation Result: {result}")
                
                await asyncio.sleep(1)  # Brief pause
                
            except Exception as e:
                print(f"❌ Error in {test_name}: {e}")
        
        # Test chat features
        print(f"\n💬 Testing Chat Features:")
        print("-" * 30)
        
        chat_tests = [
            "What is artificial intelligence?",
            "Tell me a joke about programming",
            "Explain quantum computing in simple terms"
        ]
        
        for question in chat_tests:
            try:
                print(f"\n❓ Question: '{question}'")
                result = await asyncio.to_thread(ChatBot, question)
                print(f"🤖 {self.Assistantname}: {result[:150]}..." if len(result) > 150 else f"🤖 {self.Assistantname}: {result}")
            except Exception as e:
                print(f"❌ Chat error: {e}")
        
        # Test realtime search
        print(f"\n🌐 Testing Realtime Search:")
        print("-" * 30)
        
        search_tests = [
            "latest technology news today",
            "current weather forecast"
        ]
        
        for query in search_tests:
            try:
                print(f"\n🔍 Query: '{query}'")
                result = await asyncio.to_thread(RealtimeSearchEngine, query)
                print(f"🌐 Result: {result[:150]}..." if len(str(result)) > 150 else f"🌐 Result: {result}")
            except Exception as e:
                print(f"❌ Search error: {e}")
        
        print(f"\n✅ Demo completed! All features tested.")
        print("=" * 50)
        
    async def interactive_mode(self):
        """Interactive mode for testing specific commands"""
        print("\n🎯 Interactive Mode - Type commands to test")
        print("Commands: automation, chat, search, or 'quit' to exit")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    break
                    
                if not user_input:
                    continue
                
                print(f"Processing: '{user_input}'")
                
                # Determine type and process
                decision_list = FirstlayerDMM(user_input)
                print(f"Decision: {decision_list}")
                
                if decision_list and any("realtime" in d.lower() for d in decision_list):
                    result = await asyncio.to_thread(RealtimeSearchEngine, QueryModifier(user_input))
                    print(f"🌐 {self.Assistantname}: {result}")
                elif decision_list and any("general" in d.lower() for d in decision_list):
                    result = await asyncio.to_thread(ChatBot, QueryModifier(user_input))
                    print(f"💬 {self.Assistantname}: {result}")
                else:
                    result = await Automation(decision_list)
                    print(f"⚙️ {self.Assistantname}: {result}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Goodbye!")

async def main():
    demo = JarvisDemo()
    
    print("Choose mode:")
    print("1. Full Feature Demo")
    print("2. Interactive Testing")
    
    try:
        choice = input("Enter choice (1/2): ").strip()
        
        if choice == "1":
            await demo.test_all_features()
        elif choice == "2":
            await demo.interactive_mode()
        else:
            print("Invalid choice, running full demo...")
            await demo.test_all_features()
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

if __name__ == "__main__":
    asyncio.run(main())