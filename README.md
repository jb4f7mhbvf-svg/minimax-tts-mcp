# minimax-tts-mcp

A lightweight MCP (Model Context Protocol) server that gives AI the ability to speak. Text in, audio URL out.

Built with Flask + [MiniMax TTS API](https://www.minimaxi.com/).

## What it does

- Exposes a `generate_speech` tool via MCP protocol
- AI sends text → server calls MiniMax TTS → returns a playable mp3 URL
- Supports emotion control, speed adjustment, and language selection (Cantonese, Mandarin, etc.)

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/minimax-tts-mcp.git
cd minimax-tts-mcp
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your MiniMax API key and voice ID
```

Get your API key and voice ID from [MiniMax Platform](https://www.minimaxi.com/).

### 3. Run

```bash
python server.py
```

Server starts at `http://localhost:5000`.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/mcp` | POST | MCP protocol endpoint for AI tool calls |
| `/tts` | POST | Direct TTS — post JSON, get mp3 file |
| `/audio/<filename>` | GET | Serve generated audio files |
| `/health` | GET | Health check |

## MCP Integration

Add to your MCP client config:

```json
{
  "mcpServers": {
    "tts": {
      "url": "http://localhost:5000/mcp"
    }
  }
}
```

The server exposes one tool:

**`generate_speech`**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | yes | Text to speak |
| emotion | string | no | neutral, happy, sad, angry, fearful, surprised, disgusted |
| speed | number | no | 0.5 - 2.0 (default 0.9) |
| language | string | no | e.g. "Chinese,Yue" for Cantonese |

## Direct TTS Usage

```bash
curl -X POST http://localhost:5000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "speed": 1.0}' \
  --output speech.mp3
```

## Deploy

Works anywhere that runs Python — a VPS, cloud VM, or container. For public access, put it behind a reverse proxy (nginx/caddy) with HTTPS.

Example with systemd:

```bash
# /etc/systemd/system/tts-mcp.service
[Unit]
Description=MiniMax TTS MCP Server

[Service]
WorkingDirectory=/path/to/minimax-tts-mcp
EnvironmentFile=/path/to/minimax-tts-mcp/.env
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Notes

- Generated audio files are stored in `/tmp` and not auto-cleaned. For production, add a cron job or cleanup logic.
- MiniMax API is a paid service. Check their pricing for TTS usage.
- Voice cloning requires setting up a custom voice on MiniMax platform first.

## License

MIT
