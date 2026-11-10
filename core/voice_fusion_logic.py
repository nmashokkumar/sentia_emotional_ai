# =============================
# VOICE + TEXT FUSION LOGIC
# =============================

def fuse_emotions(text_emotion, text_conf, voice_emotion, voice_conf):

    print("\n[FUSION INPUT]")
    print("Text :", text_emotion, text_conf)
    print("Voice:", voice_emotion, voice_conf)

    # -----------------------------
    # NORMALIZE LABELS
    # -----------------------------
    voice_map = {
        "neu": "neutral",
        "hap": "happy",
        "sad": "sad",
        "ang": "angry",
        "fea": "anxious",
        "sur": "happy",
        "dis": "angry"
    }

    text_emotion = str(text_emotion).lower()
    voice_emotion = str(voice_emotion).lower()

    voice_emotion = voice_map.get(voice_emotion, voice_emotion)

    # -----------------------------
    # SAFE CONFIDENCE CONVERSION
    # -----------------------------
    try:
        text_conf = float(text_conf)
    except:
        text_conf = 0.5

    try:
        voice_conf = float(voice_conf)
    except:
        voice_conf = 0.5

    # normalize if needed (0–100 → 0–1)
    if text_conf > 1:
        text_conf = text_conf / 100
    if voice_conf > 1:
        voice_conf = voice_conf / 100

    # -----------------------------
    # EMOTION GROUPS
    # -----------------------------
    emotion_groups = {
        "positive": ["happy"],
        "negative": ["sad", "angry", "anxious", "lonely", "stressed"],
        "neutral": ["neutral"]
    }

    def get_group(emotion):
        for group, emotions in emotion_groups.items():
            if emotion in emotions:
                return group
        return "neutral"

    text_group = get_group(text_emotion)
    voice_group = get_group(voice_emotion)

    # -----------------------------
    # CASE 1: SAME EMOTION
    # -----------------------------
    if text_emotion == voice_emotion:
        final_emotion = text_emotion
        final_conf = (text_conf + voice_conf) / 2

    # -----------------------------
    # CASE 2: ONE IS NEUTRAL → PICK OTHER
    # -----------------------------
    elif text_emotion == "neutral" and voice_emotion != "neutral":
        final_emotion = voice_emotion
        final_conf = voice_conf

    elif voice_emotion == "neutral" and text_emotion != "neutral":
        final_emotion = text_emotion
        final_conf = text_conf

    # -----------------------------
    # CASE 3: SAME GROUP → SMART MERGE
    # -----------------------------
    elif text_group == voice_group:

        # if confidence very close → average
        if abs(text_conf - voice_conf) < 0.15:
            final_emotion = text_emotion
            final_conf = (text_conf + voice_conf) / 2

        # else pick stronger
        elif text_conf > voice_conf:
            final_emotion = text_emotion
            final_conf = text_conf
        else:
            final_emotion = voice_emotion
            final_conf = voice_conf

    # -----------------------------
    # CASE 4: DIFFERENT GROUP → PICK STRONGER
    # -----------------------------
    else:
        if voice_conf > text_conf:
            final_emotion = voice_emotion
            final_conf = voice_conf
        else:
            final_emotion = text_emotion
            final_conf = text_conf

    # -----------------------------
    # FINAL CLEAN
    # -----------------------------
    final_conf = round(float(final_conf), 2)

    print("[FUSED RESULT]:", final_emotion, final_conf)

    return final_emotion, final_conf