from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values

env_vars = dotenv_values(".env")

Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

messages = []

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""
SystemCallBot = [
    {"role": "system", "content": System}
]

def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def ChatBot(Query):
    global messages, SystemCallBot
    try:
        with open(r"Data\Chatlog.json", "r") as f:
            messages = load(f)
    except (FileNotFoundError, dump.JSONDecodeError):
        messages = []
        with open(r"Data\Chatlog.json", "w") as f:
            dump([], f)
    
    try:
        messages.append({"role": "user", "content": Query})

        # Limit the context to avoid token limit issues
        # Take only the last few exchanges to keep the context manageable
        recent_messages = []
        if len(messages) > 10:  # Limit to last 5 exchanges (10 messages)
            recent_messages = messages[-10:]
        else:
            recent_messages = messages[:]
        
        # Try with the primary model first
        model_name = "llama-3.3-70b-versatile"
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=SystemCallBot + recent_messages,
                temperature=0.7,
                max_tokens=2048,
                top_p=1,
                stream=True,
                stop=None
            )
        except Exception as api_error:
            print(f"Primary model failed: {api_error}")
            # Check if it's a token-related error and try to reduce context further
            if "token" in str(api_error).lower() or "limit" in str(api_error).lower():
                # Reduce context even more for token-related issues
                if len(recent_messages) > 4:
                    ultra_reduced_messages = recent_messages[-4:]  # Just last 2 exchanges
                else:
                    ultra_reduced_messages = recent_messages
                    
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=SystemCallBot + ultra_reduced_messages,
                        temperature=0.7,
                        max_tokens=2048,
                        top_p=1,
                        stream=True,
                        stop=None
                    )
                    print("Successfully used reduced context with primary model")
                except:
                    # Fallback to a model with higher token limits
                    try:
                        model_name = "mixtral-8x7b-32768"  # Higher token limit model
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=SystemCallBot + ultra_reduced_messages,
                            temperature=0.7,
                            max_tokens=2048,
                            top_p=1,
                            stream=True,
                            stop=None
                        )
                        print(f"Falling back to {model_name} model")
                    except:
                        # Final fallback - use a lightweight model with minimal context
                        final_messages = [{"role": "user", "content": Query}]  # Just the current query
                        model_name = "gemma2-9b-it"  # Lightweight model
                        completion = client.chat.completions.create(
                            model=model_name,
                            messages=SystemCallBot + final_messages,
                            temperature=0.7,
                            max_tokens=2048,
                            top_p=1,
                            stream=True,
                            stop=None
                        )
                        print(f"Using minimal context with {model_name} model")
            else:
                # For non-token errors, try alternate models
                try:
                    model_name = "mixtral-8x7b-32768"  # Higher token limit model
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=SystemCallBot + recent_messages,
                        temperature=0.7,
                        max_tokens=2048,
                        top_p=1,
                        stream=True,
                        stop=None
                    )
                    print(f"Falling back to {model_name} model")
                except:
                    # Final fallback - use a lightweight model with minimal context
                    final_messages = [{"role": "user", "content": Query}]  # Just the current query
                    model_name = "gemma2-9b-it"  # Lightweight model
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=SystemCallBot + final_messages,
                        temperature=0.7,
                        max_tokens=2048,
                        top_p=1,
                        stream=True,
                        stop=None
                    )
                    print(f"Using minimal context with {model_name} model")

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s2>", "").strip()
        print(f"[ChatBot] Generated response: {Answer[:100]}...")
        
        messages.append({"role": "assistant", "content": Answer})

        with open(r"Data\Chatlog.json", "w", encoding="utf-8") as f:
            dump(messages, f, indent=4)
        print(f"[ChatBot] Chat log updated with {len(messages)} messages")

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        print(f"Error: {e}")
        # Check if it's a token limit error and try to handle it gracefully
        error_str = str(e).lower()
        if "token" in error_str or "limit" in error_str or "request too large" in error_str:
            # Try with minimum context using a lightweight model
            try:
                minimal_messages = [{"role": "user", "content": Query}]
                completion = client.chat.completions.create(
                    model="gemma2-9b-it",  # Use a lightweight model
                    messages=SystemCallBot + minimal_messages,
                    temperature=0.7,
                    max_tokens=2048,
                    top_p=1,
                    stream=True,
                    stop=None
                )
                
                Answer = ""
                for chunk in completion:
                    if chunk.choices[0].delta.content:
                        Answer += chunk.choices[0].delta.content

                Answer = Answer.replace("</s2>", "").strip()
                print(f"[ChatBot] Generated response with minimal context: {Answer[:100]}...")
                
                messages.append({"role": "assistant", "content": Answer})

                with open(r"Data\Chatlog.json", "w", encoding="utf-8") as f:
                    dump(messages, f, indent=4)
                
                return AnswerModifier(Answer=Answer)
            except:
                pass  # If even minimal context fails, return the default error message
        return "I am sorry, but I am unable to respond to that request."

if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))