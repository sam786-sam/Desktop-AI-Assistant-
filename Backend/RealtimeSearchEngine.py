from tavily import TavilyClient
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================
env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")
TavilyAPIKey = env_vars.get("TavilyAPIKey", "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")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in .env file")

# =========================
# INITIALIZE GROQ AND TAVILY CLIENTS
# =========================
client = Groq(api_key=GroqAPIKey)
tavily_client = TavilyClient(api_key=TavilyAPIKey)

# =========================
# SYSTEM PROMPT
# =========================
System = f"""
Hello, I am {Username}.
You are a very accurate and advanced AI chatbot named {Assistantname}
which has real-time up-to-date information from internet search.

*** Provide answers in a professional way.
*** Use proper grammar, commas, and full stops.
*** Answer strictly from the provided data.
*** Give comprehensive and detailed responses, not just one-line answers.
*** Explain the topic thoroughly with all relevant information available.
*** If multiple aspects of a topic are covered in the search results, include all of them in your response.
*** DO NOT mention "Tavily", "search results", or any similar phrases in your response.
*** Just provide the answer naturally as if you already know this information.
*** Never say "according to" or "based on search results" - simply state the facts directly.
"""

# =========================
# CHAT LOG INITIALIZATION
# =========================
CHATLOG_PATH = "Data/ChatLog.json"

os.makedirs("Data", exist_ok=True)

try:
    with open(CHATLOG_PATH, "r") as f:
        messages = load(f)
except:
    with open(CHATLOG_PATH, "w") as f:
        dump([], f)
    messages = []

# =========================
# TAVILY SEARCH FUNCTION
# =========================
def TavilySearch(query):
    try:
        # Use search with include_answer=True to get a direct answer
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,  # Get more results for comprehensive answers
            include_answer=True
        )
        
        # Build a comprehensive response from all available information
        comprehensive_answer = []
        
        # Add the main answer if available
        if 'answer' in response and response['answer']:
            answer = response['answer']
            comprehensive_answer.append(answer)
        
        # Add detailed content from results
        if 'results' in response and len(response['results']) > 0:
            for i, result in enumerate(response['results'][:3]):  # Take top 3 results
                content = result.get('content', '')
                if content and len(content) > 50:  # Only add substantial content
                    comprehensive_answer.append(content)
        
        # Combine all information
        if comprehensive_answer:
            # Join all parts with proper formatting
            detailed_response = "\n\n".join(comprehensive_answer)
            
            # Ensure it's not too long (limit to ~800 characters)
            if len(detailed_response) > 800:
                detailed_response = detailed_response[:797] + "..."
            
            return detailed_response  # Return just the content without prefix
        else:
            return f"No specific answer found for query: {query}"
            
    except Exception as e:
        print(f"Tavily search error: {e}")
        return f"[No results available due to search error]"

# =========================
# ANSWER CLEANER
# =========================
def AnswerModifier(answer):
    lines = answer.split("\n")
    return "\n".join(line for line in lines if line.strip())

# =========================
# SYSTEM CHAT MEMORY
# =========================
SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# =========================
# REAL-TIME INFORMATION
# =========================
def Information():
    now = datetime.datetime.now()
    return (
        "Real-time information:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
    )

# =========================
# REALTIME SEARCH ENGINE
# =========================
def RealtimeSearchEngine(prompt):
    global messages

    with open(CHATLOG_PATH, "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": prompt})

    # Add Tavily search result as system context
    SystemChatBot.append(
        {"role": "system", "content": TavilySearch(prompt)}
    )

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=(
            SystemChatBot
            + [{"role": "system", "content": Information()}]
            + messages[-6:]  # LIMIT CHAT HISTORY (TPM SAFE)
        ),
        temperature=0.7,
        max_tokens=1024,
        top_p=1,
        stream=True
    )

    answer = ""

    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content

    answer = answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": answer})

    with open(CHATLOG_PATH, "w") as f:
        dump(messages, f, indent=4)

    # Remove last system search result
    SystemChatBot.pop()

    return AnswerModifier(answer)

# =========================
# MAIN LOOP
# =========================
if __name__ == "__main__":
    print(f"{Assistantname} is running with Tavily API...\n")
    while True:
        try:
            prompt = input("Enter your query: ")
            if prompt.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            print("\n" + RealtimeSearchEngine(prompt) + "\n")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
