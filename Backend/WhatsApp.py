# --- START OF FILE Backend/WhatsApp.py ---

import pywhatkit
from rich import print

async def SendWhatsAppMessage(number: str, message: str):
    """Sends a WhatsApp message to the specified number."""
    try:
        print(f"[WhatsApp] Attempting to send message to {number}: {message}")
        pywhatkit.sendwhatmsg_instantly(number, message, wait_time=15, tab_close=True)
        print(f"[WhatsApp] Message sent successfully to {number}.")
        return True
    except Exception as e:
        print(f"[WhatsApp] Error sending message: {e}")
        return False