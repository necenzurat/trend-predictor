from google import genai
import os

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit(
        "Missing API key. Set GEMINI_API_KEY or GOOGLE_API_KEY before running."
    )

client = genai.Client(api_key=api_key)

print("Checking available models...")
try:
    for m in client.models.list():
        if 'generateContent' in m.supported_actions:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
