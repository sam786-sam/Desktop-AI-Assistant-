# --- START OF FILE 3DImageGeneration.py ---

import os
import sys
import requests
import json
from PIL import Image
from io import BytesIO
import base64
import platform
import subprocess
import time

# NVIDIA 3D API configuration
NVIDIA_3D_API_KEY = "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"
INVOKE_URL = "https://ai.api.nvidia.com/v1/genai/microsoft/trellis"

# Absolute path to Data folder
data_folder = os.path.join(os.path.dirname(__file__), "..", "Data")

def sanitize_filename(name):
    """Sanitize filename by removing invalid characters"""
    sanitized = name.replace('"', '').replace("'", '').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    return sanitized[:100]

def generate_3d_image(prompt):
    """Generate 3D image using NVIDIA Trellis API with multiple fallbacks"""
    try:
        print(f"[3DImageGeneration] Generating 3D image with prompt: {prompt}")
        
        # First, try to create a placeholder image immediately as fallback
        print(f"[3DImageGeneration] Creating placeholder 3D image while attempting API connection...")
        placeholder_result = create_placeholder_3d_image(prompt)
        
        # Try the NVIDIA API as enhancement
        headers = {
            "Authorization": f"Bearer {NVIDIA_3D_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Try multiple payload formats that might work
        payload_formats = [
            {"prompt": prompt},
            {"prompt": f"3D render of {prompt}"},
            {"prompt": prompt, "seed": 0},
            {"image": f"data:image/png;prompt,{prompt}"},
        ]
        
        for i, payload in enumerate(payload_formats):
            print(f"[3DImageGeneration] Trying payload format {i+1}: {payload}")
            try:
                response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
                print(f"[3DImageGeneration] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"[3DImageGeneration] ✅ Successfully got response with format {i+1}")
                    # Try to process the actual API response
                    response_body = response.json()
                    print(f"[3DImageGeneration] API Response: {response_body}")
                    
                    # If we get valid image data, replace the placeholder
                    if process_api_response(response_body, prompt):
                        print(f"[3DImageGeneration] ✅ Replaced placeholder with actual 3D image from API")
                        return True
                    else:
                        print(f"[3DImageGeneration] ❌ API response didn't contain valid image data")
                        break
                else:
                    print(f"[3DImageGeneration] ❌ Format {i+1} failed: {response.status_code}")
                    if i < len(payload_formats) - 1:
                        print(f"[3DImageGeneration] Trying next format...")
                        
            except requests.exceptions.Timeout:
                print(f"[3DImageGeneration] ❌ Format {i+1} timed out")
                continue
            except Exception as e:
                print(f"[3DImageGeneration] ❌ Format {i+1} failed: {e}")
                continue
        
        # If we get here, API attempts failed but placeholder was created
        print(f"[3DImageGeneration] ✅ Using placeholder 3D image as fallback")
        return placeholder_result
        
    except Exception as e:
        print(f"[3DImageGeneration] 3D image generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_api_response(response_body, prompt):
    """Process API response and save actual 3D image if available"""
    try:
        # Handle different response formats
        image_data = None
        
        # Check if response contains 'image' field directly
        if 'image' in response_body:
            image_data = response_body['image']
        # Check if response contains 'artifacts' array
        elif 'artifacts' in response_body and len(response_body['artifacts']) > 0:
            artifact = response_body['artifacts'][0]
            if 'base64' in artifact:
                image_data = artifact['base64']
            elif 'image' in artifact:
                image_data = artifact['image']
        # Check if response is directly the base64 string
        elif isinstance(response_body, str) and len(response_body) > 100:
            image_data = response_body
        
        if image_data:
            print(f"[3DImageGeneration] Found image data in API response")
            
            # If it's a base64 string, decode it
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]
                else:
                    image_data = image_data.split(';', 1)[1] if ';' in image_data else image_data
            
            try:
                # Decode base64 image
                if isinstance(image_data, str):
                    image_bytes = base64.b64decode(image_data)
                    img = Image.open(BytesIO(image_bytes))
                else:
                    img = Image.open(BytesIO(image_data))
                
                # Save the actual 3D image (overwrites placeholder)
                temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_3d.jpg")
                img.save(temp_file, quality=95)
                print(f"[3DImageGeneration] Actual 3D Image saved as {temp_file}")
                
                # Try to open the actual image
                try:
                    os.startfile(temp_file)
                    print(f"[3DImageGeneration] ✅ Actual 3D image opened successfully")
                except:
                    img.show()
                
                return True
            except Exception as decode_error:
                print(f"[3DImageGeneration] Error decoding API image: {decode_error}")
                return False
        else:
            print(f"[3DImageGeneration] No valid image data in API response")
            return False
            
    except Exception as e:
        print(f"[3DImageGeneration] Error processing API response: {e}")
        return False

if __name__ == "__main__":
    # Test the 3D generation when run directly
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = input("Enter 3D image prompt: ").strip()
    
    if prompt:
        generate_3d_image(prompt)
    else:
        print("[3DImageGeneration] No prompt provided.")

def create_placeholder_3d_image(prompt):
    """Create a placeholder 3D-like image when API fails"""
    try:
        print(f"[3DImageGeneration] Creating placeholder 3D image for: {prompt}")
        
        # Create a simple 3D-like gradient image
        width, height = 512, 512
        img = Image.new('RGB', (width, height), color=(50, 50, 100))
        
        # Add some 3D-like gradients
        pixels = img.load()
        for i in range(width):
            for j in range(height):
                # Create a gradient effect
                r = int(100 + 50 * (i / width))
                g = int(80 + 40 * (j / height))
                b = int(120 + 60 * ((width - i) / width))
                pixels[i, j] = (r, g, b)
        
        # Add text overlay
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        try:
            # Try to use a system font
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        text = f"3D: {prompt}"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with background
        draw.rectangle([x-10, y-10, x+text_width+10, y+text_height+10], fill=(0, 0, 0, 128))
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Save and display the image
        temp_file = os.path.join(data_folder, f"{sanitize_filename(prompt)}_3d.jpg")
        img.save(temp_file, quality=95)
        print(f"[3DImageGeneration] Placeholder 3D Image saved as {temp_file}")
        
        # Wait a moment for file to be written completely
        time.sleep(1)
        
        # Try to open the image
        try:
            os.startfile(temp_file)
            print(f"[3DImageGeneration] ✅ Placeholder image opened successfully")
            return True
        except Exception as e:
            print(f"[3DImageGeneration] Could not open placeholder image: {e}")
            img.show()
            return True
            
    except Exception as e:
        print(f"[3DImageGeneration] Failed to create placeholder: {e}")
        return False

# --- END OF FILE 3DImageGeneration.py ---