def text_pipeline(message):

    print("[TEXT PIPELINE] Running...")

    return {
        "response": f"(text pipeline) You said: {message}",
        "emotion": "neutral",
        "confidence": 0.7
    }