# --- ENHANCED WhatsApp.py ---

import pywhatkit
import pyautogui
import pyperclip
import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rich import print
import subprocess
import webbrowser
from datetime import datetime

class WhatsAppController:
    def __init__(self):
        self.driver = None
        self.is_web_active = False
        
    def initialize_whatsapp_web(self):
        """Initialize WhatsApp Web session"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--user-data-dir=whatsapp_session")
            chrome_options.add_experimental_option("detach", True)
            # Add more options to handle common issues
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.get("https://web.whatsapp.com")
            
            # Execute script to remove webdriver property to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("[WhatsApp] Opening WhatsApp Web. Please scan QR code if needed...")
            
            # Wait for user to scan QR code and login - try multiple selectors
            try:
                # Original selector
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
                )
            except:
                # Alternative selectors for the search box
                try:
                    WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-testid='search-chat-input']"))
                    )
                except:
                    WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@tabindex='0']"))
                    )
            
            self.is_web_active = True
            print("[WhatsApp] ✅ WhatsApp Web initialized successfully!")
            return True
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to initialize WhatsApp Web: {e}")
            return False

    def find_contact(self, contact_name):
        """Find and open a contact chat"""
        try:
            if not self.is_web_active:
                if not self.initialize_whatsapp_web():
                    return False
            
            # Click on search box - try multiple selectors
            search_box = None
            selectors = [
                "//div[@contenteditable='true'][@data-tab='3']",
                "//div[@contenteditable='true'][@data-testid='search-chat-input']",
                "//div[@contenteditable='true'][@tabindex='0']"
            ]
            
            for selector in selectors:
                try:
                    search_box = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if not search_box:
                print("[WhatsApp] ❌ Could not find search box")
                return False
                
            search_box.click()
            
            # Clear and type contact name
            search_box.clear()
            search_box.send_keys(contact_name)
            time.sleep(2)
            
            # Click on the contact - try multiple selectors
            contact_selectors = [
                f"//span[@title='{contact_name}']",
                f"//span[contains(text(), '{contact_name}')]",
                f"//div[contains(@title, '{contact_name}')]"
            ]
            
            contact_element = None
            for selector in contact_selectors:
                try:
                    contact_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if not contact_element:
                print(f"[WhatsApp] ❌ Could not find contact '{contact_name}'")
                return False
                
            contact_element.click()
            
            print(f"[WhatsApp] ✅ Contact '{contact_name}' found and opened")
            return True
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to find contact '{contact_name}': {e}")
            return False

    async def send_message(self, contact_name, message):
        """Send message to specific contact via WhatsApp desktop app - optimized version with search clearing"""
        try:
            print(f"[WhatsApp] Sending message to '{contact_name}': {message}")
            
            # CRITICAL: Ensure WhatsApp is fully loaded and ready
            import pygetwindow as gw
            import pyautogui
            import time
            from urllib.parse import quote_plus
            import webbrowser
            import subprocess
            
            # Step 1: Make sure WhatsApp window exists and is active
            whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
            
            if not whatsapp_windows:
                print("[WhatsApp] No WhatsApp window found, launching...")
                subprocess.run(['start', 'whatsapp:'], shell=True)
                time.sleep(3)  # Wait longer for launch
                
                # Try to find and activate window
                whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
                if whatsapp_windows:
                    whatsapp_windows[0].activate()
                    time.sleep(1)  # Wait after activation
                else:
                    print("[WhatsApp] Still no window, trying fallback...")
                    # Open WhatsApp Web as fallback
                    webbrowser.open('https://web.whatsapp.com')
                    time.sleep(5)  # Wait for browser to load
            else:
                # Activate existing window
                whatsapp_window = whatsapp_windows[0]
                whatsapp_window.activate()
                time.sleep(1)  # Wait for window to come to front
            
            print("[WhatsApp] ✅ WhatsApp window ready")
            
            # Step 2: Search for contact using Ctrl+F shortcut
            try:
                # Wait a bit to ensure WhatsApp is fully ready
                time.sleep(0.5)
                
                # CRITICAL: Use Ctrl+F to activate/focus the search bar
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.8)  # Wait for search bar to focus
                
                # NOW use Ctrl+A to select all text in search bar, then backspace to clear
                pyautogui.hotkey('ctrl', 'a')  # Select all text in search bar
                time.sleep(0.2)
                pyautogui.press('backspace')  # Clear the selected text
                time.sleep(0.3)
                
                # CRITICAL: Clean contact name - remove ALL special characters except letters, numbers, and spaces
                import re
                cleaned_contact = re.sub(r'[^a-zA-Z0-9\s]', '', str(contact_name))
                
                # IMPORTANT: Type the contact name EXACTLY as provided (no extra chars)
                pyautogui.typewrite(cleaned_contact, interval=0.08)  # Slower typing
                time.sleep(2.5)  # Wait LONGER for search results to fully load
                
                # CRITICAL: Press Enter directly to open the first matching contact
                # Don't use down arrow - just press Enter twice to ensure it opens
                pyautogui.press('enter')  # Select first result
                time.sleep(0.5)
                pyautogui.press('enter')  # Open chat (backup in case first didn't work)
                time.sleep(2.0)  # Wait LONGER for chat window to fully load
                
                # Verify chat opened by clicking message input box
                screen_width, screen_height = pyautogui.size()
                message_input_x = screen_width // 2
                message_input_y = int(screen_height * 0.85)
                
                pyautogui.click(x=message_input_x, y=message_input_y)
                time.sleep(0.8)  # Wait longer after click
                
                # Type the message EXACTLY as provided - use clipboard to avoid "typing" indicator
                import pyperclip
                pyperclip.copy(message)
                time.sleep(0.2)
                pyautogui.hotkey('ctrl', 'v')  # Paste message instead of typing
                time.sleep(0.3)
                
                # Send the message by pressing Enter
                pyautogui.press('enter')
                time.sleep(0.2)
                
                print(f"[WhatsApp] ✅ SUCCESS! Message sent to {contact_name}")
                return True
                
            except Exception as e:
                print(f"[WhatsApp] Search method failed: {e}")
                # Fallback to URL method
                pass
            
            # Step 3: Fallback - Use WhatsApp URL
            try:
                if contact_name.startswith('+') or contact_name.replace('-', '').replace(' ', '').isdigit():
                    phone_number = contact_name.replace('-', '').replace(' ', '')
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number
                    
                    print(f"[WhatsApp] Using WhatsApp URL for {phone_number}")
                    encoded_message = quote_plus(message)
                    whatsapp_url = f"https://web.whatsapp.com/send?phone={phone_number}&text={encoded_message}"
                    
                    webbrowser.open(whatsapp_url)
                    time.sleep(3)
                    
                    # Try to send
                    pyautogui.press('enter')
                    time.sleep(1)
                    print(f"[WhatsApp] ✅ Message sent via web for {contact_name}")
                    return True
                else:
                    # For contact names, open WhatsApp and let user select
                    whatsapp_url = "https://web.whatsapp.com"
                    webbrowser.open(whatsapp_url)
                    print(f"[WhatsApp] ✅ WhatsApp opened - please select {contact_name} and send: {message}")
                    return True
                    
            except Exception as e:
                print(f"[WhatsApp] Fallback method failed: {e}")
                return False
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to send message: {e}")
            return False

    def read_recent_messages(self, contact_name=None, count=10):
        """Read recent messages from a contact or all chats"""
        try:
            if not self.is_web_active:
                if not self.initialize_whatsapp_web():
                    return []
            
            messages = []
            
            if contact_name:
                # Read from specific contact
                if not self.find_contact(contact_name):
                    return []
                
                # Get messages from the chat
                message_elements = self.driver.find_elements(By.XPATH, "//div[@class='_3-8er']//span[@dir='ltr']")
                
                for element in message_elements[-count:]:  # Get last 'count' messages
                    try:
                        message_text = element.text
                        if message_text.strip():
                            # Try to get timestamp and sender info
                            timestamp_elem = element.find_element(By.XPATH, ".//../..//div[@class='_3EFt_']")
                            timestamp = timestamp_elem.text if timestamp_elem else datetime.now().strftime("%H:%M")
                            
                            messages.append({
                                "contact": contact_name,
                                "message": message_text,
                                "timestamp": timestamp,
                                "datetime": datetime.now().isoformat()
                            })
                    except:
                        continue
                        
            else:
                # Read from recent chats
                chat_elements = self.driver.find_elements(By.XPATH, "//div[@role='listitem']//div[@title]")
                
                for i, chat in enumerate(chat_elements[:count]):
                    try:
                        chat_title = chat.get_attribute('title')
                        chat.click()
                        time.sleep(1)
                        
                        # Get last message from this chat
                        last_message_elem = self.driver.find_elements(By.XPATH, "//div[@class='_3-8er']//span[@dir='ltr']")
                        if last_message_elem:
                            last_message = last_message_elem[-1].text
                            messages.append({
                                "contact": chat_title,
                                "message": last_message,
                                "timestamp": datetime.now().strftime("%H:%M"),
                                "datetime": datetime.now().isoformat()
                            })
                            
                    except Exception as e:
                        print(f"[WhatsApp] Error reading from chat {i}: {e}")
                        continue
            
            print(f"[WhatsApp] ✅ Read {len(messages)} recent messages")
            return messages
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to read messages: {e}")
            return []

    async def make_call(self, contact_name):
        """Make a voice call to contact - optimized version"""
        try:
            print(f"[WhatsApp] Calling {contact_name}")
            
            # Quick window activation
            try:
                import pygetwindow as gw
                import pyautogui
                import time
                import webbrowser
                import subprocess
                from urllib.parse import quote_plus
                
                # Find and activate WhatsApp
                whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
                
                if whatsapp_windows:
                    whatsapp_window = whatsapp_windows[0]
                    whatsapp_window.activate()
                    time.sleep(0.3)
                else:
                    # Launch WhatsApp
                    subprocess.run(['start', 'whatsapp:'], shell=True)
                    time.sleep(1.5)
                    whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
                    if whatsapp_windows:
                        whatsapp_windows[0].activate()
                        time.sleep(0.3)
                        
            except Exception as e:
                print(f"[WhatsApp] Window error: {e}")
            
            # Direct search and call
            try:
                # Wait for WhatsApp to be ready
                time.sleep(1.0)
                
                # Click to ensure focus on search area
                pyautogui.click(x=150, y=80)
                time.sleep(0.5)
                
                # Clear previous search
                for _ in range(3):
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.press('backspace')
                    time.sleep(0.1)
                time.sleep(0.3)
                
                # Search for contact
                pyautogui.typewrite(contact_name, interval=0.05)
                time.sleep(1.5)  # Wait for search results
                
                # Press Enter to select and open chat
                pyautogui.press('enter')
                time.sleep(1.2)  # Wait for chat window to load
                
                # Look for call button - click on top right area where call buttons are located
                screen_width, screen_height = pyautogui.size()
                call_button_x = int(screen_width * 0.88)
                call_button_y = int(screen_height * 0.12)
                pyautogui.click(x=call_button_x, y=call_button_y)
                time.sleep(0.5)
                
                # Press 'c' for voice call (WhatsApp Web shortcut)
                pyautogui.press('c')
                time.sleep(0.3)
                
                print(f"[WhatsApp] ✅ Voice call initiated to {contact_name}")
                return True
                
            except Exception as e:
                print(f"[WhatsApp] Direct call method failed: {e}")
            
            # Fallback for phone numbers
            if contact_name.startswith('+') or contact_name.replace('-', '').replace(' ', '').isdigit():
                try:
                    phone_number = contact_name.replace('-', '').replace(' ', '')
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number
                    
                    call_url = f"https://web.whatsapp.com/send?phone={phone_number}"
                    webbrowser.open(call_url)
                    time.sleep(1.5)
                    pyautogui.hotkey('ctrl', 'shift', 'c')
                    print(f"[WhatsApp] ✅ Call initiated via web for {contact_name}")
                    return True
                    
                except Exception as e:
                    print(f"[WhatsApp] Web call fallback failed: {e}")
            
            return False
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to make call: {e}")
            return False

    async def video_call(self, contact_name):
        """Make a video call to contact - optimized version"""
        try:
            print(f"[WhatsApp] Video calling {contact_name}")
            
            # Quick window activation
            try:
                import pygetwindow as gw
                import pyautogui
                import time
                import webbrowser
                import subprocess
                from urllib.parse import quote_plus
                
                # Find and activate WhatsApp
                whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
                
                if whatsapp_windows:
                    whatsapp_window = whatsapp_windows[0]
                    whatsapp_window.activate()
                    time.sleep(0.3)
                else:
                    # Launch WhatsApp
                    subprocess.run(['start', 'whatsapp:'], shell=True)
                    time.sleep(1.5)
                    whatsapp_windows = [window for window in gw.getWindowsWithTitle('WhatsApp') if window.title.startswith('WhatsApp')]
                    if whatsapp_windows:
                        whatsapp_windows[0].activate()
                        time.sleep(0.3)
                        
            except Exception as e:
                print(f"[WhatsApp] Window error: {e}")
            
            # Direct search and video call
            try:
                # Search for contact
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.2)
                pyautogui.press('backspace')
                time.sleep(0.1)
                pyautogui.typewrite(contact_name)
                time.sleep(0.3)
                
                # Select contact and initiate video call
                pyautogui.press('down')
                time.sleep(0.1)
                pyautogui.press('enter')  # Open chat
                time.sleep(0.2)
                
                # Video call shortcut (Ctrl+Shift+V)
                pyautogui.hotkey('ctrl', 'shift', 'v')
                print(f"[WhatsApp] ✅ Video call initiated to {contact_name}")
                return True
                
            except Exception as e:
                print(f"[WhatsApp] Direct video call method failed: {e}")
            
            # Fallback for phone numbers
            if contact_name.startswith('+') or contact_name.replace('-', '').replace(' ', '').isdigit():
                try:
                    phone_number = contact_name.replace('-', '').replace(' ', '')
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number
                    
                    call_url = f"https://web.whatsapp.com/send?phone={phone_number}"
                    webbrowser.open(call_url)
                    time.sleep(1.5)
                    pyautogui.hotkey('ctrl', 'shift', 'v')
                    print(f"[WhatsApp] ✅ Video call initiated via web for {contact_name}")
                    return True
                    
                except Exception as e:
                    print(f"[WhatsApp] Web video call fallback failed: {e}")
            
            return False
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to make video call: {e}")
            return False

    def get_contact_status(self, contact_name):
        """Get contact's online status"""
        try:
            if not self.find_contact(contact_name):
                return "Unknown"
            
            # Look for status indicators
            status_elements = self.driver.find_elements(By.XPATH, "//span[contains(@title,'online') or contains(@title,'last seen')]")
            
            if status_elements:
                return status_elements[0].get_attribute('title')
            
            return "Status not available"
            
        except Exception as e:
            print(f"[WhatsApp] ❌ Failed to get status: {e}")
            return "Error"

    def close_session(self):
        """Close WhatsApp Web session"""
        try:
            if self.driver:
                self.driver.quit()
                self.is_web_active = False
                print("[WhatsApp] ✅ Session closed")
        except Exception as e:
            print(f"[WhatsApp] ❌ Error closing session: {e}")

# Global WhatsApp controller instance
whatsapp_controller = WhatsAppController()

# Backward compatibility functions
async def SendWhatsAppMessage(contact, message):
    """Send WhatsApp message - enhanced version"""
    return await whatsapp_controller.send_message(contact, message)

async def ReadRecentMessages(contact=None, count=10):
    """Read recent WhatsApp messages"""
    return whatsapp_controller.read_recent_messages(contact, count)

async def MakeWhatsAppCall(contact):
    """Make WhatsApp voice call"""
    return await whatsapp_controller.make_call(contact)

async def MakeWhatsAppVideoCall(contact):
    """Make WhatsApp video call"""
    return await whatsapp_controller.video_call(contact)

def GetContactStatus(contact):
    """Get contact's WhatsApp status"""
    return whatsapp_controller.get_contact_status(contact)

# Usage Examples:
if __name__ == "__main__":
    import asyncio
    
    async def test_whatsapp():
        # Initialize
        controller = WhatsAppController()
        
        # Send message
        await controller.send_message("John Doe", "Hello from enhanced WhatsApp!")
        
        # Read recent messages
        messages = controller.read_recent_messages("John Doe", 5)
        print("Recent messages:", messages)
        
        # Make a call
        await controller.make_call("John Doe")
        
        # Close session
        controller.close_session()
    
    # Run test
    # asyncio.run(test_whatsapp())
    print("[WhatsApp] Enhanced WhatsApp module loaded successfully!")