"""
Basic SnapCommands implementation without cv2 dependency
For immediate compatibility while cv2 is being installed
"""

import os
import random
import json
import ctypes
from pathlib import Path
import sys
from rich import print

# Current directory and data paths
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(current_dir, "Data")
images_dir = os.path.join(data_dir, "Images")
snap_commands_file = os.path.join(data_dir, "snap_commands.json")

# Ensure directories exist
os.makedirs(images_dir, exist_ok=True)

def get_wallpaper_style_constant(style):
    """Get Windows wallpaper style constants"""
    styles = {
        'fill': 10,
        'fit': 6, 
        'stretch': 2,
        'tile': 0,
        'center': 0,
        'span': 22
    }
    return styles.get(style, 10)

def change_wallpaper(image_path, style='fill'):
    """Change Windows wallpaper using basic method"""
    try:
        if not os.path.exists(image_path):
            print(f"[SnapCommands] ❌ Image not found: {image_path}")
            return False
        
        # Convert to absolute path
        abs_path = os.path.abspath(image_path)
        
        # Set wallpaper using Windows API
        SPI_SETDESKWALLPAPER = 20
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            abs_path,
            3  # SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        if result:
            print(f"[SnapCommands] ✅ Wallpaper changed to: {os.path.basename(image_path)}")
            return True
        else:
            print(f"[SnapCommands] ❌ Failed to change wallpaper")
            return False
            
    except Exception as e:
        print(f"[SnapCommands] ❌ Error changing wallpaper: {e}")
        return False

class BasicSnapImageController:
    """Basic image navigation without cv2 dependency"""
    
    def __init__(self):
        self.images_dir = images_dir
        self.current_index = 0
        self.image_files = []
        self.image_collections = {
            "all": [],
            "heroes": [],
            "cars": [], 
            "actors": [],
            "landscapes": [],
            "abstract": []
        }
        self.scan_images()
    
    def scan_images(self):
        """Scan for image files"""
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
        
        try:
            if os.path.exists(self.images_dir):
                for file in os.listdir(self.images_dir):
                    if any(file.lower().endswith(fmt) for fmt in supported_formats):
                        full_path = os.path.join(self.images_dir, file)
                        self.image_files.append(full_path)
                        
                        # Categorize by filename keywords
                        file_lower = file.lower()
                        if any(keyword in file_lower for keyword in ['hero', 'super', 'batman', 'spider', 'iron']):
                            self.image_collections["heroes"].append(full_path)
                        elif any(keyword in file_lower for keyword in ['car', 'auto', 'vehicle', 'bmw', 'ferrari']):
                            self.image_collections["cars"].append(full_path)
                        elif any(keyword in file_lower for keyword in ['actor', 'celebrity', 'star']):
                            self.image_collections["actors"].append(full_path)
                        elif any(keyword in file_lower for keyword in ['landscape', 'mountain', 'beach', 'nature']):
                            self.image_collections["landscapes"].append(full_path)
                        elif any(keyword in file_lower for keyword in ['abstract', 'pattern', 'geometric']):
                            self.image_collections["abstract"].append(full_path)
                        
                        # Add to all collection
                        self.image_collections["all"].append(full_path)
            
            print(f"[SnapCommands] 📸 Found {len(self.image_files)} images")
            for category, images in self.image_collections.items():
                if images:
                    print(f"[SnapCommands]   {category}: {len(images)} images")
        
        except Exception as e:
            print(f"[SnapCommands] ❌ Error scanning images: {e}")
    
    def navigate_images(self, direction, category="all"):
        """Navigate through images"""
        collection = self.image_collections.get(category, self.image_collections["all"])
        
        if not collection:
            print(f"[SnapCommands] ❌ No images found in category: {category}")
            return None
        
        if direction == 'next':
            self.current_index = (self.current_index + 1) % len(collection)
        elif direction == 'previous':
            self.current_index = (self.current_index - 1) % len(collection)
        elif direction == 'random':
            self.current_index = random.randint(0, len(collection) - 1)
        
        current_image = collection[self.current_index]
        print(f"[SnapCommands] 🖼️ {direction.title()} {category} image: {os.path.basename(current_image)}")
        return current_image
    
    def get_current_image(self, category="all"):
        """Get current image from category"""
        collection = self.image_collections.get(category, self.image_collections["all"])
        if collection and self.current_index < len(collection):
            return collection[self.current_index]
        return None

# Global image controller
image_controller = BasicSnapImageController()

def load_custom_commands():
    """Load custom snap commands from JSON file"""
    try:
        if os.path.exists(snap_commands_file):
            with open(snap_commands_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Create default commands
            default_commands = {
                "morning routine": [
                    "wifi: on",
                    "open: chrome",
                    "volume: 50",
                    "brightness: 80"
                ],
                "gaming setup": [
                    "close: chrome",
                    "volume: 100",
                    "brightness: 100",
                    "open: steam"
                ],
                "work mode": [
                    "volume: 30",
                    "brightness: 60", 
                    "open: notepad",
                    "open: calculator"
                ]
            }
            
            os.makedirs(os.path.dirname(snap_commands_file), exist_ok=True)
            with open(snap_commands_file, 'w', encoding='utf-8') as f:
                json.dump(default_commands, f, indent=4)
            
            return default_commands
    except Exception as e:
        print(f"[SnapCommands] ❌ Error loading custom commands: {e}")
        return {}

def save_custom_commands(commands):
    """Save custom commands to JSON file"""
    try:
        with open(snap_commands_file, 'w', encoding='utf-8') as f:
            json.dump(commands, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SnapCommands] ❌ Error saving commands: {e}")
        return False

async def ExecuteSnapCommand(command, fallback_handler=None):
    """Execute snap commands with basic functionality"""
    global image_controller
    
    try:
        command = command.lower().strip()
        print(f"[SnapCommands] 🎯 Processing: '{command}'")
        
        # Image navigation commands
        if "next" in command and "image" in command:
            category = "all"
            for cat in image_controller.image_collections.keys():
                if cat in command:
                    category = cat
                    break
            
            image_path = image_controller.navigate_images('next', category)
            if image_path:
                return f"Showing next {category} image: {os.path.basename(image_path)}"
        
        elif "previous" in command and "image" in command:
            category = "all"
            for cat in image_controller.image_collections.keys():
                if cat in command:
                    category = cat
                    break
            
            image_path = image_controller.navigate_images('previous', category)
            if image_path:
                return f"Showing previous {category} image: {os.path.basename(image_path)}"
        
        elif "random" in command and "image" in command:
            category = "all"
            for cat in image_controller.image_collections.keys():
                if cat in command:
                    category = cat
                    break
            
            image_path = image_controller.navigate_images('random', category)
            if image_path:
                return f"Showing random {category} image: {os.path.basename(image_path)}"
        
        # Wallpaper commands
        elif "change wallpaper" in command or "wallpaper" in command:
            current_image = image_controller.get_current_image()
            if current_image:
                if change_wallpaper(current_image):
                    return f"Changed wallpaper to: {os.path.basename(current_image)}"
                else:
                    return "Failed to change wallpaper"
            else:
                return "No image available for wallpaper"
        
        # Custom command execution
        else:
            custom_commands = load_custom_commands()
            if command in custom_commands:
                commands_to_execute = custom_commands[command]
                print(f"[SnapCommands] 🚀 Executing custom command: {command}")
                
                if fallback_handler:
                    result = await fallback_handler(commands_to_execute)
                    return f"Executed {command}: {len(commands_to_execute)} actions"
                else:
                    print(f"[SnapCommands] Commands to execute: {commands_to_execute}")
                    return f"Custom command '{command}' ready (no handler provided)"
        
        return False
        
    except Exception as e:
        print(f"[SnapCommands] ❌ Error executing snap command: {e}")
        return False

def list_available_commands():
    """List all available snap commands"""
    commands = []
    
    # Image navigation commands
    categories = list(image_controller.image_collections.keys())
    for category in categories:
        if image_controller.image_collections[category]:  # Only if category has images
            commands.extend([
                f"next {category} image",
                f"previous {category} image", 
                f"random {category} image"
            ])
    
    # Wallpaper commands
    commands.extend([
        "change wallpaper",
        "set wallpaper"
    ])
    
    # Custom commands
    custom_commands = load_custom_commands()
    commands.extend(custom_commands.keys())
    
    return commands

def create_sample_images_info():
    """Create info file about expected image organization"""
    info_file = os.path.join(images_dir, "README.txt")
    
    info_content = """
Image Organization Guide
========================

Place your images in this Data/Images/ folder for SnapCommands to work.

Supported formats: JPG, PNG, BMP, GIF, WebP

Image Categories (auto-detected by filename):
- Heroes: Files with 'hero', 'super', 'batman', 'spider', 'iron' in name
- Cars: Files with 'car', 'auto', 'vehicle', 'bmw', 'ferrari' in name  
- Actors: Files with 'actor', 'celebrity', 'star' in name
- Landscapes: Files with 'landscape', 'mountain', 'beach', 'nature' in name
- Abstract: Files with 'abstract', 'pattern', 'geometric' in name

Voice Commands:
- "next hero image" - Show next hero image
- "random car image" - Show random car image
- "change wallpaper" - Set current image as wallpaper
- "morning routine" - Execute custom command sequence

Add your images here and use voice commands to navigate!
"""
    
    try:
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(info_content)
        print(f"[SnapCommands] ℹ️ Created image guide: {info_file}")
    except Exception as e:
        print(f"[SnapCommands] Warning: Could not create guide file: {e}")

# Initialize
if __name__ == "__main__":
    print("[SnapCommands] 🚀 Basic SnapCommands System")
    print("=" * 50)
    
    # Create sample info
    create_sample_images_info()
    
    # Test functionality
    print(f"\n📸 Available Commands:")
    commands = list_available_commands()
    for cmd in commands[:10]:  # Show first 10
        print(f"  • {cmd}")
    
    if len(commands) > 10:
        print(f"  ... and {len(commands) - 10} more")
    
    print(f"\n📁 Image Statistics:")
    for category, images in image_controller.image_collections.items():
        print(f"  {category}: {len(images)} images")