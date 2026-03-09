import cohere
from rich import print
from dotenv import dotenv_values
import cohere.core.api_error

env_vars = dotenv_values(".env")

CohereAPIKey = env_vars.get("CohereAPIKey")

co = cohere.Client(api_key=CohereAPIKey)

funcs = [
    'exit', 'general', 'realtime', 'open', 'close', 'play',
    'generate image', 'system', 'content', 'google search',
    'youtube search', 'reminder', 'wifi', 'bluetooth',
    'brightness', 'volume', 'media', 'whatsapp', 'message', 'call',
    'calendar'
]

messages = []

preamble = """
You are a very accurate Decision-Making Model, which decides what kind of a query is given to you.
You will decide whether a query is a 'general' query, a 'realtime' query, or is asking to perform any task or automation like 'open facebook, instagram', 'can you write a application and open it in notepad'
*** Do not answer any query, just decide what kind of query is given to you. ***
-> Respond with 'general ( query )' if a query can be answered by a llm model (conversational ai chatbot) and doesn't require internet search and it is not a automation function given below.
-> Respond with 'realtime ( query )' if a query requires an internet search or up to date information like news, weather, or current events.
# The automation functions are: open, close, play, system, content, google search, youtube search, generate image, generate 3d image, wifi, bluetooth, brightness, volume, media
-> You should only respond with the exact function name from the list and the query in parenthesis. For example, if the user asks 'open chrome', you should respond with 'open ( chrome )'. If the user asks 'play despacito on youtube', you should respond with 'play ( despacito )'.
-> The output for a single user query can contain multiple function calls, separated by the delimiter </t>. For example: 'open ( chrome )</t>open ( facebook )'.
-> The output should contain all the tasks a user asked for.
"""

def FirstlayerDMM(prompt):
    global messages
    
    prompt_lower = prompt.lower().strip()
    
    # Check for real-time related queries first
    realtime_keywords = [
        'time', 'date', 'today', 'weather', 'news', 'latest', 'current', 
        'now', 'temperature', 'forecast', 'stock', 'price', 'updates',
        'what day', 'day is it', 'month', 'year', 'hour', 'minute', 'second'
    ]
    
    # Check for real-time keywords
    for keyword in realtime_keywords:
        if keyword in prompt_lower:
            return [f"realtime ( {prompt} )"]
    
    # Enhanced parsing for better command recognition
    for func in funcs:
        if func in prompt_lower:
            if func in ["general", "realtime"]:
                return [f"{func} ( {prompt} )"]
            else:
                # Extract the action and target
                remaining = prompt_lower.replace(func, '', 1).strip()
                
                # Handle common command patterns
                if func == "bluetooth":
                    if "on" in remaining or "enable" in remaining or "turn on" in prompt_lower:
                        return [f"{func} : on"]
                    elif "off" in remaining or "disable" in remaining or "turn off" in prompt_lower:
                        return [f"{func} : off"]
                    else:
                        return [f"{func} : status"]  # Default to status check
                elif func == "wifi":
                    if "on" in remaining or "enable" in remaining or "turn on" in prompt_lower:
                        return [f"{func} : on"]
                    elif "off" in remaining or "disable" in remaining or "turn off" in prompt_lower:
                        return [f"{func} : off"]
                    else:
                        return [f"{func} : status"]
                elif func == "volume":
                    if "up" in remaining or "increase" in remaining:
                        return [f"{func} : up"]
                    elif "down" in remaining or "decrease" in remaining:
                        return [f"{func} : down"]
                    elif "mute" in remaining:
                        return [f"{func} : mute"]
                    else:
                        return [f"{func} : up"]  # Default
                elif func == "brightness":
                    if "up" in remaining or "increase" in remaining:
                        return [f"{func} : up"]
                    elif "down" in remaining or "decrease" in remaining:
                        return [f"{func} : down"]
                    else:
                        return [f"{func} : up"]  # Default
                elif func == "play":
                    # Extract what to play from the prompt
                    play_keywords = ["play", "song", "music", "video"]
                    extracted = remaining
                    for keyword in play_keywords:
                        if keyword in extracted:
                            extracted = extracted.replace(keyword, "").strip()
                    return [f"{func} : {extracted}"]
                elif func == "whatsapp":
                    # Handle WhatsApp commands with better argument parsing
                    if "send" in remaining or "message" in remaining or "whatsapp" in remaining:
                        # Extract contact and message
                        # Format 1: "send message to john saying hello"
                        if "to " in remaining and "saying " in remaining:
                            to_index = remaining.find("to ")
                            saying_index = remaining.find("saying ")
                            if to_index != -1 and saying_index != -1:
                                contact = remaining[to_index+3:saying_index].strip()
                                message = remaining[saying_index+7:].strip()
                                return [f"whatsapp : send:{contact}:{message}"]
                        # Format 2: "send 'message' to 'contact'" or "send message to contact"
                        elif "to " in remaining:
                            # Find the last occurrence of "to " to get the contact name
                            parts = remaining.split(" to ")
                            if len(parts) >= 2:
                                # Everything after the last "to" is the contact name
                                contact = parts[-1].strip()
                                # Everything before "to" (after removing send/message words) is the message
                                message_part = " to ".join(parts[:-1])
                                message = message_part.replace("send", "").replace("a", "").replace("message", "").strip()
                                # Clean up message - remove extra quotes and spaces
                                message = message.strip('"\' ').strip()
                                contact = contact.strip('"\' ').strip()
                                return [f"whatsapp : send:{contact}:{message}"]
                        # Format 3: Just "send <message>" without contact (user will select)
                        elif "send" in remaining:
                            # Extract just the message content, remove command words
                            message = remaining.replace("send", "").replace("a", "").replace("message", "").replace("whatsapp", "").strip()
                            message = message.strip('"\' ').strip()
                            # If no contact specified, user will need to select manually
                            return [f"whatsapp : send:: {message}"]
                        # Format 4: "contact:message"
                        elif ":" in remaining:
                            # Handle format "contact:message"
                            parts = remaining.split(":", 1)
                            if len(parts) == 2:
                                contact = parts[0].strip()
                                message = parts[1].strip()
                                return [f"whatsapp : send:{contact}:{message}"]
                    elif "call" in remaining:
                        # Handle call commands
                        if "video" in remaining:
                            # Video call
                            contact = remaining.replace("video", "").replace("call", "").replace("with", "").strip()
                            return [f"whatsapp : video:{contact}"]
                        else:
                            # Voice call
                            contact = remaining.replace("call", "").strip()
                            return [f"whatsapp : call:{contact}"]
                    elif "video" in remaining:
                        # Handle video call commands directly
                        contact = remaining.replace("video", "").replace("call", "").replace("with", "").strip()
                        return [f"whatsapp : video:{contact}"]
                    else:
                        # Default to send format
                        return [f"whatsapp : {remaining}"]
                elif func == "message":
                    # Handle message sending with better argument parsing
                    if "to " in remaining and "saying " in remaining:
                        # Handle "to [contact] saying [message]" format
                        to_index = remaining.find("to ")
                        saying_index = remaining.find("saying ")
                        if to_index != -1 and saying_index != -1:
                            contact = remaining[to_index+3:saying_index].strip()
                            message = remaining[saying_index+7:].strip()
                            return [f"message : {contact}:{message}"]
                    elif "to " in remaining:
                        # Handle "send [message] to [contact]" format
                        to_index = remaining.find("to ")
                        message_part = remaining[:to_index].strip()
                        contact = remaining[to_index+3:].strip()
                        
                        # Clean message part - remove command words (use word boundaries)
                        import re
                        clean_message = message_part
                        # Remove complete words only, not substrings
                        for word in ['send', 'tell', 'text']:
                            clean_message = re.sub(r'\b' + word + r'\b', '', clean_message, flags=re.IGNORECASE).strip()
                        # Remove articles carefully
                        clean_message = re.sub(r'^\s*(a|an|the)\s+', ' ', clean_message, flags=re.IGNORECASE).strip()
                        clean_message = clean_message.strip('"\' ').strip()
                        
                        if clean_message and contact and len(clean_message) > 1:
                            return [f"message : {contact}:{clean_message}"]
                        elif contact:
                            return [f"message : {contact}:Hello"]
                    elif ":" in remaining:
                        parts = remaining.split(":", 1)
                        if len(parts) == 2:
                            contact = parts[0].strip()
                            message = parts[1].strip()
                            return [f"message : {contact}:{message}"]
                    else:
                        # Try to extract contact from common phrases
                        if "to " in remaining:
                            parts = remaining.split("to ", 1)
                            if len(parts) > 1:
                                contact_message = parts[1].strip()
                                if ":" in contact_message:
                                    contact_parts = contact_message.split(":", 1)
                                    contact = contact_parts[0].strip()
                                    message = contact_parts[1].strip()
                                    return [f"message : {contact}:{message}"]
                        # Fallback - clean the remaining text
                        import re
                        clean_message = remaining
                        # Remove complete words only, not substrings
                        for word in ['send', 'tell', 'text']:
                            clean_message = re.sub(r'\b' + word + r'\b', '', clean_message, flags=re.IGNORECASE).strip()
                        # Remove articles carefully
                        clean_message = re.sub(r'^\s*(a|an|the)\s+', ' ', clean_message, flags=re.IGNORECASE).strip()
                        clean_message = clean_message.strip('"\' ').strip()
                        return [f"message : {clean_message}"]
                elif func == "call":
                    # Handle call commands more specifically
                    if "video" in remaining:
                        # This is a video call command
                        contact = remaining.replace("video", "").replace("with", "").replace("call", "").strip()
                        return [f"whatsapp : video:{contact}"]
                    else:
                        # This is a regular voice call
                        contact = remaining.replace("with", "").replace("the", "").strip()
                        return [f"call : {contact}"]
                elif func == "calendar":
                    # Handle calendar commands
                    return [f"calendar : {remaining}"]
                elif func == "google search":
                    search_text = remaining.replace("for", "").replace("about", "").strip()
                    return [f"{func} : {search_text}"]
                elif func == "youtube search":
                    search_text = remaining.replace("for", "").replace("about", "").strip()
                    return [f"{func} : {search_text}"]
                elif func == "youtube play":
                    play_text = remaining.replace("for", "").replace("song", "").replace("music", "").strip()
                    return [f"{func} : {play_text}"]
                else:
                    # For other functions, return the remaining text
                    clean_remaining = remaining.strip('. ')
                    return [f"{func} : {clean_remaining}"] if clean_remaining else [f"{func} : "]
    
    # NEW: Flexible message detection - check for message-related keywords even if not in funcs
    message_related_keywords = [
        'send', 'message', 'text', 'whatsapp', 'chat', 'sms', 'msg', 'tell', 'say', 'send to'
    ]
    
    for keyword in message_related_keywords:
        if keyword in prompt_lower:
            # Try to extract contact and message from various formats
            if ' to ' in prompt_lower and (' saying ' in prompt_lower or ' that ' in prompt_lower):
                # Handle "send to [contact] saying [message]" or "tell [contact] that [message]"
                to_idx = prompt_lower.find(' to ') if ' to ' in prompt_lower else prompt_lower.find(' tell ')
                if ' saying ' in prompt_lower:
                    msg_idx = prompt_lower.find(' saying ')
                elif ' that ' in prompt_lower:
                    msg_idx = prompt_lower.find(' that ')
                else:
                    msg_idx = -1
                
                if to_idx != -1 and msg_idx != -1 and msg_idx > to_idx:
                    contact = prompt[to_idx + 4:msg_idx].strip()
                    message = prompt[msg_idx + 7:].strip() if ' saying ' in prompt_lower else prompt[msg_idx + 5:].strip()
                    return [f"message : {contact}:{message}"]
            elif ' to ' in prompt_lower:
                # Handle "send [message] to [contact]" - reverse format
                to_idx = prompt_lower.find(' to ')
                message_part = prompt[:to_idx].strip()
                contact = prompt[to_idx + 4:].strip()
                
                # Extract just the message part (remove command words)
                import re
                message_words = ['send', 'message', 'text', 'tell', 'say', 'whatsapp']
                clean_message = message_part
                for word in message_words:
                    clean_message = re.sub(r'\b' + word + r'\b', '', clean_message, flags=re.IGNORECASE).strip()
                # Remove articles carefully
                clean_message = re.sub(r'^\s*(a|an|the)\s+', ' ', clean_message, flags=re.IGNORECASE).strip()
                
                if clean_message and contact:
                    return [f"message : {contact}:{clean_message}"]
                elif contact:
                    # If no clean message found, use a default
                    return [f"message : {contact}:Hello"]
            else:
                # Generic message command without contact - extract only the message content
                # Remove all command words to get just the actual message
                import re
                message_words = ['send', 'message', 'text', 'tell', 'say', 'whatsapp']
                clean_message = prompt
                for word in message_words:
                    clean_message = re.sub(r'\b' + word + r'\b', '', clean_message, flags=re.IGNORECASE).strip()
                # Remove articles carefully
                clean_message = re.sub(r'^\s*(a|an|the)\s+', ' ', clean_message, flags=re.IGNORECASE).strip()
                clean_message = clean_message.strip('"\' ').strip()
                
                # Return with empty contact (user will need to select manually)
                return [f"message : :{clean_message}"]
    
    try:
        # CORRECTED: Changed 'content' to 'message' to fix the Cohere API error.
        messages = [{"role": "system", "message": preamble}]
        
        response = co.chat(
            model="command-light",
            message=prompt,
            chat_history=messages,
            preamble=preamble,
            temperature=0.7
        )
        
        text = response.text.lower().strip()
        tasks = [t.strip() for t in text.split("</t>") if t.strip()]

        formatted_tasks = []
        for task in tasks:
            task = task.strip().strip('"')
            # Check if task already has proper format
            if '(' in task and ')' in task:
                # Standard format "command ( argument )"
                formatted_tasks.append(task)
            elif ':' in task:
                parts = task.split(":", 1)
                if len(parts) == 2:
                    cmd = parts[0].strip()
                    content = parts[1].strip()
                    if cmd in ["general", "realtime"]:
                        formatted_tasks.append(f"{cmd} ( {content} )")
                    else:
                        formatted_tasks.append(f"{cmd} : {content}")
                else:
                    formatted_tasks.append(f"general ( {task} )")
            else:
                # Try to detect function type from the raw task
                matched_func = None
                for func in funcs:
                    if func in task.lower():
                        matched_func = func
                        break
                
                if matched_func:
                    if matched_func in ["general", "realtime"]:
                        formatted_tasks.append(f"{matched_func} ( {task} )")
                    else:
                        # Extract the argument part after the function name
                        pos = task.lower().find(matched_func)
                        if pos != -1:
                            arg_part = task[pos + len(matched_func):].strip()
                            formatted_tasks.append(f"{matched_func} : {arg_part}")
                        else:
                            formatted_tasks.append(f"{matched_func} : {task}")
                else:
                    formatted_tasks.append(f"general ( {task} )")

        return formatted_tasks

    except cohere.core.api_error.ApiError as e:
        print(f"ERROR: Cohere API call failed with exception: {e}")
        # Fallback to manual parsing
        return manual_parse_fallback(prompt_lower)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Fallback to manual parsing
        return manual_parse_fallback(prompt_lower)


def manual_parse_fallback(prompt):
    """Manual parsing fallback when Cohere API fails"""
    prompt_lower = prompt.lower().strip()
    
    # Check for real-time related queries first
    realtime_keywords = [
        'time', 'date', 'today', 'weather', 'news', 'latest', 'current', 
        'now', 'temperature', 'forecast', 'stock', 'price', 'updates',
        'what day', 'day is it', 'month', 'year', 'hour', 'minute', 'second'
    ]
    
    # Check for real-time keywords
    for keyword in realtime_keywords:
        if keyword in prompt_lower:
            return [f"realtime ( {prompt} )"]
    
    # Define function patterns - ORDER MATTERS!
    func_patterns = {
        'whatsapp': ['whatsapp', 'whats app', 'send message'],
        'message': ['message', 'text'],
        'call': ['call', 'phone call', 'voice call'],
        'open': ['open'],
        'close': ['close'],
        'play': ['play'],
        'google search': ['google search', 'search google'],
        'youtube search': ['youtube search', 'search youtube'],
        'youtube play': ['youtube play', 'play on youtube'],
        'generate image': ['generate image', 'image generation'],
        'content': ['content', 'write', 'essay', 'letter', 'application'],
        'wifi': ['wifi', 'wi-fi'],
        'bluetooth': ['bluetooth'],
        'brightness': ['brightness'],
        'volume': ['volume'],
        'media': ['media']
    }
    
    for func, patterns in func_patterns.items():
        for pattern in patterns:
            if pattern in prompt_lower:
                # Extract argument after the pattern
                pos = prompt_lower.find(pattern)
                arg = prompt_lower[pos + len(pattern):].strip()
                # Clean up common words - especially for WhatsApp/message commands
                if func in ['whatsapp', 'message']:
                    # Remove command words from the message content
                    arg = arg.replace("send", "").replace("a", "").replace("message", "").replace("whatsapp", "").replace("to", "").strip()
                    arg = arg.strip('"\' ').strip()
                else:
                    # For other functions, just remove basic words
                    arg = arg.replace("for", "").replace("about", "").replace("a", "").strip()
                return [f"{func} : {arg}" if arg else f"{func} : "]
    
    # If no specific function found, return general
    return ["general ( " + prompt + " )"]
    
if __name__ == "__main__":
    while True:
        print(FirstlayerDMM(input(">>> ")))