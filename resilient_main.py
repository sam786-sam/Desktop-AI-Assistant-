#!/usr/bin/env python3
"""
Resilient Jarvis Assistant - Enhanced Error Recovery
This version includes comprehensive error handling and automatic recovery
"""

import asyncio
import sys
import os
import time
import threading
import traceback

# Add paths
sys.path.append(os.path.dirname(__file__))

# Import main components with error handling
try:
    from Main import (
        first_thread_logic,
        start_main_async_loop,
        InitialExecution,
        SecondThread,
        SetMicrophoneStatus,
        SetAssistantStatus
    )
    from speechtotext import start_continuous_listening, stop_continuous_listening
    from rich.console import Console
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

console = Console()

class ResilientJarvis:
    def __init__(self):
        self.running = True
        self.restart_count = 0
        self.max_restarts = 10
        self.main_thread = None
        self.gui_thread = None
        self.async_thread = None
        
    def start_system(self):
        """Start the complete Jarvis system with error recovery"""
        
        console.print("\n🚀 [bold green]Starting Resilient Jarvis Assistant[/bold green]")
        console.print("=" * 60)
        
        while self.running and self.restart_count < self.max_restarts:
            try:
                console.print(f"\n🔄 Starting system (Attempt {self.restart_count + 1})...")
                
                # Initialize the system
                self.initialize_system()
                
                # Start all threads
                self.start_all_threads()
                
                # Monitor system health
                self.monitor_system()
                
            except KeyboardInterrupt:
                console.print("\n\n👋 [yellow]System stopped by user[/yellow]")
                self.running = False
                break
                
            except Exception as e:
                console.print(f"\n❌ [red]System error: {e}[/red]")
                traceback.print_exc()
                
                self.restart_count += 1
                if self.restart_count < self.max_restarts:
                    console.print(f"🔄 [yellow]Restarting system... ({self.restart_count}/{self.max_restarts})[/yellow]")
                    self.cleanup_threads()
                    time.sleep(5)  # Wait before restart
                else:
                    console.print("❌ [red]Max restart attempts reached. Exiting.[/red]")
                    break
        
        self.shutdown()
    
    def initialize_system(self):
        """Initialize the Jarvis system"""
        try:
            console.print("📋 [blue]Initializing system components...[/blue]")
            
            # Set initial status
            SetMicrophoneStatus("True")
            SetAssistantStatus("Initializing...")
            
            # Initialize the chat and GUI
            InitialExecution()
            
            console.print("✅ [green]System initialized successfully[/green]")
            
        except Exception as e:
            console.print(f"❌ [red]Initialization error: {e}[/red]")
            raise
    
    def start_all_threads(self):
        """Start all system threads"""
        try:
            console.print("🧵 [blue]Starting system threads...[/blue]")
            
            # Start async event loop thread
            self.async_thread = threading.Thread(target=start_main_async_loop, daemon=True)
            self.async_thread.start()
            console.print("✅ Async thread started")
            
            # Wait a moment for async loop to initialize
            time.sleep(2)
            
            # Start main logic thread
            self.main_thread = threading.Thread(target=first_thread_logic, daemon=True)
            self.main_thread.start()
            console.print("✅ Main logic thread started")
            
            # Start GUI thread
            self.gui_thread = threading.Thread(target=SecondThread, daemon=False)
            self.gui_thread.start()
            console.print("✅ GUI thread started")
            
            console.print("🎉 [green]All threads started successfully![/green]")
            
        except Exception as e:
            console.print(f"❌ [red]Thread startup error: {e}[/red]")
            raise
    
    def monitor_system(self):
        """Monitor system health and restart if needed"""
        console.print("\n🔍 [blue]System monitoring started...[/blue]")
        console.print("💡 [yellow]The system is now ready for voice commands![/yellow]")
        console.print("🎤 [green]Say commands like:[/green]")
        console.print("   • 'open WhatsApp'")
        console.print("   • 'volume up'")  
        console.print("   • 'google search AI news'")
        console.print("   • 'open notepad and volume up'")
        console.print("\n📊 [cyan]System Status:[/cyan]")
        
        last_health_check = time.time()
        health_check_interval = 30  # seconds
        
        while self.running:
            try:
                current_time = time.time()
                
                # Periodic health check
                if current_time - last_health_check > health_check_interval:
                    self.check_system_health()
                    last_health_check = current_time
                
                # Check if GUI thread is still alive (main indicator)
                if self.gui_thread and not self.gui_thread.is_alive():
                    console.print("⚠️ [yellow]GUI thread stopped, system may need restart[/yellow]")
                    break
                
                time.sleep(1)
                
            except Exception as e:
                console.print(f"❌ [red]Monitor error: {e}[/red]")
                time.sleep(5)
    
    def check_system_health(self):
        """Check the health of system components"""
        try:
            # Check thread status
            threads_status = {
                "GUI": self.gui_thread.is_alive() if self.gui_thread else False,
                "Main": self.main_thread.is_alive() if self.main_thread else False,
                "Async": self.async_thread.is_alive() if self.async_thread else False
            }
            
            active_threads = sum(1 for alive in threads_status.values() if alive)
            console.print(f"💚 [green]Health Check: {active_threads}/3 threads active[/green]")
            
            if active_threads < 2:
                console.print("⚠️ [yellow]System health degraded, may need restart[/yellow]")
                
        except Exception as e:
            console.print(f"❌ [red]Health check error: {e}[/red]")
    
    def cleanup_threads(self):
        """Clean up threads before restart"""
        try:
            console.print("🧹 [blue]Cleaning up threads...[/blue]")
            
            # Stop continuous listening
            try:
                stop_continuous_listening()
            except:
                pass
            
            # Reset thread references
            self.main_thread = None
            self.gui_thread = None
            self.async_thread = None
            
            # Brief pause for cleanup
            time.sleep(2)
            
        except Exception as e:
            console.print(f"⚠️ [yellow]Cleanup error: {e}[/yellow]")
    
    def shutdown(self):
        """Graceful shutdown"""
        try:
            console.print("\n🔄 [blue]Shutting down system...[/blue]")
            
            self.running = False
            
            # Stop continuous listening
            stop_continuous_listening()
            
            console.print("👋 [green]System shutdown complete[/green]")
            
        except Exception as e:
            console.print(f"⚠️ [yellow]Shutdown error: {e}[/yellow]")

def main():
    """Main entry point"""
    try:
        jarvis = ResilientJarvis()
        jarvis.start_system()
        
    except KeyboardInterrupt:
        console.print("\n\n👋 [yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n❌ [red]Fatal error: {e}[/red]")
        traceback.print_exc()

if __name__ == "__main__":
    main()