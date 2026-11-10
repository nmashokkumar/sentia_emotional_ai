# =============================
# IMPORTS
# =============================

from core.stt_engine import speech_to_text
from core.emotion import detect_emotion
from core.voice_detection import predict_emotion
from core.voice_fusion_logic import fuse_emotions


# =============================
# VOICE PIPELINE
# =============================

def voice_pipeline(audio_path):

    print("\n[VOICE PIPELINE] Running...")

    # -----------------------------
    # 1. SPEECH TO TEXT
    # -----------------------------
    text = speech_to_text(audio_path)

    print("[STT OUTPUT]:", text)

    # Safety check
    if not text or len(text.strip()) == 0:
        print("[STT ERROR] No speech detected")

        return {
            "text": "",
            "emotion": "neutral",
            "confidence": 0.5,
            "response": "I couldn't hear clearly, can you try again?"
        }

    # -----------------------------
    # 2. TEXT EMOTION
    # -----------------------------
    text_emotion, text_conf = detect_emotion(text)

    print("[TEXT EMOTION]:", text_emotion, text_conf)

# -----------------------------
# 3. VOICE EMOTION
# -----------------------------
    voice_result = predict_emotion(audio_path)

    # 🔥 FIX: extract properly from dict
    voice_emotion = str(voice_result.get("emotion", "neutral"))

    try:
        voice_conf = float(voice_result.get("confidence", 0.5))
    except:
        voice_conf = 0.5

# normalize if needed (0–100 → 0–1)
    if voice_conf > 1:
        voice_conf = voice_conf / 100

    print("[VOICE EMOTION]:", voice_emotion, voice_conf)
    # -----------------------------
    # 4. FUSION LOGIC
    # -----------------------------
    final_emotion, final_conf = fuse_emotions(
        text_emotion, text_conf,
        voice_emotion, voice_conf
    )

    print("[FINAL EMOTION]:", final_emotion, final_conf)

    # -----------------------------
    # 5. RETURN (NO LLM YET)
    # -----------------------------
    return {
        "text": text,
        "emotion": final_emotion,
        "confidence": final_conf
    }