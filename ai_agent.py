import google.generativeai as genai
import streamlit as st
import time
import os

DEFAULT_MODELS = (
    "gemini-2.0-flash",
    "gemini-1.5-flash",
)


def _model_candidates():
    """
    Priority:
    1) GEMINI_MODEL env override
    2) Built-in stable defaults
    """
    override = os.getenv("GEMINI_MODEL")
    if override:
        yield override
    for model_name in DEFAULT_MODELS:
        yield model_name


def get_api_key():
    """
    Ye function API Key dhoondhne ki koshish karega.
    Pehle Cloud Secrets mein, phir Local Secrets mein.
    """
    try:
        # Step 1: Streamlit Secrets check karo (Cloud & Local)
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        # Step 2: Agar Secrets nahi mile, toh Environment Variable check karo
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _normalize_ai_error(model_name, model_error):
    message = str(model_error)
    lowered = message.lower()

    if (
        "api_key_http_referrer_blocked" in lowered
        or "requests from referer <empty> are blocked" in lowered
        or ("403" in lowered and "referer" in lowered and "blocked" in lowered)
    ):
        return (
            "AI Error: This Gemini key is restricted by HTTP referrer, but this app "
            "calls Gemini from Python (server-side), so referer is empty. "
            "Use a server-compatible key (Application restrictions: None or IP), "
            "then update GEMINI_API_KEY in Streamlit secrets/env and restart."
        )

    if "reported as leaked" in lowered or ("403" in lowered and "leaked" in lowered):
        return (
            "AI Error: Your Gemini API key was flagged as leaked (403). "
            "Create a new key in Google AI Studio, then update GEMINI_API_KEY "
            "in .streamlit/secrets.toml (or env var) and restart the app."
        )

    if "api key not valid" in lowered or "invalid api key" in lowered:
        return (
            "AI Error: Invalid Gemini API key. "
            "Check GEMINI_API_KEY in your Streamlit secrets or environment."
        )

    return f"AI Error ({model_name}): {message}"

def generate_script(topic):
    # 1. API Key fetch karo secure tarike se
    api_key = get_api_key()
    
    if not api_key:
        return (
            "Error: API key missing. Add GEMINI_API_KEY to .streamlit/secrets.toml "
            "or set GEMINI_API_KEY/GOOGLE_API_KEY as an environment variable."
        )

    try:
        # 2. Configure Gemini
        genai.configure(api_key=api_key)

        prompt = f"""
        Acționează ca un influencer tech celebru, cu un stil energic, pasionat și foarte accesibil publicului larg.
Subiect: {topic}
Scrie un script viral pentru un Reel de 30 de secunde în stil viral si in engleza, adaptat pentru platforma Instagram/YouTube Shorts.
Structură detaliată:
🎬 Hook (0–3 secunde): Linie de impact

Începe cu o întrebare provocatoare SAU o afirmație șocantă legată de subiect
Trebuie să oprească utilizatorul din scroll instantaneu
Folosește un ton urgent, surprinzător sau curios
Exemplu de format: "Yaar, tu ancora folosești X?! Bhai, ascultă-mă..."

📖 Explicație (3–20 secunde): Conținut simplu și captivant

Explică subiectul în termeni simpli, ca și cum ai vorbi cu un prieten
Folosește analogii din viața de zi cu zi pentru a face conceptele tehnice ușor de înțeles
Împarte informația în 2–3 idei clare și rapide
Adaugă energie vizuală prin gesturi sau tranziții sugerate în script (ex: [arată spre ecran], [ridică degetul mare])
Include cel puțin un element de umor sau surpriză specific culturii indiene

📣 CTA – Call to Action (20–30 secunde): Îndemn la acțiune

Cere follow într-un mod natural și prietenos, nu forțat
Adaugă un motiv concret pentru care merită să urmărească contul
Opțional: menționează că urmează mai mult conținut pe același subiect
Exemplu de format: "Dacă vrei să afli mai multe despre X, dă follow acum — în fiecare săptămână îți aduc cele mai tari tips tech!"
        """

        last_error = None
        for model_name in _model_candidates():
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as model_error:
                last_error = model_error
                msg = str(model_error).lower()
                if "not found" in msg or "not supported for generatecontent" in msg:
                    continue
                if "429" in msg:
                    time.sleep(2)
                    return "Server busy (Rate Limit), trying again... Please wait."
                return _normalize_ai_error(model_name, model_error)

        return f"AI Error: No supported Gemini model available. Last error: {last_error}"
        
    except Exception as e:
        # Agar quota error aaye toh retry logic
        if "429" in str(e):
            time.sleep(2)
            return "Server busy (Rate Limit), trying again... Please wait."
        return f"AI Error: {str(e)}"

if __name__ == "__main__":
    # Local testing ke liye warning
    print("Testing AI Agent...")
    print(generate_script("Virat Kohli"))
