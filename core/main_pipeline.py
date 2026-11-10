from core.emotion import detect_emotion
from core.context_builder import build_context
from core.llm_engine import generate_response
from memory.memory import store_memory, retrieve_memory


def run_pipeline(user_text, emotion=None, confidence=None):

    print("\n[MAIN PIPELINE] Running...")

    # -----------------------------
    # 1. Emotion Handling
    # -----------------------------
    if emotion is None or confidence is None:
        emotion, confidence = detect_emotion(user_text)
        print("[EMOTION - TEXT]:", emotion, confidence)
    else:
        print("[EMOTION - FROM VOICE]:", emotion, confidence)

    # -----------------------------
    # 2. Retrieve Memory
    # -----------------------------
    if user_text and user_text.strip():
        memory = retrieve_memory(user_text)
    else:
        memory = []

    print("[MEMORY RETRIEVED]:", len(memory), "items")

    # Optional: show memory preview
    for i, m in enumerate(memory[:2], 1):
        print(f"[MEM {i}] User:", m["user"])
        print(f"[MEM {i}] Bot :", m["response"])

    # -----------------------------
    # 3. Context Builder
    # -----------------------------
    prompt = build_context(user_text, emotion, confidence, memory)

    print("[CONTEXT BUILT]")

    # -----------------------------
    # 4. LLM Response
    # -----------------------------
    response = generate_response(prompt)

    print("[LLM GENERATED]")

    # -----------------------------
    # 5. Store Memory
    # -----------------------------
    store_memory(user_text, response, emotion)

    print("[MEMORY STORED]")

    # -----------------------------
    # 6. Return
    # -----------------------------
    return {
        "response": response,
        "emotion": emotion,
        "confidence": confidence
    }