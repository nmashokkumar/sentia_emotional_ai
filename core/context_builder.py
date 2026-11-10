def build_context(user_text, emotion, confidence, memory=None):

    tone_map = {
        "happy": "sound cheerful and friendly",
        "sad": "sound gentle and understanding",
        "angry": "stay calm and grounding",
        "anxious": "be reassuring and steady",
        "lonely": "sound warm and present",
        "stressed": "sound calming and supportive",
        "neutral": "sound like a normal friendly chat"
    }

    tone = tone_map.get(emotion, "sound natural")

    memory_block = ""
    if memory:
        for m in memory[:2]:
            memory_block += f"User: {m['user']}\nYou: {m['response']}\n"

    prompt = f"""
You are Sentia.

Talk like a real person in a casual conversation.
Use small natural expressions like "yeah", "I get that", or "it can feel like that" when it fits.
Let your response feel like one smooth thought, not separate short sentences.
Use very simple, everyday spoken English. Avoid formal or poetic phrases.
Prefer natural phrases like "it can feel a lot", "that’s tough", "you’ll be okay" instead of formal wording.

Tone: {tone}

{memory_block}

User: {user_text}
You:
"""

    return prompt.strip()