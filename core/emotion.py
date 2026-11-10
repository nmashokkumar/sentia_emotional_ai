import os
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# =============================
# CONFIG
# =============================
MODEL_NAME = "emotionalsentiaai/finetuned_emotion_detector"
LOCAL_PATH = "models/emotion_model"

LABELS = ["happy", "sad", "angry", "anxious", "lonely", "neutral", "stressed"]


# =============================
# LOAD MODEL (AUTO DOWNLOAD)
# =============================
def load_model():
    if not os.path.exists(LOCAL_PATH):
        print("Downloading emotion model...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

        os.makedirs(LOCAL_PATH, exist_ok=True)
        tokenizer.save_pretrained(LOCAL_PATH)
        model.save_pretrained(LOCAL_PATH)
    else:
        print("Loading emotion model from cache...")

    tokenizer = AutoTokenizer.from_pretrained(LOCAL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(LOCAL_PATH)

    return tokenizer, model


tokenizer, model = load_model()
model.eval()


# =============================
# RULE-BASED KEYWORDS
# =============================
EMOTION_KEYWORDS = {
    "happy": ["happy", "good", "great", "nice", "awesome", "love", "excited"],
    "sad": ["sad", "low", "down", "upset", "cry", "crying", "bad day"],
    "angry": ["angry", "mad", "pissed", "irritated", "annoyed", "frustrated"],
    "anxious": ["anxious", "nervous", "worried", "scared", "fear"],
    "lonely": ["lonely", "alone", "no one", "nobody"],
    "stressed": ["stress", "stressed", "pressure", "overwhelmed", "deadline"]
}


COMMON_PHRASES = [
    "hi", "hello", "hey",
    "how are you", "what are you doing",
    "ok", "okay", "fine", "hmm"
]


# =============================
# EMOTION DETECTION
# =============================
def detect_emotion(text):
    text_clean = text.lower().strip()

    # -----------------------------------
    # 1. KEYWORD MATCH (HIGH PRIORITY)
    # -----------------------------------
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for word in keywords:
            if word in text_clean:
                return emotion, 0.9

    # -----------------------------------
    # 2. COMMON PHRASES (NEUTRAL)
    # -----------------------------------
    for phrase in COMMON_PHRASES:
        if phrase in text_clean:
            return "neutral", 0.95

    # -----------------------------------
    # 3. SHORT TEXT SAFETY
    # -----------------------------------
    if len(text_clean.split()) <= 2:
        return "neutral", 0.6

    # -----------------------------------
    # 4. MODEL (DISTILBERT)
    # -----------------------------------
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    confidence, pred = torch.max(probs, dim=1)

    emotion = LABELS[pred.item()]
    confidence = round(confidence.item(), 3)

    # -----------------------------------
    # 5. LOW CONFIDENCE FIX
    # -----------------------------------
    if confidence < 0.4:
        return "neutral", confidence

    return emotion, confidence