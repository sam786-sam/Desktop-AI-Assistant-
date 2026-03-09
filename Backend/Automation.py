# --- START OF FILE Automation.py ---

import subprocess
import asyncio
import os
import sys
import requests
from AppOpener import open as AppOpen, close as AppClose
from webbrowser import open as webopen
from pywhatkit import playonyt
from bs4 import BeautifulSoup
from dotenv import dotenv_values
from rich import print
import keyboard
import win32api
import win32con
import json
import webbrowser
from urllib.parse import quote_plus
import time

# -----------------------------
# Optional WMI Import
# -----------------------------
try:
    import wmi
except ModuleNotFoundError:
    wmi = None
    print("[Automation] Warning: 'wmi' module not installed. WMI-dependent features will be disabled.")

# -----------------------------
# Helper Functions for Automation
# -----------------------------

async def GoogleSearch(Topic):
    try:
        webopen(f"https://www.google.com/search?q={requests.utils.quote(Topic)}")
        return True
    except Exception as e:
        print(f"[Automation] GoogleSearch Error: {e}")
        return False

async def YoutubeSearch(Topic):
    """Enhanced YouTube search with better formatting and error handling"""
    try:
        # Clean and format the search query
        cleaned_topic = Topic.strip()
        encoded_topic = quote_plus(cleaned_topic)
        search_url = f"https://www.youtube.com/results?search_query={encoded_topic}"
        
        print(f"[YouTube] Searching for: '{cleaned_topic}'")
        webbrowser.open(search_url)
        print(f"[YouTube] ✅ Search opened in browser")
        return True
    except Exception as e:
        print(f"[Automation] YoutubeSearch Error: {e}")
        return False

async def YoutubePlay(Topic):
    """Enhanced YouTube play with direct video playback"""
    try:
        # Clean and format the search query
        cleaned_topic = Topic.strip()
        print(f"[YouTube] Playing: '{cleaned_topic}'")
        
        # Try pywhatkit first for direct play
        try:
            playonyt(cleaned_topic)
            print(f"[YouTube] ✅ Video started playing")
            return True
        except Exception as pywhatkit_error:
            print(f"[YouTube] Pywhatkit failed, using search fallback: {pywhatkit_error}")
            # Fallback to search
            return await YoutubeSearch(cleaned_topic)
            
    except Exception as e:
        print(f"[Automation] YoutubePlay Error: {e}")
        return False

async def PlayYoutube(query):
    try:
        playonyt(query)
        return True
    except Exception as e:
        print(f"[Automation] PlayYoutube Error: {e}")
        await YoutubeSearch(query)
        return False

async def OpenApp(app):
    try:
        # Map common app names to their actual executable names
        app_name_mapping = {
            "chrome": "Google Chrome",
            "brave": "Brave",
            "firefox": "Mozilla Firefox",
            "edge": "Microsoft Edge",
            "notepad": "notepad",
            "calculator": "calculator",
            "settings": "settings",
            "control panel": "control",
            "file explorer": "explorer",
            "youtube": "chrome",
            "whatsapp": "whatsapp",
            "spotify": "spotify",
            "vlc": "vlc",
            "vs code": "code",
            "visual studio code": "code",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "outlook": "outlook"
        }
        
        # Try to find a mapped name, otherwise use the original
        normalized_app = app.strip().lower()
        if normalized_app in app_name_mapping:
            actual_app = app_name_mapping[normalized_app]
        else:
            actual_app = app
        
        print(f"[Automation] Attempting to open: {actual_app}")
        AppOpen(actual_app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as e:
        print(f"[Automation] OpenApp Error: {e}")
        # Try alternative methods if AppOpener fails
        return await open_app_alternative(app)
        
async def CloseApp(app):
    try:
        # Map common app names to their actual executable names (same mapping as OpenApp)
        app_name_mapping = {
            "chrome": "Google Chrome",
            "brave": "Brave",
            "firefox": "Mozilla Firefox",
            "edge": "Microsoft Edge",
            "notepad": "notepad",
            "calculator": "calculator",
            "settings": "settings",
            "control panel": "control",
            "file explorer": "explorer",
            "youtube": "chrome",
            "whatsapp": "whatsapp",
            "spotify": "spotify",
            "vlc": "vlc",
            "vs code": "code",
            "visual studio code": "code",
            "word": "winword",
            "excel": "excel",
            "powerpoint": "powerpnt",
            "outlook": "outlook"
        }
        
        # Try to find a mapped name, otherwise use the original
        normalized_app = app.strip().lower()
        if normalized_app in app_name_mapping:
            actual_app = app_name_mapping[normalized_app]
        else:
            actual_app = app
            
        print(f"[Automation] Attempting to close: {actual_app}")
        AppClose(actual_app, match_closest=True, output=True, throw_error=True)
        return True
    except Exception as e:
        print(f"[Automation] CloseApp Error: {e}")
        # Try alternative methods if AppOpener fails
        return await close_app_alternative(app)

async def open_app_alternative(app_name):
    """Alternative method to open applications using subprocess"""
    try:
        app_name = app_name.strip().lower()
        
        # Define common applications and their commands
        app_commands = {
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "settings": ["ms-settings:"],
            "control panel": ["control.exe"],
            "file explorer": ["explorer.exe"],
            "command prompt": ["cmd.exe"],
            "powershell": ["powershell.exe"],
            "task manager": ["taskmgr.exe"],
            "paint": ["mspaint.exe"],
            "wordpad": ["write.exe"],
            "camera": ["microsoft.windows.camera:"],
            "mail": ["outlookmail:"],
            "calendar": ["outlookcal:"],
            "photos": ["ms-photos:"],
            "store": ["ms-windows-store:"],
            "maps": ["bingmaps:"],
            "alarms": ["ms-alarms:"],
            "clock": ["timedate.cpl"],
            "sticky notes": ["stikynot.exe"],
            "snipping tool": ["snippingtool.exe"],
            "voice recorder": ["ms-callrecording:"],
            "feedback": ["feedback-hub:"],
            "get started": ["getstarted.exe"],
            "windows defender": ["windowsdefender:"],
            "windows update": ["ms-settings:windowsupdate"],
            "network settings": ["ms-settings:network"],
            "bluetooth settings": ["ms-settings:bluetooth"],
            "sound settings": ["sndvol.exe"],
            "display settings": ["desk.cpl"],
            "date and time": ["timedate.cpl"],
            "mouse settings": ["main.cpl"],
            "keyboard settings": ["intl.cpl"],
            "printer settings": ["printers.cpl"],
            "system info": ["msinfo32.exe"],
            "disk cleanup": ["cleanmgr.exe"],
            "defragment": ["dfrgui.exe"],
            "backup and restore": ["sdclt.exe"],
            "windows firewall": ["firewall.cpl"],
            "user accounts": ["netplwiz.exe"],
            "system properties": ["sysdm.cpl"],
            "performance": ["perfmon.exe"],
            "reliability": ["perfcenter.cpl"],
            "event viewer": ["eventvwr.msc"],
            "local security policy": ["secpol.msc"],
            "services": ["services.msc"],
            "device manager": ["devmgmt.msc"],
            "disk management": ["diskmgmt.msc"],
            "group policy": ["gpedit.msc"],
            "registry editor": ["regedit.exe"],
            "system configuration": ["msconfig.exe"],
            "task scheduler": ["taskschd.msc"],
            "windows mobility center": ["mblctr.exe"],
            "windows activation": ["slui.exe"],
            "windows troubleshoot": ["msdt.exe"],
            "windows firewall advanced": ["wf.msc"],
            "windows features": ["optionalfeatures.exe"],
            "windows defender security": ["securitycentercpl.dll"],
            "windows defender virus": ["mpcmdrun.exe"],
            "windows memory diagnostic": ["mdsched.exe"],
            "windows network diagnostics": ["ncpa.cpl"],
            "windows power options": ["powercfg.cpl"],
            "windows sound recording": ["soundrecorder.exe"],
            "windows sync center": ["synccenter.exe"],
            "windows troubleshooter": ["msdt.exe"],
            "windows update settings": ["ms-settings:updates"],
            "windows accessibility": ["utilman.exe"],
            "windows ease of access": ["osk.exe"],
            "windows magnifier": ["magnify.exe"],
            "windows narrator": ["narrator.exe"],
            "windows on-screen keyboard": ["osk.exe"],
            "windows speech recognition": ["microsoft.windows.speech:"],
            "windows voice access": ["ms-voiceaccess:"],
            "chrome": ["chrome.exe"],
            "firefox": ["firefox.exe"],
            "edge": ["msedge.exe"],
            "brave": ["brave.exe"],
            "whatsapp": ["whatsapp.exe"],
            "spotify": ["spotify.exe"],
            "vlc": ["vlc.exe"],
            "vs code": ["code.exe"],
            "visual studio code": ["code.exe"],
            "word": ["winword.exe"],
            "excel": ["excel.exe"],
            "powerpoint": ["powerpnt.exe"],
            "outlook": ["outlook.exe"],
            "onenote": ["onenote.exe"],
            "skype": ["skype.exe"],
            "teams": ["teams.exe"],
            "zoom": ["zoom.exe"],
            "discord": ["discord.exe"],
            "telegram": ["telegram.exe"],
            "steam": ["steam.exe"],
            "vlc media player": ["vlc.exe"],
            "adobe reader": ["acrord32.exe"],
            "acrobat reader": ["acrord32.exe"],
            "winrar": ["winrar.exe"],
            "7zip": ["7z.exe"],
            "utorrent": ["utorrent.exe"],
            "bitTorrent": ["bittorrent.exe"],
            "itunes": ["itunes.exe"],
            "vlc player": ["vlc.exe"],
            "media player": ["wmplayer.exe"],
            "windows media player": ["wmplayer.exe"],
            "vlc media": ["vlc.exe"],
            "adobe acrobat": ["acrobat.exe"],
            "acrobat": ["acrobat.exe"],
            "virtualbox": ["virtualbox.exe"],
            "vmware": ["vmware.exe"],
            "android studio": ["studio64.exe"],
            "intellij idea": ["idea64.exe"],
            "pycharm": ["pycharm64.exe"],
            "webstorm": ["webstorm64.exe"],
            "phpstorm": ["phpstorm64.exe"],
            "datagrip": ["datagrip64.exe"],
            "rubymine": ["rubymine64.exe"],
            "clion": ["clion64.exe"],
            "goland": ["goland64.exe"],
            "rider": ["rider64.exe"],
            "resharper": ["resharper64.exe"],
            "unity": ["unity.exe"],
            "unreal engine": ["unreal.exe"],
            "blender": ["blender.exe"],
            "autocad": ["acad.exe"],
            "photoshop": ["photoshop.exe"],
            "illustrator": ["illustrator.exe"],
            "premiere": ["premiere.exe"],
            "after effects": ["afterfx.exe"],
            "lightroom": ["lightroom.exe"],
            "indesign": ["indesign.exe"],
            "acrobat": ["acrobat.exe"],
            "dreamweaver": ["dreamweaver.exe"],
            "flash": ["flash.exe"],
            "animator": ["animator.exe"],
            "audition": ["audition.exe"],
            "prelude": ["prelude.exe"],
            "speedgrade": ["speedgrade.exe"],
            "encore": ["encore.exe"],
            "bridge": ["bridge.exe"],
            "ame": ["ame.exe"],
            "character animator": ["charanim.exe"],
            "dimension": ["dimension.exe"],
            "fuse": ["fuse.exe"],
            "premiere rush": ["prrush.exe"],
            "substance painter": ["substance_painter.exe"],
            "substance designer": ["substance_designer.exe"],
            "substance sampler": ["substance_sampler.exe"],
            "substance alchemist": ["substance_alchemist.exe"],
            "xd": ["xd.exe"],
            "fuse cc": ["fuse.exe"],
            "acrobat dc": ["acrobat.exe"],
            "acrobat reader dc": ["acrord32.exe"],
            "acrobat xi": ["acrobat.exe"],
            "acrobat x": ["acrobat.exe"],
            "acrobat 9": ["acrobat.exe"],
            "acrobat 8": ["acrobat.exe"],
            "acrobat 7": ["acrobat.exe"],
            "acrobat 6": ["acrobat.exe"],
            "acrobat 5": ["acrobat.exe"],
            "acrobat 4": ["acrobat.exe"],
            "acrobat 3": ["acrobat.exe"],
            "acrobat 2": ["acrobat.exe"],
            "acrobat 1": ["acrobat.exe"],
        }
        
        if app_name in app_commands:
            subprocess.Popen(app_commands[app_name])
            print(f"[Automation] Successfully opened {app_name} using alternative method")
            return True
        else:
            print(f"[Automation] Alternative method for {app_name} not found")
            return False
            
    except Exception as e:
        print(f"[Automation] Alternative open method failed: {e}")
        return False

async def close_app_alternative(app_name):
    """Alternative method to close applications using taskkill"""
    try:
        app_name = app_name.strip().lower()
        
        # Map common names to actual process names
        process_names = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "brave": "brave.exe",
            "whatsapp": "whatsapp.exe",
            "spotify": "spotify.exe",
            "vlc": "vlc.exe",
            "vs code": "code.exe",
            "visual studio code": "code.exe",
            "word": "winword.exe",
            "excel": "excel.exe",
            "powerpoint": "powerpnt.exe",
            "outlook": "outlook.exe",
            "onenote": "onenote.exe",
            "skype": "skype.exe",
            "teams": ["teams.exe", "teams.exe"],
            "zoom": "zoom.exe",
            "discord": "discord.exe",
            "telegram": "telegram.exe",
            "steam": "steam.exe",
            "vlc media player": "vlc.exe",
            "windows media player": "wmplayer.exe",
            "adobe reader": "acrord32.exe",
            "acrobat reader": "acrord32.exe",
            "winrar": "winrar.exe",
            "7zip": "7z.exe",
            "utorrent": "utorrent.exe",
            "bitTorrent": "bittorrent.exe",
            "itunes": "itunes.exe",
            "media player": "wmplayer.exe",
            "vlc media": "vlc.exe",
            "adobe acrobat": "acrobat.exe",
            "acrobat": "acrobat.exe",
            "virtualbox": "virtualbox.exe",
            "vmware": "vmware.exe",
            "android studio": "studio64.exe",
            "intellij idea": "idea64.exe",
            "pycharm": "pycharm64.exe",
            "webstorm": "webstorm64.exe",
            "phpstorm": "phpstorm64.exe",
            "datagrip": "datagrip64.exe",
            "rubymine": "rubymine64.exe",
            "clion": "clion64.exe",
            "goland": "goland64.exe",
            "rider": "rider64.exe",
            "resharper": "resharper64.exe",
            "unity": "unity.exe",
            "unreal engine": "unreal.exe",
            "blender": "blender.exe",
            "autocad": "acad.exe",
            "photoshop": "photoshop.exe",
            "illustrator": "illustrator.exe",
            "premiere": "premiere.exe",
            "after effects": "afterfx.exe",
            "lightroom": "lightroom.exe",
            "indesign": "indesign.exe",
            "acrobat": "acrobat.exe",
            "dreamweaver": "dreamweaver.exe",
            "flash": "flash.exe",
            "animator": "animator.exe",
            "audition": "audition.exe",
            "prelude": "prelude.exe",
            "speedgrade": "speedgrade.exe",
            "encore": "encore.exe",
            "bridge": "bridge.exe",
            "ame": "ame.exe",
            "character animator": "charanim.exe",
            "dimension": "dimension.exe",
            "fuse": "fuse.exe",
            "premiere rush": "prrush.exe",
            "substance painter": "substance_painter.exe",
            "substance designer": "substance_designer.exe",
            "substance sampler": "substance_sampler.exe",
            "substance alchemist": "substance_alchemist.exe",
            "xd": "xd.exe",
            "fuse cc": "fuse.exe",
            "acrobat dc": "acrobat.exe",
            "acrobat reader dc": "acrord32.exe",
            "acrobat xi": "acrobat.exe",
            "acrobat x": "acrobat.exe",
            "acrobat 9": "acrobat.exe",
            "acrobat 8": "acrobat.exe",
            "acrobat 7": "acrobat.exe",
            "acrobat 6": "acrobat.exe",
            "acrobat 5": "acrobat.exe",
            "acrobat 4": "acrobat.exe",
            "acrobat 3": "acrobat.exe",
            "acrobat 2": "acrobat.exe",
            "acrobat 1": "acrobat.exe",
        }
        
        if app_name in process_names:
            process_name = process_names[app_name]
            subprocess.run(["taskkill", "/f", "/im", process_name], check=True)
            print(f"[Automation] Successfully closed {app_name} using alternative method")
            return True
        else:
            # Try to kill by the app name directly
            try:
                subprocess.run(["taskkill", "/f", "/im", app_name + ".exe"], check=True)
                print(f"[Automation] Successfully closed {app_name} using direct method")
                return True
            except subprocess.CalledProcessError:
                print(f"[Automation] Alternative close method for {app_name} failed")
                return False
            
    except Exception as e:
        print(f"[Automation] Alternative close method failed: {e}")
        return False
    

async def SystemControl(command):
    """System-level controls that don't fit other categories"""
    try:
        if "restart" in command.lower():
            subprocess.run(["shutdown", "/r", "/t", "0"])
        elif "shutdown" in command.lower():
            subprocess.run(["shutdown", "/s", "/t", "0"])
        elif "lock" in command.lower():
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        else:
            return False
        return True
    except Exception as e:
        print(f"[Automation] System Control Error: {e}")
        return False

# -----------------------------
# WiFi and Bluetooth
# -----------------------------
async def WiFiControl(action):
    """Improved WiFi control with multiple fallback methods"""
    try:
        print(f"[WiFi] Attempting to {action} WiFi...")
        
        if action.lower() in ["on", "enable", "turn on"]:
            # Primary method: netsh command
            try:
                result = subprocess.run(
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"], 
                    check=True, capture_output=True, text=True, timeout=15
                )
                print("[WiFi] ✅ Primary method succeeded")
            except subprocess.CalledProcessError as e:
                print(f"[WiFi] Primary method failed: {e}")
                # Fallback method: PowerShell
                try:
                    result = subprocess.run([
                        "powershell", "-Command",
                        "Enable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"
                    ], check=True, capture_output=True, text=True, timeout=15)
                    print("[WiFi] ✅ Fallback method succeeded")
                except subprocess.CalledProcessError as e2:
                    print(f"[WiFi] ❌ Both methods failed: {e2}")
                    return False
            
            print("[WiFi] ✅ WiFi enabled successfully")
            return True
                
        elif action.lower() in ["off", "disable", "turn off"]:
            # Primary method: netsh command
            try:
                result = subprocess.run(
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"], 
                    check=True, capture_output=True, text=True, timeout=15
                )
                print("[WiFi] ✅ Primary method succeeded")
            except subprocess.CalledProcessError as e:
                print(f"[WiFi] Primary method failed: {e}")
                # Fallback method: PowerShell
                try:
                    result = subprocess.run([
                        "powershell", "-Command",
                        "Disable-NetAdapter -Name 'Wi-Fi' -Confirm:$false"
                    ], check=True, capture_output=True, text=True, timeout=15)
                    print("[WiFi] ✅ Fallback method succeeded")
                except subprocess.CalledProcessError as e2:
                    print(f"[WiFi] ❌ Both methods failed: {e2}")
                    return False
            
            print("[WiFi] ✅ WiFi disabled successfully")
            return True
        else:
            print(f"[WiFi] ❌ Unknown action: {action}")
            return False
            
    except Exception as e:
        print(f"[WiFi] ❌ Unexpected error: {e}")
        return False

async def BluetoothControl(action):
    """Improved Bluetooth control with multiple fallback methods"""
    try:
        print(f"[Bluetooth] Attempting to {action} Bluetooth...")
        
        if action.lower() in ["on", "enable", "turn on"]:
            # Try multiple methods for enabling Bluetooth
            methods = [
                # Method 1: PowerShell PnP device control
                [
                    "powershell", "-Command", 
                    "Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'Error'} | Enable-PnpDevice -Confirm:$false"
                ],
                # Method 2: Direct Bluetooth service control
                [
                    "powershell", "-Command",
                    "Set-Service bthserv -StartupType Automatic; Start-Service bthserv"
                ],
                # Method 3: Alternative PnP approach
                [
                    "powershell", "-Command",
                    "Enable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth).InstanceId -Confirm:$false"
                ]
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    result = subprocess.run(method, check=True, capture_output=True, text=True, timeout=20)
                    print(f"[Bluetooth] ✅ Method {i} succeeded")
                    break
                except subprocess.CalledProcessError as e:
                    print(f"[Bluetooth] Method {i} failed: {e}")
                    if i == len(methods):
                        print("[Bluetooth] ❌ All methods failed")
                        return False
                    continue
            
            print("[Bluetooth] ✅ Bluetooth enabled successfully")
            return True
                
        elif action.lower() in ["off", "disable", "turn off"]:
            # Try multiple methods for disabling Bluetooth
            methods = [
                # Method 1: PowerShell PnP device control
                [
                    "powershell", "-Command", 
                    "Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq 'OK'} | Disable-PnpDevice -Confirm:$false"
                ],
                # Method 2: Direct Bluetooth service control
                [
                    "powershell", "-Command",
                    "Stop-Service bthserv -Force; Set-Service bthserv -StartupType Disabled"
                ],
                # Method 3: Alternative PnP approach
                [
                    "powershell", "-Command",
                    "Disable-PnpDevice -InstanceId (Get-PnpDevice -Class Bluetooth).InstanceId -Confirm:$false"
                ]
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    result = subprocess.run(method, check=True, capture_output=True, text=True, timeout=20)
                    print(f"[Bluetooth] ✅ Method {i} succeeded")
                    break
                except subprocess.CalledProcessError as e:
                    print(f"[Bluetooth] Method {i} failed: {e}")
                    if i == len(methods):
                        print("[Bluetooth] ❌ All methods failed")
                        return False
                    continue
            
            print("[Bluetooth] ✅ Bluetooth disabled successfully")
            return True
        else:
            print(f"[Bluetooth] ❌ Unknown action: {action}")
            return False
            
    except Exception as e:
        print(f"[Bluetooth] ❌ Unexpected error: {e}")
        return False


# -----------------------------
# Brightness, Volume, Media
# -----------------------------
async def BrightnessControl(action):
    try:
        if action.lower() in ["up", "increase", "raise", "max"]:
            # Try multiple common brightness up key combinations
            try:
                keyboard.press_and_release("f6")  # Common brightness up key
            except:
                try:
                    keyboard.press_and_release("ctrl+shift+f6")
                except:
                    # Use PowerShell command as fallback
                    subprocess.run([
                        "powershell", "-Command",
                        "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)"
                    ], capture_output=True)
            print("[Automation] Brightness increased")
        elif action.lower() in ["down", "decrease", "lower"]:
            try:
                keyboard.press_and_release("f5")  # Common brightness down key
            except:
                try:
                    keyboard.press_and_release("ctrl+shift+f5")
                except:
                    # Use PowerShell command as fallback
                    subprocess.run([
                        "powershell", "-Command",
                        "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,50)"
                    ], capture_output=True)
            print("[Automation] Brightness decreased")
        else:
            return False
        return True
    except Exception as e:
        print(f"[Automation] Brightness Control Error: {e}")
        return False

async def VolumeControl(action):
    try:
        if action.lower() in ["up", "increase", "raise"]:
            try:
                keyboard.press_and_release("volume up")
            except:
                # Fallback to Windows API
                for i in range(5):  # Increase by 10% (5 * 2%)
                    win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0xA0000)
            print("[Automation] Volume increased")
        elif action.lower() in ["down", "decrease", "lower"]:
            try:
                keyboard.press_and_release("volume down")
            except:
                # Fallback to Windows API
                for i in range(5):  # Decrease by 10%
                    win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x90000)
            print("[Automation] Volume decreased")
        elif action.lower() in ["mute", "unmute", "toggle"]:
            try:
                keyboard.press_and_release("volume mute")
            except:
                # Fallback to Windows API
                win32api.SendMessage(-1, win32con.WM_APPCOMMAND, 0, 0x80000)
            print("[Automation] Volume muted/unmuted")
        else:
            return False
        return True
    except Exception as e:
        print(f"[Automation] Volume Control Error: {e}")
        return False

async def MediaControl(action):
    try:
        if action.lower() in ["next", "next song", "skip"]:
            keyboard.press_and_release("media next track")
        elif action.lower() in ["previous", "prev", "previous song", "back"]:
            keyboard.press_and_release("media prev track")
        elif action.lower() in ["pause", "stop"]:
            keyboard.press_and_release("media play pause")
        elif action.lower() in ["resume", "play"]:
            keyboard.press_and_release("media play pause")
        else:
            return False
        return True
    except Exception as e:
        print(f"[Automation] Media Control Error: {e}")
        return False

# -----------------------------
# Content Generation
# -----------------------------
async def GenerateImage(prompt):
    """Enhanced image generation with 3D support and multiple providers"""
    try:
        import subprocess
        import sys
        import threading
        import time
        
        # Check if this is a 3D image request
        is_3d_request = "3d" in prompt.lower() and ("generate" in prompt.lower() or "create" in prompt.lower())
        
        if is_3d_request:
            # Handle 3D image generation
            print(f"[ImageGen] 3D image request detected for: '{prompt}'")
            
            # Extract the actual subject for 3D generation
            subject = prompt.lower()
            for phrase in ["generate 3d image of", "create 3d image of", "3d image of", "generate 3d", "create 3d"]:
                if phrase in subject:
                    subject = subject.replace(phrase, "").strip()
                    break
            
            if not subject:
                print(f"[ImageGen] Could not extract subject for 3D generation")
                return False
            
            print(f"[ImageGen] Generating 3D image for: '{subject}'")
            
            # Save to data file for 3D generation
            data_folder = os.path.join(os.path.dirname(__file__), "..", "Data")
            os.makedirs(data_folder, exist_ok=True)
            
            with open(os.path.join(data_folder, "ImageGeneration.data"), "w", encoding="utf-8") as f:
                f.write(subject)
            
            # Execute the 3DImageGeneration.py script
            image_gen_script = os.path.join(os.path.dirname(__file__), "3DImageGeneration.py")
            
            def run_3d_generation():
                try:
                    result = subprocess.run([
                        sys.executable, image_gen_script
                    ], capture_output=True, text=True, timeout=180)
                    
                    if result.returncode == 0:
                        print(f"[ImageGen] ✅ 3D Image generation completed successfully")
                        print(f"[ImageGen] Output: {result.stdout[:500]}...")
                        return True
                    else:
                        print(f"[ImageGen] ❌ 3D Image generation failed with error: {result.stderr}")
                        return False
                except subprocess.TimeoutExpired:
                    print(f"[ImageGen] ❌ 3D Image generation timed out after 3 minutes")
                    return False
                except Exception as subproc_error:
                    print(f"[ImageGen] ❌ 3D Subprocess error: {subproc_error}")
                    return False
            
            # Run the subprocess in a separate thread
            thread = threading.Thread(target=run_3d_generation)
            thread.daemon = True
            thread.start()
            
            # Give the subprocess time to start
            time.sleep(0.5)
            
            print(f"[ImageGen] 🎨 3D Image generation started in background for: '{subject}'")
            return True
        else:
            # Handle regular 2D image generation
            # Clean the prompt
            cleaned_prompt = prompt.replace("generate image", "").replace("image of", "").strip()
            print(f"[ImageGen] Generating 2D image for: '{cleaned_prompt}'")
            
            # Save to data file for other components to use
            data_folder = os.path.join(os.path.dirname(__file__), "..", "Data")
            os.makedirs(data_folder, exist_ok=True)
            
            with open(os.path.join(data_folder, "ImageGeneration.data"), "w", encoding="utf-8") as f:
                f.write(cleaned_prompt)
            
            # Execute the ImageGeneration.py script to leverage its full functionality
            image_gen_script = os.path.join(os.path.dirname(__file__), "ImageGeneration.py")
            
            # Run the ImageGeneration script as a subprocess in a non-blocking way
            def run_image_generation():
                try:
                    result = subprocess.run([
                        sys.executable, image_gen_script
                    ], capture_output=True, text=True, timeout=180)
                    
                    if result.returncode == 0:
                        print(f"[ImageGen] ✅ 2D Image generation completed successfully")
                        print(f"[ImageGen] Output: {result.stdout[:500]}...")
                        return True
                    else:
                        print(f"[ImageGen] ❌ 2D Image generation failed with error: {result.stderr}")
                        return False
                except subprocess.TimeoutExpired:
                    print(f"[ImageGen] ❌ 2D Image generation timed out after 3 minutes")
                    return False
                except Exception as subproc_error:
                    print(f"[ImageGen] ❌ 2D Subprocess error: {subproc_error}")
                    return False
            
            # Run the subprocess in a separate thread
            thread = threading.Thread(target=run_image_generation)
            thread.daemon = True
            thread.start()
            
            # Give the subprocess time to start
            time.sleep(0.5)
            
            print(f"[ImageGen] 🖼️ 2D Image generation started in background for: '{cleaned_prompt}'")
            return True
            
    except Exception as e:
        print(f"[Automation] Image Generation Error: {e}")
        return False

async def Content(Topic):
    """Enhanced content generation with better formatting and file handling"""
    try:
        from .Chatbot import ChatBot
        Topic = Topic.replace("content", "").strip()
        content_prompt = f"Write detailed, well-structured content about: {Topic}. Include headings, subheadings, and organized information."
        
        print(f"[Content] Generating content for: '{Topic}'")
        generated_content = await asyncio.to_thread(ChatBot, content_prompt)
        
        # Create filename with timestamp to avoid conflicts
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_filename = "".join(c for c in Topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        file_name = os.path.join(os.path.dirname(__file__), "..", "Data", f"{safe_filename}_{timestamp}.txt")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(f"Content for: {Topic}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(generated_content)
        
        # Open in notepad
        subprocess.Popen(['notepad.exe', file_name])
        print(f"[Content] ✅ Content generated and opened: {file_name}")
        return True
    except Exception as e:
        print(f"[Automation] Content Generation Error: {e}")
        return False

# -----------------------------
# Enhanced App Controls
# -----------------------------
async def OpenMultipleApps(app_list):
    """Open multiple applications concurrently"""
    tasks = []
    for app in app_list:
        tasks.append(OpenApp(app.strip()))
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(result for result in results if result is not Exception)
    return False

async def CloseMultipleApps(app_list):
    """Close multiple applications concurrently"""
    tasks = []
    for app in app_list:
        tasks.append(CloseApp(app.strip()))
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return any(result for result in results if result is not Exception)
    return False

# -----------------------------
# WhatsApp and Communication Controls
# -----------------------------

async def WhatsAppControl(command_arg: str):
    """Control WhatsApp operations"""
    try:
        # Import WhatsApp module with fallbacks
        try:
            from .WhatsApp_Enhanced import whatsapp_controller
        except ImportError:
            try:
                from WhatsApp_Enhanced import whatsapp_controller
            except ImportError:
                print("[Automation] ❌ WhatsApp_Enhanced module not found")
                return False
        
        if "send" in command_arg.lower():
            # Format: "send:contact_name:message"
            parts = command_arg.split(":", 2)
            if len(parts) >= 3:
                contact = parts[1].strip()
                message = parts[2].strip()
                
                # Clean the message by removing command words
                message_words = ["send", "tell", "text", "message", "say", "a", "the"]
                for word in message_words:
                    message = message.replace(word, "").strip()
                message = message.strip('"\' ').strip()
                
                result = await whatsapp_controller.send_message(contact, message)
                return result
            
        elif "read" in command_arg.lower():
            # Format: "read:contact_name:count" or "read:count"
            parts = command_arg.split(":")
            if len(parts) >= 2:
                if parts[1].strip().isdigit():
                    count = int(parts[1].strip())
                    messages = whatsapp_controller.read_recent_messages(count=count)
                else:
                    contact = parts[1].strip()
                    count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 10
                    messages = whatsapp_controller.read_recent_messages(contact, count)
                print(f"[WhatsApp] Recent messages: {messages}")
                return True
            
        elif "call" in command_arg.lower():
            # Format: "call:contact_name"
            contact = command_arg.replace("call:", "").strip()
            result = await whatsapp_controller.make_call(contact)
            return result
            
        elif "video" in command_arg.lower():
            # Format: "video:contact_name"
            contact = command_arg.replace("video:", "").strip()
            result = await whatsapp_controller.video_call(contact)
            return result
            
        elif "status" in command_arg.lower():
            # Format: "status:contact_name"
            contact = command_arg.replace("status:", "").strip()
            status = whatsapp_controller.get_contact_status(contact)
            print(f"[WhatsApp] {contact} status: {status}")
            return True
            
        return False
        
    except Exception as e:
        print(f"[Automation] WhatsApp control error: {e}")
        return False

async def SendMessageControl(command_arg: str):
    """Send message control - simplified interface with better parsing"""
    try:
        print(f"[Automation] Raw command argument: '{command_arg}'")
        
        # Handle different formats with better parsing
        contact = ""
        message = ""
        
        # Format 1: "send [message] to [contact]" or "tell [message] to [contact]" etc.
        if " to " in command_arg and command_arg.startswith(("send", "tell", "text", "message")):
            # Split by " to " to separate message and contact
            parts = command_arg.split(" to ", 1)
            if len(parts) == 2:
                message_part = parts[0].strip()
                contact = parts[1].strip()
                
                # Clean the message part by removing command words
                message_words = ["send", "tell", "text", "message", "say"]
                clean_message = message_part
                for word in message_words:
                    clean_message = clean_message.replace(word, "").strip()
                message = clean_message
                
        # Format 2: "to [contact] saying [message]" 
        elif "to " in command_arg and " saying " in command_arg:
            to_index = command_arg.find("to ")
            saying_index = command_arg.find(" saying ")
            if to_index != -1 and saying_index != -1:
                contact = command_arg[to_index+3:saying_index].strip()
                message = command_arg[saying_index+8:].strip()
        
        # Format 3: "contact:message"
        elif ":" in command_arg:
            contact, message = command_arg.split(":", 1)
            contact = contact.strip()
            message = message.strip()
            
        # Format 4: "to [contact] [message]" (simple format)
        elif command_arg.startswith("to "):
            # Split into parts and take second as contact, rest as message
            parts = command_arg.split(" ", 2)  # Split into max 3 parts
            if len(parts) >= 2:
                contact = parts[1].strip()
                message = parts[2].strip() if len(parts) > 2 else "Hello"
        
        # Format 5: Fallback - try to extract from natural language
        else:
            # Try to find if there's a contact in the command
            parts = command_arg.split(" ", 2)
            if len(parts) >= 2:
                # Assume first word is contact, rest is message
                contact = parts[0].strip()
                message = " ".join(parts[1:]).strip()
            else:
                contact = command_arg.strip()
                message = "Hello"
        
        # Clean up contact name (remove common words that might be misparsed)
        # Common corrections for misrecognized names
        contact_corrections = {
            "smeer": "sameer",
            "bsh": "basha",
            "mohd": "mohammed",
            "mhd": "mohammed",
            "abdul": "abdullah",
            "syed": "sayed",
            "khan": "khan",
            "ali": "ali",
            "ahmed": "ahmed",
            "umar": "umar"
        }
        
        # Apply corrections
        for wrong, correct in contact_corrections.items():
            if wrong in contact.lower():
                contact = contact.lower().replace(wrong, correct).title()
                break
        
        print(f"[Automation] Parsed - Contact: '{contact}', Message: '{message}'")
        
        if not contact or not message.strip():
            print("[Automation] ❌ Failed to parse contact or message")
            return False
        
        # Import WhatsApp module
        try:
            from .WhatsApp_Enhanced import SendWhatsAppMessage
        except ImportError:
            try:
                from WhatsApp_Enhanced import SendWhatsAppMessage
            except ImportError:
                # Fallback to basic WhatsApp if enhanced version not available
                try:
                    from .WhatsApp import SendWhatsAppMessage
                except ImportError:
                    try:
                        from WhatsApp import SendWhatsAppMessage
                    except ImportError:
                        print("[Automation] ❌ WhatsApp module not found")
                        return False
        
        result = await SendWhatsAppMessage(contact, message)
        return result
        
    except Exception as e:
        print(f"[Automation] Send message error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def MakeCallControl(command_arg: str):
    """Make call control"""
    try:
        # Import WhatsApp module with fallbacks
        try:
            from .WhatsApp_Enhanced import MakeWhatsAppCall
        except ImportError:
            try:
                from WhatsApp_Enhanced import MakeWhatsAppCall
            except ImportError:
                # Fallback to basic WhatsApp if enhanced version not available
                try:
                    from .WhatsApp import SendWhatsAppMessage
                    # For basic WhatsApp, we'll simulate a call by sending a message
                    contact = command_arg.strip()
                    message = f"📞 Calling {contact}..."
                    return await SendWhatsAppMessage(contact, message)
                except ImportError:
                    try:
                        from WhatsApp import SendWhatsAppMessage
                        contact = command_arg.strip()
                        message = f"📞 Calling {contact}..."
                        return await SendWhatsAppMessage(contact, message)
                    except ImportError:
                        print("[Automation] ❌ WhatsApp module not found")
                        return False
        
        return await MakeWhatsAppCall(command_arg.strip())
        
    except Exception as e:
        print(f"[Automation] Make call error: {e}")
        return False

# -----------------------------
# Calendar and Reminder Controls
# -----------------------------
async def CalendarControl(command_arg: str):
    """Control calendar and reminder operations"""
    try:
        from .CalendarIntegration import CalendarIntegration
    except ImportError:
        try:
            from CalendarIntegration import CalendarIntegration
        except ImportError:
            print("[Automation] ❌ CalendarIntegration module not found")
            return False
    
    calendar_integration = CalendarIntegration()
    
    # Process the calendar command
    result = calendar_integration.process_calendar_command(command_arg)
    print(f"[Calendar] {result}")
    
    # In a real scenario, you might want to trigger TTS here
    # For now, just return True to indicate success
    return True

# -----------------------------
# Scheduler Controls
# -----------------------------

async def SetReminderControl(command_arg: str):
    """Set reminder control"""
    try:
        from Scheduler import SetReminder
        
        # Format: "time:message" (e.g., "14:30:Take medicine")
        if ":" in command_arg:
            parts = command_arg.split(":", 1)
            if len(parts) >= 2:
                time_part = parts[0].strip()
                message_part = parts[1].strip()
                return SetReminder(time_part, message_part)
        return False
        
    except Exception as e:
        print(f"[Automation] Set reminder error: {e}")
        return False

async def ScheduleTaskControl(command_arg: str):
    """Schedule task control"""
    try:
        from Scheduler import ScheduleTask
        
        # Format: "time:task_description"
        if ":" in command_arg:
            parts = command_arg.split(":", 1)
            if len(parts) >= 2:
                time_part = parts[0].strip()
                task_description = parts[1].strip()
                
                def custom_task():
                    print(f"[Scheduler] Executing scheduled task: {task_description}")
                    return True
                
                return ScheduleTask(time_part, custom_task)
        return False
        
    except Exception as e:
        print(f"[Automation] Schedule task error: {e}")
        return False

# -----------------------------
# Command Dispatcher
# -----------------------------
async def TranslateAndExecute(commands: list[str]):
    tasks = []
    for cmd in commands:
        cmd_type, cmd_arg = "", ""
        cmd_lower = cmd.lower()
        
        # More robust parsing to handle various formats
        if ":" in cmd_lower:
            parts = cmd_lower.split(":", 1)
            cmd_type = parts[0].strip()
            cmd_arg = parts[1].strip()
        elif "(" in cmd and ")" in cmd:
            # Handle the format "command ( argument )"
            paren_start = cmd.find("(")
            paren_end = cmd.find(")")
            cmd_type = cmd[:paren_start].strip()
            cmd_arg = cmd[paren_start+1:paren_end].strip()
        else:
            cmd_type = cmd_lower
            cmd_arg = ""

        # Normalize command type by removing extra spaces and parentheses
        cmd_type = cmd_type.replace("(", "").replace(")", "").strip()
        
        print(f"[Automation] Processing command: '{cmd_type}' with argument: '{cmd_arg}'")

        # Map command types to their respective functions
        command_mapping = {
            "open": OpenApp,
            "close": CloseApp,
            "play": YoutubePlay,
            "content": Content,
            "google search": GoogleSearch,
            "youtube search": YoutubeSearch,
            "youtube play": YoutubePlay,
            "system": SystemControl,
            "generate image": GenerateImage,
            "image generation": GenerateImage,
            "wifi": WiFiControl,
            "bluetooth": BluetoothControl,
            "brightness": BrightnessControl,
            "volume": VolumeControl,
            "media": MediaControl,
            "whatsapp": WhatsAppControl,
            "message": SendMessageControl,
            "call": MakeCallControl,
            "reminder": SetReminderControl,
            "schedule": ScheduleTaskControl,
            "calendar": CalendarControl,
        }
        
        if cmd_type in command_mapping:
            tasks.append(command_mapping[cmd_type](cmd_arg))
        else:
            print(f"[Automation] Unknown command type: '{cmd_type}' with argument: '{cmd_arg}'")
            # Try to handle commands that might have been misparsed
            # For example, if the entire command is treated as cmd_type
            if any(keyword in cmd_type for keyword in ["open", "close", "play", "search", "youtube", "google", "system", "wifi", "bluetooth", "brightness", "volume", "media", "whatsapp", "message", "call", "reminder", "schedule", "generate image", "image generation"]):
                # Try to extract the command and argument
                for keyword in command_mapping.keys():
                    if keyword in cmd_type:
                        # Extract the argument part after the keyword
                        pos = cmd_type.find(keyword)
                        arg_part = cmd_type[pos + len(keyword):].strip()
                        tasks.append(command_mapping[keyword](arg_part))
                        break
            else:
                print(f"[Automation] Skipping unknown command: {cmd}")

    if tasks:
        print(f"[Automation] Executing {len(tasks)} task(s)...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful results
        success_count = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[Automation] Task {i+1} failed: {result}")
                import traceback
                traceback.print_exception(type(result), result, result.__traceback__)
            elif result:
                success_count += 1
                print(f"[Automation] Task {i+1} completed successfully")
            else:
                print(f"[Automation] Task {i+1} returned False (may have failed)")
        
        print(f"[Automation] {success_count}/{len(tasks)} tasks completed successfully")
        return success_count > 0
    else:
        print("[Automation] No valid tasks to execute")
        return False

# Wrapper for Main.py
async def Automation(DecisionList):
    if isinstance(DecisionList, str):
        DecisionList = [DecisionList]
    
    try:
        result = await TranslateAndExecute(DecisionList)
        print(f"[Automation] Function has finished execution. Success: {result}")
        
        if result:
            return "Commands executed successfully."
        else:
            return "Some commands failed to execute."
    except Exception as e:
        print(f"[Automation] Error in execution: {e}")
        return f"Error executing commands: {str(e)}"

# --- END OF FILE Automation.py ---