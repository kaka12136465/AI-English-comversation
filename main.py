import sys
import os
import re
import threading
import time
import webbrowser
from pathlib import Path

# ── Path handling (normal run vs PyInstaller bundle) ──────────────────────
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller .exe
    # _MEIPASS holds the extracted temp dir (static files live here)
    BUNDLE_DIR  = Path(sys._MEIPASS)
    # .env lives next to the .exe itself
    RUNTIME_DIR = Path(sys.executable).parent
else:
    BUNDLE_DIR  = Path(__file__).parent
    RUNTIME_DIR = Path(__file__).parent

# ── Load .env ─────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(RUNTIME_DIR / '.env')

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import anthropic
import json
from typing import List

app = FastAPI()
client = anthropic.Anthropic()

STATIC_DIR = BUNDLE_DIR / 'static'

SYSTEM_PROMPT = """You are a warm and encouraging English conversation partner and teacher.

CRITICAL: You MUST check EVERY single user message for English mistakes — not just the first one. Do this every time without exception.

For EACH user message, follow these steps:

STEP 1 - Error Check (REQUIRED EVERY TURN):
Carefully check the user's English for any mistakes, including:
- Grammar errors (verb tenses, subject-verb agreement, articles, prepositions)
- Spelling mistakes
- Wrong word choice or unnatural phrasing
- Punctuation issues

STEP 2 - Response Format:
If the user made ANY mistakes, start your response with EXACTLY this block:

---CORRECTION---
Original: [copy their exact text]
Corrected: [the corrected version]
Explanation: [brief, friendly explanation of the error(s)]
---END CORRECTION---

If there are NO mistakes, do NOT include any correction block.

STEP 3 - Conversation:
After the correction block (if any), respond naturally and engagingly. Ask a follow-up question to keep the conversation flowing.

Rules:
- Be warm, encouraging, and supportive
- Keep explanations simple and clear
- ALWAYS perform the error check, even on the 2nd, 3rd, 4th message and beyond"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message]


@app.get("/", response_class=HTMLResponse)
async def root():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/chat")
async def chat(request: ChatRequest):
    corr_re = re.compile(r'---CORRECTION---[\s\S]*?---END CORRECTION---', re.MULTILINE)
    messages = [{"role": m.role, "content": corr_re.sub('', m.content).strip()} for m in request.history]
    messages.append({"role": "user", "content": request.message})

    def generate():
        try:
            with client.messages.stream(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8000")

    threading.Thread(target=open_browser, daemon=True).start()

    print("=" * 50)
    print("  AI English Voice Coach")
    print("  Starting server at http://localhost:8000")
    print("  Browser will open automatically.")
    print("  Close this window to stop the app.")
    print("=" * 50)

    uvicorn.run(app, host="127.0.0.1", port=8000)
