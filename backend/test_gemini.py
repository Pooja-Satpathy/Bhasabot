import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"Loaded API Key starting with: {api_key[:10] if api_key else 'None'}... (Length: {len(api_key) if api_key else 0})")

if not api_key:
    print("Error: GEMINI_API_KEY is not set in the .env file!")
    exit(1)

genai.configure(api_key=api_key)

try:
    print("Attempting to list available models...")
    models = genai.list_models()
    print("Successfully connected! Available models:")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"\nFailed to connect or retrieve models.")
    print(f"Error Details: {str(e)}")
    print("\nTroubleshooting Tips:")
    print("1. Did you get your key from Google AI Studio (https://aistudio.google.com)?")
    print("2. If you got it from Google Cloud Console, make sure the 'Generative Language API' is enabled.")
    print("3. Check if your API key was copied completely (is the length correct? standard keys are about 39 or 50+ characters).")
