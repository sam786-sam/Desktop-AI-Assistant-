# --- START OF FILE Backend/SnapCommands.py ---

import json
import os
import glob
from rich import print

# Path for the snap commands configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "Data")
SNAP_CONFIG_PATH = os.path.join(DATA_DIR, "snap_commands.json")
CURRENT_IMAGE_INDEX = 0

def get_snap_commands():
    """Loads snap commands from a JSON file."""
    if not os.path.exists(SNAP_CONFIG_PATH):
        sample_config = {
            "play next songs": [
                "youtube search: next song for me",
                "play: next song for me"
            ],
            "morning routine": [
                "wifi: on",
                "open: spotify",
                "open: google chrome"
            ]
        }
        with open(SNAP_CONFIG_PATH, 'w') as f:
            json.dump(sample_config, f, indent=4)
        return sample_config
    
    with open(SNAP_CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_image_files():
    """Get all image files from the Data directory"""
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(DATA_DIR, ext)))
    return sorted(image_files)

def navigate_images(direction: str):
    """Navigate through images in the Data folder"""
    global CURRENT_IMAGE_INDEX
    image_files = get_image_files()
    
    if not image_files:
        return None
    
    if direction.lower() in ['next', 'forward']:
        CURRENT_IMAGE_INDEX = (CURRENT_IMAGE_INDEX + 1) % len(image_files)
    elif direction.lower() in ['previous', 'prev', 'back']:
        CURRENT_IMAGE_INDEX = (CURRENT_IMAGE_INDEX - 1) % len(image_files)
    elif direction.lower() in ['first', 'start']:
        CURRENT_IMAGE_INDEX = 0
    elif direction.lower() in ['last', 'end']:
        CURRENT_IMAGE_INDEX = len(image_files) - 1
    
    current_image = image_files[CURRENT_IMAGE_INDEX]
    return current_image

async def handle_image_navigation(command_name: str):
    """Handle image navigation commands"""
    if "next image" in command_name.lower():
        current_image = navigate_images('next')
        if current_image:
            return [f"open: {current_image}"]
    elif "previous image" in command_name.lower():
        current_image = navigate_images('previous')
        if current_image:
            return [f"open: {current_image}"]
    elif "first image" in command_name.lower():
        current_image = navigate_images('first')
        if current_image:
            return [f"open: {current_image}"]
    elif "last image" in command_name.lower():
        current_image = navigate_images('last')
        if current_image:
            return [f"open: {current_image}"]
    return None

async def ExecuteSnapCommand(command_name: str, handle_multiple_commands_func):
    """
    Executes a predefined sequence of commands based on a snap command name.
    """
    # First check for image navigation commands
    image_commands = await handle_image_navigation(command_name)
    if image_commands:
        print(f"[SnapCommands] Executing image navigation: {image_commands}")
        await handle_multiple_commands_func(image_commands)
        return True
    
    # Then check for predefined snap commands
    snap_commands = get_snap_commands()
    
    matched_commands = None
    for key in snap_commands:
        if key.lower() in command_name.lower() or command_name.lower() in key.lower():
            matched_commands = snap_commands[key]
            break

    if matched_commands:
        print(f"[SnapCommands] Executing snap command '{command_name}': {matched_commands}")
        await handle_multiple_commands_func(matched_commands)
        return True
    else:
        print(f"[SnapCommands] No snap command found for '{command_name}'.")
        return False