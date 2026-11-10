# =============================
# OFFLINE SETTINGS (IMPORTANT)
# =============================
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"


# =============================
# IMPORTS
# =============================
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import torch
import librosa
import torch.nn.functional as F


# =============================
# CONFIG
# =============================
MODEL_PATH = "models/voice_model"  # 🔥 local saved model


# =============================
# LOAD MODEL (ONLY ONCE)
# =============================
print("⏳ Loading Voice Emotion Model (offline)...")

model = Wav2Vec2ForSequenceClassification.from_pretrained(MODEL_PATH)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_PATH)

model.eval()

print("✅ Voice Emotion Model Loaded")


# =============================
# PREDICT EMOTION
# =============================
def predict_emotion(audio_path):
    try:
        # -----------------------------
        # LOAD AUDIO (FORCE 16kHz)
        # -----------------------------
        speech, sr = librosa.load(audio_path, sr=16000)

        if len(speech) == 0:
            return {
                "emotion": "neutral",
                "confidence": 0.5
            }

        # -----------------------------
        # FEATURE EXTRACTION
        # -----------------------------
        inputs = feature_extractor(
            speech,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True
        )

        # -----------------------------
        # MODEL INFERENCE
        # -----------------------------
        with torch.no_grad():
            logits = model(**inputs).logits

        probs = F.softmax(logits, dim=1)

        confidence, predicted_class_id = torch.max(probs, dim=1)

        emotion = model.config.id2label[predicted_class_id.item()]
        confidence_score = round(confidence.item(), 3)  # 0–1 scale

        return {
            "emotion": emotion.lower(),
            "confidence": confidence_score
        }

    except Exception as e:
        print("[VOICE MODEL ERROR]:", str(e))

        return {
            "emotion": "neutral",
            "confidence": 0.5
        }


# =============================
# TEST (OPTIONAL)
# =============================
if __name__ == "__main__":
    test_audio = "temp.wav"

    if os.path.exists(test_audio):
        result = predict_emotion(test_audio)
        print("🎯 Emotion Result:", result)
    else:
        print("❌ temp.wav not found")