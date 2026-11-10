import requests
import time


# ==============================
# CONFIG
# ==============================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "sentia_ft_2:latest"

# Minimal parameters for natural output
LLM_PARAMS = {
    "temperature": 0.85,
    "top_p": 0.95,
    "repeat_penalty": 1.1,
    "num_predict": 180   # 🔥 increase
}


# ==============================
# LLM ENGINE (Singleton)
# ==============================

class SentiaLLM:

    _instance = None
    _last_used = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        if hasattr(self, "initialized"):
            return

        self.initialized = True
        self._last_used = None


    # --------------------------
    # GENERATE RESPONSE
    # --------------------------

    def generate_response(self, prompt):

        self._last_used = time.time()

        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": LLM_PARAMS
                }
            )

            data = response.json()
            text = data.get("response", "").strip()

            return self._clean(text)

        except Exception as e:
            print("LLM Error:", e)
            return "Sorry, I couldn't respond properly."


    # --------------------------
    # CLEAN OUTPUT
    # --------------------------

    def _clean(self, text):

        text = text.replace("\n", " ").strip()

        # remove unwanted prefix
        if "Sentia:" in text:
            text = text.split("Sentia:")[-1]

    # remove repetition
        parts = text.split(". ")
        seen = []
        for p in parts:
            if p not in seen:
                seen.append(p)

        text = ". ".join(seen)

        # 🔥 SAFE FALLBACK (IMPORTANT)
        if not text or len(text.strip()) < 3:
            return "that sounds a bit intense... what’s going on?"

        return text.strip()


# ==============================
# SIMPLE FUNCTION
# ==============================

llm_instance = SentiaLLM()

def generate_response(prompt):
    return llm_instance.generate_response(prompt)