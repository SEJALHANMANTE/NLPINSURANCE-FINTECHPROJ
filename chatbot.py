import sqlite3
import speech_recognition as sr
import pyttsx3
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from IPython.display import display, Markdown

# ✅ Set Up OpenRouter API
API_KEY = "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" #"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"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
    default_headers={ 
        "Authorization": f"Bearer {API_KEY}",  
        "X-Title": "Insurance Chatbot"
    }
)

from IPython.display import display, Markdown


# ✅ Load Fine-Tuned Sentence Transformer
model = SentenceTransformer(r"C:\Users\DELL\Documents\GitHub\NLPINSURANCE-FINTECHPROJ\custom_insurance_encoder")

# ✅ Load Insurance Questions
import json
with open(r"C:\Users\DELL\Documents\GitHub\NLPINSURANCE-FINTECHPROJ\Chatbot\decoded_questions.json", "r", encoding="utf-8") as file:
    insurance_data = json.load(file)

questions = [entry["question"] for entry in insurance_data]
question_embeddings = model.encode(questions)

# ✅ Set Up SQLite for Memory
conn = sqlite3.connect("chatbot_memory.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS chatbot_memory (query TEXT, response TEXT)")
conn.commit()



def respond_to_query(user_query):
    if user_query.strip().lower() in ["thank you", "thanks", "ok", "exit", "goodbye", "bye"]:
        return "You're welcome! Have a great day! 😊"
    bot_response = get_insurance_response(user_query)
    return bot_response



# ✅ Function to Search Memory
def search_memory(user_query):
    cursor.execute("SELECT response FROM chatbot_memory WHERE query=?", (user_query,))
    result = cursor.fetchone()
    return result[0] if result else None

# ✅ Function to Store in Memory
def store_memory(user_query, response):
    cursor.execute("INSERT INTO chatbot_memory (query, response) VALUES (?, ?)", (user_query, response))
    conn.commit()

# ✅ Function for Semantic Search
def find_relevant_questions(user_query):
    query_embedding = model.encode([user_query])
    similarities = np.dot(query_embedding, question_embeddings.T)[0]
    top_indices = np.argsort(similarities)[-3:][::-1]
    relevant_questions = [questions[i] for i in top_indices]
    return relevant_questions

# ✅ Function to Get Insurance Answer
def get_insurance_response(user_query):
    # Step 1: Check Memory
    memory_response = search_memory(user_query)
    if memory_response:
        return f"[From Memory] {memory_response}"

    # Step 2: Find Relevant Questions
    relevant_questions = find_relevant_questions(user_query)

    # Step 3: Call OpenRouter (DeepSeek R1)
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1:free", #"deepseek/deepseek-v3-base:free",  #
            messages=[
                {"role": "system", "content": "You are an insurance chatbot based from India who follows rules and regulations related to insurance for India. Answer insurance-related questions only. If non-insurance related questions asked please politely deny saying i am not made for this domain"},
                {"role": "user", "content": f"User Query: {user_query}\nRelevant Questions: {relevant_questions}"}
            ],
            temperature=0.3,
        )
        chatbot_response = response.choices[0].message.content
        store_memory(user_query, chatbot_response)  # Save response in memory
        return chatbot_response
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Voice Input & Output Functions
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand."
    except sr.RequestError:
        return "Speech recognition service is unavailable."

def speak_response(response):
    engine = pyttsx3.init()
    engine.say(response)
    
    try:
        engine.runAndWait()  # Normal execution
    except RuntimeError:
        engine.endLoop()  # Stop the current event loop
        engine.runAndWait() 



# ✅ Main Chat Loop (Conversation Mode)
def start_chatbot():
    print("💬 Insurance Chatbot Started! Type 'voice' for voice input. Say 'thank you', 'ok', or 'exit' to stop.")
    
    while True:
        user_input = input("👤 You: ").strip().lower()
        print("User question: " ,user_input)

        # Handle voice input
        if user_input == "voice":
            user_input = recognize_speech()
            print(f"👤 You (via voice): {user_input}")

        # Check for exit words
        if user_input in ["thank you", "thanks", "ok", "exit", "goodbye", "bye"]:
            print("🤖 Bot: You're welcome! Have a great day! 😊")
            speak_response("You're welcome! Have a great day!")
            break

        # Get response
        bot_response = get_insurance_response(user_input)
    
        display(Markdown(f"🤖 Bot: {bot_response}"))
        speak_response(bot_response)

        # Ask if further help is needed
        follow_up = input("🤖 Bot: Do you need help with anything else? (yes/no) ").strip().lower()
        if follow_up in ["no", "thank you", "thanks", "ok", "exit", "goodbye", "bye"]:
            print("🤖 Bot: Have a great day! 😊")
            speak_response("Have a great day!")
            break



# ✅ Run the Chatbot
if __name__ == "__main__":
    start_chatbot()
