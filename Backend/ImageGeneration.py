# --- START OF FILE ImageGeneration.py ---

import os
import sys
import requests
import json
from PIL import Image
from io import BytesIO
from dotenv import dotenv_values
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import base64
import platform
import shutil
import subprocess

# Load environment variables
env_vars = dotenv_values(".env")
STABILITY_API_KEY = "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"  # New Stability AI API key
NVIDIA_API_KEY = env_vars.get("NVIDIA_API_KEY", "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")

# Absolute path to Data folder
data_folder = os.path.join(os.path.dirname(__file__), "..", "Data")
file_path = os.path.join(data_folder, "ImageGeneration.data")


def sanitize_filename(name):
    """Sanitize filename by removing invalid characters"""
    # Remove quotes and other problematic characters
    sanitized = name.replace('"', '').replace("'", '').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    # Limit length to avoid filename too long errors
    return sanitized[:100]


if __name__ == "__main__":
    # When called as subprocess, prioritize reading from the data file
    # This ensures compatibility with voice command flow
    if os.path.exists(file_path):
        # Read from ImageGeneration.data file (as used by voice commands)
        with open(file_path, "r", encoding="utf-8") as f:
            line = f.read().strip()

        if line:
            prompt = line.split(",")[0].strip().strip('"\'')  # Remove quotes and whitespace
        else:
            print("[ImageGeneration] ImageGeneration.data is empty.")
            sys.exit(1)
    elif len(sys.argv) > 1:
        # Use command line argument as prompt (for direct command line usage)
        prompt = " ".join(sys.argv[1:])
    else:
        # Get prompt from user input (for interactive mode)
        prompt = input("Enter image prompt: ").strip()
    
    if not prompt:
        print("[ImageGeneration] No prompt provided.")
        sys.exit(1)
else:
    # Module mode: read from file as before
    if not os.path.exists(file_path):
        print("[ImageGeneration] No ImageGeneration.data file found.")
        sys.exit(1)

    # Read prompt
    with open(file_path, "r", encoding="utf-8") as f:
        line = f.read().strip()

    if not line:
        print("[ImageGeneration] ImageGeneration.data is empty.")
        sys.exit(1)

    prompt = line.split(",")[0].strip().strip('"\'')  # Remove quotes and whitespace

# Try Stability AI API first (new preferred API)
STABILITY_API_ENABLED = True
STABILITY_API_URL = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"

# Fallback to NVIDIA API 
NVIDIA_API_ENABLED = True  # Enabled - using correct image generation endpoint
NVIDIA_API_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"  # Working image generation endpoint

# Final fallback to Pollinations API
POLLINATIONS_API_URL = "https://image.pollinations.ai/prompt/"

try:
    # Try Stability AI API first (new preferred API)
    if STABILITY_API_ENABLED and STABILITY_API_URL:
        try:
            print(f"[ImageGeneration] Generating image with Stability AI API using prompt: {filtered_prompt}")
            
            headers = {
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Use the exact payload structure from your example
            payload = {
                "prompt": filtered_prompt,
                "cfg_scale": 5,
                "aspect_ratio": "16:9",
                "seed": 0,
                "steps": 50,
                "negative_prompt": ""
            }
            
            print(f"[ImageGeneration] Stability API Payload: {payload}")
            
            # Generate 3 different images by varying the seed using concurrent requests
            seeds = [0, 12345, 24690]  # Three different seeds
            payloads = []
            
            for i in range(3):
                payload_copy = payload.copy()
                payload_copy["seed"] = seeds[i]
                payloads.append((i, payload_copy))
            
            # Use ThreadPoolExecutor to make requests concurrently
            max_workers = min(3, len(payloads))  # Don't exceed number of payloads
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(requests.post, STABILITY_API_URL, json=payload, headers=headers, timeout=45): idx 
                    for idx, payload in payloads
                }
                
                # Process completed tasks
                results = {}
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        response = future.result()
                        print(f"[ImageGeneration] Stability API Response {idx+1} Status: {response.status_code}")
                        if response.status_code == 200:
                            results[idx] = response.json()
                        else:
                            print(f"[ImageGeneration] Stability API Error {idx+1}: {response.status_code} - {response.text}")
                            results[idx] = None
                    except Exception as e:
                        print(f"[ImageGeneration] Error with Stability API request {idx+1}: {e}")
                        results[idx] = None
            
            # Process results and save images
            saved_images = []  # Track saved images to display later
            success_count = 0
            
            for i in range(3):
                if i in results and results[i]:
                    result = results[i]
                    if 'artifacts' in result and len(result['artifacts']) > 0:
                        artifact = result['artifacts'][0]
                        if 'base64' in artifact:
                            # Decode base64 image
                            image_bytes = base64.b64decode(artifact['base64'])
                            img = Image.open(BytesIO(image_bytes))
                            
                            # Save the image first
                            temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{i+1}.jpg")
                            img.save(temp_file)
                            print(f"[ImageGeneration] Image {i+1} saved as {temp_file}")
                            
                            # Store the image to display later
                            saved_images.append(img)
                            success_count += 1
                        else:
                            print(f"[ImageGeneration] Unexpected response format for image {i+1}: {result}")
                    else:
                        print(f"[ImageGeneration] No image data in response for image {i+1}: {result}")
            
            if success_count > 0:
                # Display all images after saving (non-blocking)
                time.sleep(1)  # Wait for files to be written
                
                for idx in range(len(saved_images)):
                    temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{idx+1}.jpg")
                    
                    try:
                        # For Windows, try to launch 360 Extreme Browser with the image file
                        browser_paths = [
                            r"C:\Program Files\360\360 Extreme Browser\360se.exe",
                            r"C:\Program Files (x86)\360\360 Extreme Browser\360se.exe",
                            r"C:\Program Files\360Chrome\Chrome\Application\360se.exe",
                            r"C:\Program Files (x86)\360Chrome\Chrome\Application\360se.exe"
                        ]
                        
                        browser_exe = None
                        for path in browser_paths:
                            if os.path.exists(path):
                                browser_exe = path
                                break
                        
                        if browser_exe:
                            # Launch a separate instance of 360 Extreme Browser for each image
                            subprocess.Popen([browser_exe, temp_file])
                        else:
                            # If 360 Extreme Browser executable is not found, use the system default
                            os.startfile(temp_file)
                        
                        # Add delay between opening browser instances
                        if idx < len(saved_images) - 1:  # Don't delay after the last image
                            time.sleep(2)  # Longer delay to allow browser to start
                    except Exception as e:
                        print(f"[ImageGeneration] Could not open image {idx+1} in 360 Extreme Browser: {e}")
                        try:
                            # Fallback to system default
                            os.startfile(temp_file)
                        except Exception as fallback_error:
                            print(f"[ImageGeneration] Fallback also failed: {fallback_error}")
                            # Final fallback to PIL show
                            try:
                                saved_images[idx].show()
                            except Exception as pil_error:
                                print(f"[ImageGeneration] PIL show also failed: {pil_error}")
                
                print(f"[ImageGeneration] Generated {success_count} images using Stability AI API")
                sys.exit(0)  # Success, exit early
            else:
                print("[ImageGeneration] No images generated from Stability AI API")
                
        except requests.exceptions.RequestException as stability_error:
            print(f"[ImageGeneration] Stability AI API request failed: {stability_error}")
        except Exception as stability_error:
            print(f"[ImageGeneration] Stability AI API error: {stability_error}")
    
    # Fallback to NVIDIA API if Stability API fails
    if NVIDIA_API_ENABLED and NVIDIA_API_URL:
        try:
            # NVIDIA API request payload
            # Handle content filtering by using general descriptions for specific people
            filtered_prompt = prompt
            content_filtered_names = ["elon musk", "tony stark", "iron man", "hulk", "spider-man", "superman", "batman"]
            
            for name in content_filtered_names:
                if name in prompt.lower():
                    filtered_prompt = "professional businessman portrait" if "elon" in name or "tony" in name else "superhero character"
                    print(f"[ImageGeneration] Content filter detected '{name}', using general prompt: '{filtered_prompt}'")
                    break
            
            # Generate 3 different images by varying the seed using concurrent requests
            seeds = [0, 12345, 24690]  # Three different seeds
            payloads = []
            
            for i in range(3):
                payload = {
                    "prompt": filtered_prompt,
                    "mode": "base",
                    "cfg_scale": 3.5,
                    "width": 1024,
                    "height": 1024,
                    "seed": seeds[i],
                    "steps": 50
                }
                payloads.append((i, payload))
            
            headers = {
                "Authorization": f"Bearer {NVIDIA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Use ThreadPoolExecutor to make requests concurrently
            max_workers = min(3, len(payloads))  # Don't exceed number of payloads
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(requests.post, NVIDIA_API_URL, json=payload, headers=headers, timeout=45): idx 
                    for idx, payload in payloads
                }
                
                # Process completed tasks
                results = {}
                for future in as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        response = future.result()
                        response.raise_for_status()
                        results[idx] = response.json()
                    except Exception as e:
                        print(f"[ImageGeneration] Error generating image {idx+1}: {e}")
                        results[idx] = None
            
            # Process results and save images
            saved_images = []  # Track saved images to display later
            for i in range(3):
                if i in results and results[i]:
                    result = results[i]
                    if 'artifacts' in result and len(result['artifacts']) > 0:
                        artifact = result['artifacts'][0]
                        finish_reason = artifact.get('finishReason', '')
                        
                        # Check if content was filtered
                        if finish_reason == 'CONTENT_FILTERED':
                            print(f"[ImageGeneration] Content filtered for prompt: {filtered_prompt}")
                            # Continue to fallback methods
                            break
                        elif 'base64' in artifact:
                            # Decode base64 image
                            image_bytes = base64.b64decode(artifact['base64'])
                            img = Image.open(BytesIO(image_bytes))
                            
                            # Save the image first
                            temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{i+1}.jpg")
                            img.save(temp_file)
                            print(f"[ImageGeneration] Image {i+1} saved as {temp_file}")
                            
                            # Store the image to display later
                            saved_images.append(img)
                        else:
                            print(f"[ImageGeneration] Unexpected response format for image {i+1}: {result}")
                    else:
                        print(f"[ImageGeneration] No image data in response for image {i+1}: {result}")
            
            # Display all images after saving (non-blocking)
            
            # Wait a moment for all images to be saved before attempting to open them
            time.sleep(1)
            
            for idx in range(len(saved_images)):
                temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{idx+1}.jpg")
                
                try:
                    # For Windows, try to launch 360 Extreme Browser with the image file
                    # First, we'll try to find the 360 Extreme Browser executable
                    
                    # Common installation paths for 360 Extreme Browser on Windows
                    browser_paths = [
                        r"C:\Program Files\360\360 Extreme Browser\360se.exe",
                        r"C:\Program Files (x86)\360\360 Extreme Browser\360se.exe",
                        r"C:\Program Files\360Chrome\Chrome\Application\360se.exe",
                        r"C:\Program Files (x86)\360Chrome\Chrome\Application\360se.exe"
                    ]
                    
                    browser_exe = None
                    for path in browser_paths:
                        if os.path.exists(path):
                            browser_exe = path
                            break
                    
                    if browser_exe:
                        # Launch a separate instance of 360 Extreme Browser for each image
                        subprocess.Popen([browser_exe, temp_file])
                    else:
                        # If 360 Extreme Browser executable is not found, use the system default
                        os.startfile(temp_file)
                    
                    # Add delay between opening browser instances
                    if idx < len(saved_images) - 1:  # Don't delay after the last image
                        time.sleep(2)  # Longer delay to allow browser to start
                except Exception as e:
                    print(f"[ImageGeneration] Could not open image {idx+1} in 360 Extreme Browser: {e}")
                    try:
                        # Fallback to system default
                        os.startfile(temp_file)
                    except Exception as fallback_error:
                        print(f"[ImageGeneration] Fallback also failed: {fallback_error}")
                        # Final fallback to PIL show
                        try:
                            saved_images[idx].show()
                        except Exception as pil_error:
                            print(f"[ImageGeneration] PIL show also failed: {pil_error}")
            
            print("[ImageGeneration] Generated using NVIDIA API")
            sys.exit(0)  # Success, exit early
        except requests.exceptions.RequestException as nvidia_error:
            print(f"[ImageGeneration] NVIDIA API request failed: {nvidia_error}")
        except Exception as nvidia_error:
            print(f"[ImageGeneration] NVIDIA API error: {nvidia_error}")
    
    # Fallback to Pollinations API
    print(f"[ImageGeneration] Generating image with Pollinations API using prompt: {prompt}")
    # For Pollinations, we'll try to generate 3 different images by slightly varying the prompt
    for i in range(3):
        modified_prompt = f"{prompt} style_{i+1}"  # Add variation to get different results
        url = f"{POLLINATIONS_API_URL}{modified_prompt.replace(' ', '%20')}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        if 'image' in response.headers.get('Content-Type', '').lower():
            img = Image.open(BytesIO(response.content))
            img.show()
            temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{i+1}.jpg")
            img.save(temp_file)
            print(f"[ImageGeneration] Image {i+1} saved as {temp_file}")
        else:
            print(f"[ImageGeneration] Non-image response: {response.text[:500]}")
    
    print("[ImageGeneration] Generated using Pollinations API (fallback)")
except Exception as e:
    print(f"[ImageGeneration] Failed to generate image: {e}")
    print("[ImageGeneration] Creating placeholder image...")
    
    # Create a simple placeholder image
    try:
        # Create 3 different colored placeholder images
        colors = [(73, 109, 137), (137, 109, 73), (109, 73, 137)]  # Different colors for variety
        for i in range(3):
            # Create a simple colored image as placeholder
            img = Image.new('RGB', (512, 512), color=colors[i])
            temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_{i+1}_placeholder.jpg")
            img.save(temp_file)
            img.show()
            print(f"[ImageGeneration] Placeholder image {i+1} saved as {temp_file}")
        print("[ImageGeneration] Note: External APIs are currently unavailable")
    except Exception as placeholder_error:
        print(f"[ImageGeneration] Failed to create placeholder: {placeholder_error}")
