import google.generativeai as genai
import os

# Manual .env loading to avoid dependency issues
try:
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
except FileNotFoundError:
    print(".env file not found")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not set")
    exit(1)

genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
