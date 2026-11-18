import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

MODELS = [
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
]

for model in MODELS:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{model}:generateContent"
    )

    print(f"\nTesting: {model}")

    try:
        response = requests.post(
            url,
            headers={"x-goog-api-key": API_KEY},
            json={
                "contents": [
                    {"parts": [{"text": "Reply only: OK"}]}
                ]
            },
            timeout=90,
        )

        if response.status_code == 200:
            print("[SUCCESS] Model generated a response")

        else:
            error = response.json().get("error", {})
            print(
                f"[FAILED] HTTP {response.status_code} | "
                f"{error.get('status')} | "
                f"{error.get('message')}"
            )

    except requests.Timeout:
        print("[TIMEOUT] No response within 90 seconds")

    except requests.RequestException as error:
        print(f"[ERROR] {error}")