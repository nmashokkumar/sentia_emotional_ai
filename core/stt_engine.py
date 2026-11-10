import os
import wave
import json
import urllib.request
import zipfile
from vosk import Model, KaldiRecognizer


# =============================
# CONFIG
# =============================
MODEL_DIR = "models/vosk-model"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
ZIP_PATH = "models/vosk.zip"


# =============================
# DOWNLOAD MODEL (ONCE)
# =============================
def download_model():
    os.makedirs("models", exist_ok=True)

    # Check if already downloaded
    existing = [f for f in os.listdir("models") if f.startswith("vosk-model")]

    if existing:
        print("✅ STT model found locally")
        return os.path.join("models", existing[0])

    print("⏳ Downloading STT model (one-time)...")

    urllib.request.urlretrieve(MODEL_URL, ZIP_PATH)

    print("📦 Extracting model...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall("models")

    os.remove(ZIP_PATH)

    # Detect extracted folder
    extracted = [f for f in os.listdir("models") if f.startswith("vosk-model")]

    if not extracted:
        raise Exception("Model extraction failed")

    model_path = os.path.join("models", extracted[0])

    print("✅ STT model ready")

    return model_path
# =============================
# LOAD MODEL (ONCE)
# =============================
print("⏳ Initializing STT...")
MODEL_PATH = download_model()
model = Model(MODEL_PATH)
print("✅ STT model loaded")


# =============================
# SPEECH TO TEXT
# =============================
def speech_to_text(wav_path):
    try:
        wf = wave.open(wav_path, "rb")

        # -----------------------------
        # AUDIO VALIDATION
        # -----------------------------
        if wf.getnchannels() != 1:
            return "Error: Audio must be mono"

        if wf.getsampwidth() != 2:
            return "Error: Audio must be 16-bit"

        if wf.getframerate() not in [8000, 16000, 44100]:
            return "Error: Unsupported sample rate"

        rec = KaldiRecognizer(model, wf.getframerate())

        text = ""

        # -----------------------------
        # PROCESS AUDIO
        # -----------------------------
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text += result.get("text", "") + " "

        final_result = json.loads(rec.FinalResult())
        text += final_result.get("text", "")

        return text.strip()

    except Exception as e:
        return f"Error: {str(e)}"