import speech_recognition as sr
import os
import mtranslate as mt
from dotenv import dotenv_values

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
# Get the input language setting from the environment variables.
InputLanguage = env_vars.get("InputLanguage")

# Define the path for temporary files.
current_dir = os.getcwd()
TempDirPath = rf"{current_dir}/Frontend/Files"

# Function to set the assistant's status by writing it to a file.
def SetAssistantStatus(Status):
    """Writes the assistant's current status to a file."""
    try:
        with open(rf"{TempDirPath}/Status.data", "w", encoding='utf-8') as file:
            file.write(Status)
    except FileNotFoundError:
        print(f"Status file not found at: {TempDirPath}/Status.data")

# Function to modify a query to ensure proper punctuation and formatting.
def QueryModifier(Query):
    """Adds a period or question mark to a query for better formatting."""
    new_query = Query.lower().strip()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "what is"]

    if any(word in new_query for word in question_words):
        if new_query[-1] not in ['.', '?', '!']:
            new_query += "?"
    else:
        if new_query[-1] not in ['.', '?', '!']:
            new_query += "."
    
    return new_query.capitalize()

# Function to translate text into English using the mtranslate library.
def UniversalTranslator(Text):
    """Translates a given text to English."""
    try:
        english_translation = mt.translate(Text, "en", "auto")
        return english_translation.capitalize()
    except Exception as e:
        print(f"Translation error: {e}")
        return Text

# Function to perform speech recognition for multiple languages.
def SpeechRecognition():
    """Listens for audio, recognizes it in multiple languages, and returns a formatted English query."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        SetAssistantStatus("Listening...")
        
        try:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
            print("Recognizing...")
            SetAssistantStatus("Recognizing...")

            text = None
            detected_language = None
            
            # --- Attempt 1: Recognize in English ---
            try:
                text = r.recognize_google(audio, language="en-IN")
                detected_language = "English"
            except sr.UnknownValueError:
                pass # Continue to the next language if English recognition fails.
            
            # --- Attempt 2: Recognize in Hindi if English fails ---
            if not text:
                try:
                    text = r.recognize_google(audio, language="hi-IN")
                    detected_language = "Hindi"
                except sr.UnknownValueError:
                    pass # Continue to the next language if Hindi recognition fails.

            # --- Attempt 3: Recognize in Telugu if Hindi fails ---
            if not text:
                try:
                    text = r.recognize_google(audio, language="te-IN")
                    detected_language = "Telugu"
                except sr.UnknownValueError:
                    pass # All attempts failed.
            
            if text:
                print(f"Detected language: {detected_language}")
                
                # If Hindi or Telugu, translate to English.
                if detected_language in ["Hindi", "Telugu"]:
                    SetAssistantStatus("Translating...")
                    english_text = UniversalTranslator(text)
                    return QueryModifier(english_text)
                else:
                    # If English, just format the text.
                    return QueryModifier(text)
            else:
                # If no text was recognized after all attempts.
                print("Could not understand audio in any of the supported languages.")
                SetAssistantStatus("Couldn't understand, waiting for input...")
                return None

        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            SetAssistantStatus("Service error, please check internet connection.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

# Main execution block.
if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        if text:
            print(text)