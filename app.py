from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import tempfile

# 🔥 IMPORT ROUTER
from core.router import route_input

app  = Flask(__name__)
CORS(app)

WAV_PATH = "temp.wav"


# ─────────────────────────────────────────────────────
# HELPER: convert any audio format → 16-bit mono WAV
# Uses ffmpeg (must be installed & on PATH)
# ─────────────────────────────────────────────────────
def convert_to_wav(input_path: str, output_path: str) -> bool:
    """
    Convert input_path (webm / ogg / mp4 / etc.) to
    16 kHz mono 16-bit PCM WAV at output_path.
    Returns True on success, False on failure.
    """
    try:
        cmd = [
            "ffmpeg", "-y",           # overwrite output
            "-i", input_path,         # input file
            "-ar", "16000",           # sample rate 16 kHz
            "-ac", "1",               # mono
            "-sample_fmt", "s16",     # 16-bit PCM
            output_path               # output WAV
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        if result.returncode != 0:
            print("[FFMPEG ERROR]", result.stderr.decode())
            return False
        print("[FFMPEG] Conversion successful →", output_path)
        return True
    except FileNotFoundError:
        print("[FFMPEG] ffmpeg not found on PATH. Please install ffmpeg.")
        return False
    except subprocess.TimeoutExpired:
        print("[FFMPEG] Conversion timed out.")
        return False
    except Exception as e:
        print("[FFMPEG] Unexpected error:", e)
        return False


# ─────────────────────────────────────────────────────
# POST /chat
# ─────────────────────────────────────────────────────
@app.route('/chat', methods=['POST'])
def chat():

    try:

        # ─────────────────────────────
        # VOICE INPUT  (multipart form)
        # ─────────────────────────────
        if request.content_type and request.content_type.startswith("multipart/form-data"):

            print("\n[SENTIA] Input Type : voice")

            audio_file = request.files.get("audio")
            transcript = request.form.get("transcript", "").strip()
            history_raw = request.form.get("history", "[]")

            if not audio_file:
                return jsonify({"error": "No audio received"}), 400

            print(f"[SENTIA] Transcript  : {transcript}")
            print(f"[SENTIA] Audio file  : {audio_file.filename}, type={audio_file.content_type}")

            # ── Save raw audio to a temp file with correct extension ──
            original_filename = audio_file.filename or "recording.webm"
            ext = os.path.splitext(original_filename)[-1].lower()
            if ext not in ('.webm', '.ogg', '.mp4', '.wav', '.mp3'):
                ext = '.webm'   # safe default

            # Use a proper temp file for the raw upload
            raw_fd, raw_path = tempfile.mkstemp(suffix=ext)
            os.close(raw_fd)

            try:
                audio_file.save(raw_path)
                print(f"[RAW AUDIO SAVED]: {raw_path}")

                # ── Convert to WAV if not already WAV ──
                if ext == '.wav':
                    # Already WAV — copy directly
                    import shutil
                    shutil.copy(raw_path, WAV_PATH)
                    print("[WAV] Input was already WAV, copied directly.")
                    wav_ok = True
                else:
                    wav_ok = convert_to_wav(raw_path, WAV_PATH)

                if not wav_ok:
                    # Conversion failed — fall back to text-only pipeline
                    print("[WARNING] Audio conversion failed. Running text-only pipeline.")
                    result = route_input(transcript, "text") if transcript else {
                        "response": "I had trouble processing your voice. Could you try again?",
                        "emotion": "neutral",
                        "confidence": 0.5
                    }
                else:
                    print("[VOICE SAVED]: temp.wav")
                    # Pass transcript so router can skip STT and use it directly
                    result = route_input(transcript, "voice")

            finally:
                # Always clean up raw temp file
                if os.path.exists(raw_path):
                    os.remove(raw_path)
                    print(f"[RAW TEMP DELETED]: {raw_path}")

            # Clean up WAV
            if os.path.exists(WAV_PATH):
                os.remove(WAV_PATH)
                print("[TEMP FILE DELETED]")

        # ─────────────────────────────
        # TEXT INPUT  (JSON body)
        # ─────────────────────────────
        else:

            data = request.get_json()

            if not data:
                return jsonify({"error": "No JSON body received"}), 400

            message    = data.get("message", "").strip()
            input_type = data.get("input_type", "text")
            history    = data.get("history", [])

            print(f"\n[SENTIA] Input Type : {input_type}")
            print(f"[SENTIA] Message    : {message}")
            print(f"[SENTIA] History    : {len(history)} messages so far")

            result = route_input(message, input_type)

        # ─────────────────────────────
        # BUILD RESPONSE
        # ─────────────────────────────
        response_payload = {
            "response": result["response"],
            "emotion": {
                "name":        result["emotion"],
                "icon":        "fa-meh",
                "color":       "#8B5FBF",
                "description": result["emotion"],
                "confidence":  int(result["confidence"] * 100)
            }
        }

        print(f"[SENTIA] LLM Response : {result['response']}")
        print(f"[SENTIA] Emotion      : {result['emotion']} ({int(result['confidence'] * 100)}%)")

        return jsonify(response_payload), 200

    except Exception as e:
        import traceback
        print("[ERROR]", str(e))
        traceback.print_exc()
        return jsonify({
            "error":   "Internal server error",
            "details": str(e)
        }), 500


# ─────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "SENTIA backend is running"}), 200


# ─────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 45)
    print("  SENTIA Backend Running")
    print("  URL  : http://127.0.0.1:5000")
    print("  Chat : POST http://127.0.0.1:5000/chat")
    print("=" * 45)
    app.run(debug=True, host='127.0.0.1', port=5000)
