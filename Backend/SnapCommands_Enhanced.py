# --- ENHANCED SnapCommands.py ---

import json
import os
import glob
import random
import subprocess
import shutil
from rich import print
from pathlib import Path
import time
import cv2
from PIL import Image

# Path for the snap commands configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
SNAP_CONFIG_PATH = os.path.join(DATA_DIR, "snap_commands.json")
CURRENT_IMAGE_INDEX = 0
WALLPAPER_HISTORY = []

class SnapImageController:
    """Enhanced image control for snap commands"""
    
    def __init__(self):
        self.current_index = 0
        self.image_collections = self.organize_images_by_category()
        
    def organize_images_by_category(self):
        """Organize images by category/theme"""
        image_files = self.get_all_image_files()
        collections = {
            "all": image_files,
            "heroes": [f for f in image_files if any(hero in f.lower() for hero in ['iron', 'hulk', 'spider', 'ant', 'superman'])],
            "actors": [f for f in image_files if any(actor in f.lower() for actor in ['prabhas', 'hrithik', 'allu', 'tony', 'stark'])],
            "cars": [f for f in image_files if any(car in f.lower() for car in ['bmw', 'car', 'thar'])],
            "landscapes": [f for f in image_files if any(landscape in f.lower() for landscape in ['sunset', 'landscape', 'beautiful'])],
            "generated": [f for f in image_files if 'freepik' in f.lower() or 'pollinations' in f.lower()]
        }
        return collections
    
    def get_all_image_files(self):
        """Get all image files from the Data directory"""
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(DATA_DIR, ext)))
        return sorted(image_files)
    
    def navigate_images(self, direction: str, category: str = "all"):
        """Navigate through images with category support"""
        image_files = self.image_collections.get(category, self.image_collections["all"])
        
        if not image_files:
            return None
        
        if direction.lower() in ['next', 'forward']:
            self.current_index = (self.current_index + 1) % len(image_files)
        elif direction.lower() in ['previous', 'prev', 'back']:
            self.current_index = (self.current_index - 1) % len(image_files)
        elif direction.lower() in ['first', 'start']:
            self.current_index = 0
        elif direction.lower() in ['last', 'end']:
            self.current_index = len(image_files) - 1
        elif direction.lower() in ['random', 'shuffle']:
            self.current_index = random.randint(0, len(image_files) - 1)
        
        current_image = image_files[self.current_index]
        return current_image
    
    def get_images_by_theme(self, theme: str):
        """Get images by specific theme/keyword"""
        all_images = self.get_all_image_files()
        themed_images = [img for img in all_images if theme.lower() in os.path.basename(img).lower()]
        return themed_images
    
    def set_as_wallpaper(self, image_path: str):
        """Set image as desktop wallpaper"""
        try:
            import ctypes
            # Convert to absolute path
            abs_path = os.path.abspath(image_path)
            
            # Set wallpaper using Windows API
            SPI_SETDESKWALLPAPER = 20
            result = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path, 3
            )
            
            if result:
                WALLPAPER_HISTORY.append(abs_path)
                print(f"[SnapCommands] ✅ Wallpaper set to: {os.path.basename(image_path)}")
                return True
            else:
                print("[SnapCommands] ❌ Failed to set wallpaper")
                return False
                
        except Exception as e:
            print(f"[SnapCommands] ❌ Wallpaper error: {e}")
            return False
    
    def create_image_slideshow(self, category: str = "all", interval: int = 30):
        """Create automatic image slideshow"""
        try:
            images = self.image_collections.get(category, self.image_collections["all"])
            if not images:
                return False
            
            print(f"[SnapCommands] 🎞️ Starting slideshow with {len(images)} images")
            
            for i, image in enumerate(images):
                self.set_as_wallpaper(image)
                print(f"[SnapCommands] Slideshow: {i+1}/{len(images)} - {os.path.basename(image)}")
                
                if i < len(images) - 1:  # Don't sleep after last image
                    time.sleep(interval)
                    
            return True
            
        except Exception as e:
            print(f"[SnapCommands] ❌ Slideshow error: {e}")
            return False

# Global image controller
image_controller = SnapImageController()

def get_snap_commands():
    """Loads and manages snap commands from JSON file"""
    if not os.path.exists(SNAP_CONFIG_PATH):
        enhanced_config = {
            "morning routine": [
                "wifi: on",
                "brightness: 80",
                "volume: 50",
                "open: spotify",
                "open: chrome"
            ],
            "work mode": [
                "wifi: on",
                "brightness: 90",
                "open: vscode",
                "open: chrome",
                "open: notion",
                "volume: 30"
            ],
            "entertainment mode": [
                "volume: 80",
                "brightness: 70",
                "open: spotify",
                "play: latest hits",
                "youtube search: trending music"
            ],
            "gaming setup": [
                "brightness: 100",
                "volume: 90",
                "close: unnecessary apps",
                "open: steam",
                "wifi: on"
            ],
            "next image": [],  # Handled by image controller
            "previous image": [],  # Handled by image controller
            "random image": [],  # Handled by image controller
            "hero images": [],  # Handled by image controller
            "car images": [],  # Handled by image controller
            "actor images": [],  # Handled by image controller
            "slideshow": [],  # Handled by image controller
            "wallpaper change": [],  # Handled by image controller
            "presentation mode": [
                "brightness: 100",
                "volume: 70",
                "wifi: on",
                "open: powerpoint",
                "close: notifications"
            ],
            "shutdown routine": [
                "close: all browsers",
                "close: spotify",
                "wifi: off",
                "bluetooth: off",
                "brightness: 10"
            ],
            "social media": [
                "open: chrome",
                "google search: latest news",
                "youtube search: trending videos"
            ],
            "study mode": [
                "brightness: 90",
                "volume: 20",
                "close: distracting apps",
                "open: focus apps",
                "wifi: on"
            ]
        }
        
        os.makedirs(os.path.dirname(SNAP_CONFIG_PATH), exist_ok=True)
        with open(SNAP_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(enhanced_config, f, indent=4)
        return enhanced_config
    
    with open(SNAP_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def add_custom_snap_command(command_name: str, command_list: list):
    """Add a new custom snap command"""
    try:
        snap_commands = get_snap_commands()
        snap_commands[command_name.lower()] = command_list
        
        with open(SNAP_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(snap_commands, f, indent=4)
        
        print(f"[SnapCommands] ✅ Added custom snap command: '{command_name}'")
        return True
        
    except Exception as e:
        print(f"[SnapCommands] ❌ Failed to add custom command: {e}")
        return False

async def handle_image_navigation(command_name: str):
    """Enhanced image navigation with more options"""
    global image_controller
    
    command_lower = command_name.lower()
    
    # Next/Previous with category support
    if "next" in command_lower:
        category = "all"
        if "hero" in command_lower:
            category = "heroes"
        elif "car" in command_lower:
            category = "cars"
        elif "actor" in command_lower:
            category = "actors"
        elif "landscape" in command_lower:
            category = "landscapes"
        
        current_image = image_controller.navigate_images('next', category)
        if current_image:
            return [f"open: {current_image}"]
    
    elif "previous" in command_lower or "prev" in command_lower:
        category = "all"
        if "hero" in command_lower:
            category = "heroes"
        elif "car" in command_lower:
            category = "cars"
        elif "actor" in command_lower:
            category = "actors"
            
        current_image = image_controller.navigate_images('previous', category)
        if current_image:
            return [f"open: {current_image}"]
    
    elif "random" in command_lower:
        category = "all"
        if "hero" in command_lower:
            category = "heroes"
        elif "car" in command_lower:
            category = "cars"
        elif "actor" in command_lower:
            category = "actors"
            
        current_image = image_controller.navigate_images('random', category)
        if current_image:
            return [f"open: {current_image}"]
    
    # Wallpaper commands
    elif "wallpaper" in command_lower:
        if "next" in command_lower:
            current_image = image_controller.navigate_images('next')
            if current_image:
                image_controller.set_as_wallpaper(current_image)
                return [f"system: Wallpaper changed to {os.path.basename(current_image)}"]
        elif "random" in command_lower:
            current_image = image_controller.navigate_images('random')
            if current_image:
                image_controller.set_as_wallpaper(current_image)
                return [f"system: Random wallpaper set to {os.path.basename(current_image)}"]
    
    # Slideshow commands
    elif "slideshow" in command_lower:
        category = "all"
        interval = 30  # default 30 seconds
        
        if "hero" in command_lower:
            category = "heroes"
        elif "car" in command_lower:
            category = "cars"
        elif "actor" in command_lower:
            category = "actors"
        elif "fast" in command_lower:
            interval = 10
        elif "slow" in command_lower:
            interval = 60
        
        # Start slideshow in background thread
        import threading
        slideshow_thread = threading.Thread(
            target=image_controller.create_image_slideshow,
            args=(category, interval),
            daemon=True
        )
        slideshow_thread.start()
        return [f"system: Slideshow started with {category} images"]
    
    # Category-specific image commands
    elif "hero images" in command_lower or "superhero" in command_lower:
        images = image_controller.image_collections.get("heroes", [])
        if images:
            random_hero = random.choice(images)
            return [f"open: {random_hero}"]
    
    elif "car images" in command_lower or "vehicle" in command_lower:
        images = image_controller.image_collections.get("cars", [])
        if images:
            random_car = random.choice(images)
            return [f"open: {random_car}"]
    
    elif "actor images" in command_lower:
        images = image_controller.image_collections.get("actors", [])
        if images:
            random_actor = random.choice(images)
            return [f"open: {random_actor}"]
    
    return None

async def handle_smart_commands(command_name: str):
    """Handle smart context-aware commands"""
    command_lower = command_name.lower()
    
    # Time-based smart commands
    current_hour = time.localtime().tm_hour
    
    if "smart routine" in command_lower:
        if 6 <= current_hour < 12:  # Morning
            return await ExecuteSnapCommand("morning routine", None)
        elif 12 <= current_hour < 17:  # Afternoon
            return await ExecuteSnapCommand("work mode", None)
        elif 17 <= current_hour < 22:  # Evening
            return await ExecuteSnapCommand("entertainment mode", None)
        else:  # Night
            return await ExecuteSnapCommand("shutdown routine", None)
    
    # Weather-based commands (placeholder - would need weather API)
    elif "weather routine" in command_lower:
        # Could integrate with weather API to change wallpaper based on weather
        return [f"system: Weather-based routine not yet implemented"]
    
    return None

async def ExecuteSnapCommand(command_name: str, handle_multiple_commands_func):
    """Enhanced snap command execution with smart features"""
    
    print(f"[SnapCommands] 🎯 Processing snap command: '{command_name}'")
    
    # First check for image navigation commands
    image_commands = await handle_image_navigation(command_name)
    if image_commands:
        print(f"[SnapCommands] 🖼️ Executing image command: {image_commands}")
        if handle_multiple_commands_func:
            await handle_multiple_commands_func(image_commands)
        return True
    
    # Check for smart commands
    smart_commands = await handle_smart_commands(command_name)
    if smart_commands:
        print(f"[SnapCommands] 🧠 Executing smart command")
        return smart_commands
    
    # Check for predefined snap commands
    snap_commands = get_snap_commands()
    
    matched_commands = None
    best_match = None
    max_matches = 0
    
    # Improved matching algorithm
    for key in snap_commands:
        # Direct match
        if key.lower() == command_name.lower():
            matched_commands = snap_commands[key]
            break
        
        # Partial match
        elif key.lower() in command_name.lower() or command_name.lower() in key.lower():
            matched_commands = snap_commands[key]
            break
        
        # Word-based matching for better accuracy
        key_words = key.lower().split()
        command_words = command_name.lower().split()
        common_words = len(set(key_words) & set(command_words))
        
        if common_words > max_matches and common_words > 0:
            max_matches = common_words
            best_match = key
    
    # Use best match if no direct match found
    if not matched_commands and best_match:
        matched_commands = snap_commands[best_match]
        print(f"[SnapCommands] 🎯 Best match found: '{best_match}' for '{command_name}'")

    if matched_commands:
        if not matched_commands:  # Empty command list (handled by special functions)
            print(f"[SnapCommands] ✅ Special command '{command_name}' processed")
            return True
        
        print(f"[SnapCommands] ⚡ Executing snap command '{command_name}': {matched_commands}")
        
        if handle_multiple_commands_func:
            await handle_multiple_commands_func(matched_commands)
        else:
            print(f"[SnapCommands] 📋 Commands to execute: {matched_commands}")
        
        return True
    else:
        print(f"[SnapCommands] ❌ No snap command found for '{command_name}'.")
        
        # Suggest similar commands
        all_commands = list(snap_commands.keys())
        suggestions = [cmd for cmd in all_commands if any(word in cmd.lower() for word in command_name.lower().split())]
        
        if suggestions:
            print(f"[SnapCommands] 💡 Did you mean: {', '.join(suggestions[:3])}")
        
        return False

def list_available_commands():
    """List all available snap commands"""
    snap_commands = get_snap_commands()
    
    print("\n[SnapCommands] 📋 Available Snap Commands:")
    print("=" * 50)
    
    for i, (command, actions) in enumerate(snap_commands.items(), 1):
        action_summary = f"{len(actions)} actions" if actions else "Special command"
        print(f"{i:2}. {command:<20} - {action_summary}")
    
    print("\n[SnapCommands] 🖼️ Image Commands:")
    print("- next image [category]    - Navigate to next image")
    print("- previous image [category]- Navigate to previous image") 
    print("- random image [category]  - Show random image")
    print("- wallpaper next/random    - Change wallpaper")
    print("- slideshow [category]     - Start image slideshow")
    print("\n[SnapCommands] Categories: all, heroes, cars, actors, landscapes")
    
    return snap_commands

# Usage examples and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_snap_commands():
        """Test the enhanced snap commands"""
        
        # Test image navigation
        print("Testing image navigation...")
        result = await handle_image_navigation("next hero image")
        print(f"Result: {result}")
        
        # Test custom command
        add_custom_snap_command("my routine", [
            "wifi: on",
            "open: chrome",
            "volume: 50"
        ])
        
        # List available commands
        list_available_commands()
    
    # Run test
    # asyncio.run(test_enhanced_snap_commands())
    print("[SnapCommands] 🚀 Enhanced SnapCommands module loaded successfully!")