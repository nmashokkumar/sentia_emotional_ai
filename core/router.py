from core.voice_pipeline import voice_pipeline
from core.main_pipeline import run_pipeline


def route_input(message, input_type):

    print(f"\n[ROUTER] Input Type : {input_type}")
    print(f"[ROUTER] Message    : {message}")

    # -----------------------------
    # TEXT INPUT
    # -----------------------------
    if input_type == "text":
        print("[TEXT → MAIN PIPELINE]")
        return run_pipeline(message)

    # -----------------------------
    # VOICE INPUT
    # -----------------------------
    elif input_type == "voice":
        print("[VOICE → MAIN PIPELINE]")

        voice_result = voice_pipeline("temp.wav")

        result = run_pipeline(
            user_text=voice_result["text"],
            emotion=voice_result["emotion"],
            confidence=voice_result["confidence"]
        )

        return result

    # -----------------------------
    # SAFETY
    # -----------------------------
    else:
        return run_pipeline(message)