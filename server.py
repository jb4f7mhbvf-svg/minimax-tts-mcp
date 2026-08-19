python
"""
MiniMax TTS MCP Server
A lightweight MCP server that gives AI the ability to speak.
Converts text to speech using MiniMax API and returns playable audio URLs.
"""

from flask import Flask, request, jsonify, send_file
import requests as req
import binascii
import tempfile
import uuid
import os

app = Flask(__name__)

# Configuration via environment variables
API_KEY = os.environ.get("MINIMAX_API_KEY", "")
VOICE_ID = os.environ.get("MINIMAX_VOICE_ID", "")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")


def generate_audio(text, emotion="neutral", speed=0.9, language="Chinese,Yue", voice_id=None):
    """Call MiniMax TTS API and return saved filepath + filename."""
    if not API_KEY:
        raise ValueError("MINIMAX_API_KEY not set")

    r = req.post(
        "https://api.minimaxi.com/v1/t2a_v2",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "speech-2.8-hd",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id or VOICE_ID,
                "speed": speed,
                "vol": 1,
                "pitch": 0,
                "emotion": emotion,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
            "language_boost": language,
        },
    )

    result = r.json()
    if result.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError(f"MiniMax API error: {result}")

    audio_hex = result["data"]["audio"]
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = f"/tmp/{filename}"
    with open(filepath, "wb") as f:
        f.write(binascii.unhexlify(audio_hex))

    return filepath, filename


# --- Direct TTS endpoint ---

@app.route("/tts", methods=["POST"])
def tts():
    """Direct TTS endpoint. POST JSON with 'text' field, get back mp3."""
    data = request.json
    text = data.get("text", "")
    voice_id = data.get("voice_id", VOICE_ID)
    emotion = data.get("emotion", "neutral")
    speed = data.get("speed", 0.9)
    language = data.get("language", "Chinese,Yue")

    try:
        filepath, _ = generate_audio(text, emotion, speed, language, voice_id)
        return send_file(filepath, mimetype="audio/mpeg", as_attachment=True, download_name="output.mp3")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Audio file serving ---

@app.route("/audio/<filename>", methods=["GET"])
def serve_audio(filename):
    """Serve generated audio files."""
    filepath = f"/tmp/{filename}"
    if not os.path.exists(filepath):
        return jsonify({"error": "file not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg")


# --- MCP Protocol endpoint ---

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    """MCP (Model Context Protocol) endpoint for AI tool integration."""
    body = request.json
    method = body.get("method", "")
    req_id = body.get("id", 1)

    if method == "initialize":
        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "minimax-tts-mcp", "version": "1.0.0"},
            },
        })

    elif method == "tools/list":
        return jsonify({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_speech",
                        "description": "Generate speech audio from text using MiniMax TTS. Returns a URL to the generated mp3 file.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Text to speak"},
                                "emotion": {
                                    "type": "string",
                                    "description": "Emotion: neutral, happy, sad, angry, fearful, surprised, disgusted",
                                },
                                "speed": {"type": "number", "description": "Speed 0.5-2.0, default 0.9"},
                                "language": {
                                    "type": "string",
                                    "description": "Language boost, e.g. 'Chinese,Yue' for Cantonese, 'Chinese,Wuu' for Shanghainese",
                                },
                            },
                            "required": ["text"],
                        },
                    }
                ]
            },
        })

    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name", "")
        args = params.get("arguments", {})

        if tool_name == "generate_speech":
            try:
                text = args.get("text", "")
                emotion = args.get("emotion", "neutral")
                speed = args.get("speed", 0.9)
                language = args.get("language", "Chinese,Yue")

                _, filename = generate_audio(text, emotion, speed, language)
                audio_url = f"{BASE_URL}/audio/{filename}"

                return jsonify({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": audio_url}]},
                })
            except Exception as e:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Error: {e}"}]},
                })

    return jsonify({"jsonrpc": "2.0", "id": req_id, "result": {}})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
