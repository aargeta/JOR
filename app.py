import os
from dotenv import load_dotenv
from flask import Flask, Response, render_template
import requests
from io import BytesIO

# Load environment variables
load_dotenv()

# Grok API Configuration
GROK_API_URL = os.getenv("GROK_API_URL")
GROK_API_KEY = os.getenv("XAI_API_KEY")
PERSONALITY_PROMPT = os.getenv("SLEAZY_PERSONALITY", "Default fallback prompt")

# ElevenLabs API Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

app = Flask(__name__)

def call_grok(prompt: str) -> str:
    """ Calls Grok API and logs the response for debugging. """
    if not GROK_API_URL or not GROK_API_KEY:
        print("[ERROR] Missing GROK_API_URL or XAI_API_KEY")
        return "Error: Missing GROK_API_URL or XAI_API_KEY"
    
    headers = {"Authorization": f"Bearer {GROK_API_KEY}"}
    data = {"model": "grok-2-1212", "messages": [{"role": "user", "content": prompt}]}
    
    try:
        resp = requests.post(GROK_API_URL, json=data, headers=headers)
        print(f"[GROK] Response Code: {resp.status_code}")
        print(f"[GROK] Response Body: {resp.text}")

        if resp.status_code == 200:
            return resp.json().get('choices', [{}])[0].get('message', {}).get('content', "Error: Unexpected Grok response format.")
        else:
            return f"Error: Grok returned {resp.status_code} - {resp.text}"
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Grok API request failed: {e}")
        return f"Error: Grok API request failed: {e}"

def call_elevenlabs_tts(text: str) -> BytesIO:
    """ Calls ElevenLabs API and logs the response for debugging. """
    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        print("[ERROR] Missing ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID")
        return BytesIO(b"Error: ELEVENLABS_API_KEY or ELEVENLABS_VOICE_ID missing")
    
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "voice_settings": {"stability": 0.6, "similarity_boost": 0.9, "style_exaggeration": 0.0}}

    try:
        resp = requests.post(tts_url, json=data, headers=headers, stream=True)
        print(f"[ElevenLabs] Response Code: {resp.status_code}")
        print(f"[ElevenLabs] Response Headers: {resp.headers}")

        if resp.status_code == 200:
            return BytesIO(resp.content)
        else:
            error_msg = f"Error from ElevenLabs: {resp.status_code}, {resp.text}"
            print(f"[ERROR] {error_msg}")
            return BytesIO(error_msg.encode("utf-8"))

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] ElevenLabs API request failed: {e}")
        return BytesIO(f"Error: ElevenLabs API request failed: {e}".encode("utf-8"))

@app.route("/")
def serve_index():
    return render_template("index.html")

@app.route("/generate-tts", methods=["GET"])
def generate_tts():
    """ Handles TTS generation with debugging logs """
    print("[INFO] /generate-tts route called")
    
    grok_text = call_grok(PERSONALITY_PROMPT)
    if grok_text.startswith("Error:"):
        print(f"[ERROR] Grok Response: {grok_text}")
        return grok_text, 500

    mp3_data = call_elevenlabs_tts(grok_text)
    first_20 = mp3_data.getvalue()[:20].decode("utf-8", errors="ignore")
    
    if first_20.startswith("Error from ElevenLabs"):
        print(f"[ERROR] ElevenLabs Response: {mp3_data.getvalue().decode('utf-8')}")
        return mp3_data.getvalue().decode("utf-8"), 500

    print("[SUCCESS] Returning TTS audio file")
    return Response(mp3_data, mimetype="audio/mpeg")

if __name__ == "__main__":
    print(f"[DEBUG] GROK_API_URL: {GROK_API_URL}")
    print(f"[DEBUG] GROK_API_KEY: {bool(GROK_API_KEY)} (hidden for security)")
    print(f"[DEBUG] ELEVENLABS_API_KEY: {bool(ELEVENLABS_API_KEY)} (hidden for security)")
    print(f"[DEBUG] ELEVENLABS_VOICE_ID: {ELEVENLABS_VOICE_ID}")
    print(f"[DEBUG] PERSONALITY_PROMPT: {PERSONALITY_PROMPT[:50]} ...")

    app.run(host="0.0.0.0", port=5000, debug=True)
