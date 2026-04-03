# AI English Voice Coach

An AI-powered English conversation app that helps you practice speaking English through real-time voice interaction. Mistakes are corrected in text — not read aloud — so the conversation flows naturally.

## Features

- **Voice conversation** — speak English using your microphone; the AI responds with synthesized speech
- **Grammar correction** — mistakes are detected and shown as text correction cards (not spoken)
- **TTS pronunciation helper** — replay your own message with correct pronunciation via text-to-speech
- **Replay audio** — replay both your last message and the AI's last response at any time
- **Session timer** — tracks how long you've been practicing
- **Auto-capitalize** — first letter of your input is automatically capitalized
- **Voice selector** — choose from available system voices (natural/online voices prioritized)
- **Cancel recording** — discard a recording mid-session without sending

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Server-Sent Events (SSE) |
| AI | Anthropic Claude Haiku (`claude-haiku-4-5`) |
| Speech-to-Text | Web Speech API (`SpeechRecognition`) |
| Text-to-Speech | Web Speech API (`speechSynthesis`) |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Packaging | PyInstaller (`.exe` for Windows) |

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kaka12136465/AI-English-comversation.git
   cd AI-English-comversation
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Run the app**
   ```bash
   python main.py
   ```
   The browser will open automatically at `http://localhost:8000`.

## Build as Windows .exe

```bat
build.bat
```

The `.exe` will be output to the `dist/` folder. Copy your `.env` file next to the `.exe` before running.

## How to Use

1. Select a voice from the dropdown in the top bar
2. Click the microphone button to start recording
3. Speak in English, then click the microphone again to stop
4. The AI responds via voice; any corrections appear as cards below
5. Use the replay buttons (🔊) to replay your message or the AI's response
6. Use the pronunciation button to hear your own text read back correctly

## Project Structure

```
.
├── main.py          # FastAPI server + Claude API integration
├── requirements.txt
├── build.bat        # PyInstaller build script
└── static/
    └── index.html   # Single-page frontend (UI + all JS/CSS)
```

## Notes

- A microphone and speakers (or headphones) are required
- Voice recognition quality depends on your browser and system (Chrome recommended)
- The `.env` file contains your API key — never commit it to version control
