import google.generativeai as genai
import os
import time

# Manual .env loading
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

model_name = "gemini-2.0-flash-lite"
print(f"Testing {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
