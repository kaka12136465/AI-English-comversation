"""
Firebase Cloud Functions (Python gen2) — AI English Voice Coach
Handles /chat (SSE streaming) and /generate (sentence generation).

Deploy:
  firebase deploy --only functions

Set the Anthropic API key before deploying:
  Create  functions/.env  containing:
    ANTHROPIC_API_KEY=sk-ant-api03-...
"""

import os
import re
import json
import anthropic
from flask import Response
from firebase_functions import https_fn
from firebase_functions.options import CorsOptions

# ── Anthropic client ──────────────────────────────────────────────────────────
# API key is loaded from functions/.env (local) or Cloud Run env var (production)
def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


# ── System prompt ─────────────────────────────────────────────────────────────
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


# ── CORS ──────────────────────────────────────────────────────────────────────
_CORS = CorsOptions(
    cors_origins=["*"],
    cors_methods=["GET", "POST", "OPTIONS"],
)


# ── /chat — SSE streaming conversation ───────────────────────────────────────
@https_fn.on_request(region="asia-northeast1", cors=_CORS)
def chat(req: https_fn.Request) -> https_fn.Response:
    if req.method == "OPTIONS":
        return ("", 204)

    data = req.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return Response(
            json.dumps({"error": "message is required"}),
            status=400,
            mimetype="application/json",
        )

    corr_re = re.compile(r"---CORRECTION---[\s\S]*?---END CORRECTION---")
    messages = [
        {
            "role": m["role"],
            "content": corr_re.sub("", m["content"]).strip(),
        }
        for m in history
    ]
    messages.append({"role": "user", "content": message})

    def stream_chat():
        try:
            with _client().messages.stream(
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

    return Response(
        stream_chat(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── /generate — AI sentence generation ───────────────────────────────────────
@https_fn.on_request(region="asia-northeast1", cors=_CORS)
def generate(req: https_fn.Request) -> https_fn.Response:
    if req.method == "OPTIONS":
        return ("", 204)

    data = req.get_json(force=True, silent=True) or {}
    difficulty = data.get("difficulty", "Medium")
    topic = data.get("topic", "").strip()
    count = min(max(int(data.get("count", 5)), 1), 10)

    difficulty_guide = {
        "Easy":   "Simple vocabulary, present/past tense, short sentences (8–12 words).",
        "Medium": "Varied grammar, multiple clauses, moderate length (12–20 words).",
        "Hard":   "Advanced vocabulary, complex structures, longer sentences (20+ words).",
    }.get(difficulty, "")

    topic_line = f"Topic: {topic}" if topic else "Topic: general everyday conversation"
    prompt = (
        f"Generate exactly {count} English sentences for speaking practice.\n"
        f"Difficulty: {difficulty} — {difficulty_guide}\n"
        f"{topic_line}\n\n"
        "Return ONLY a valid JSON array of strings, with no extra text.\n"
        'Example: ["Sentence one.", "Sentence two."]'
    )

    try:
        response = _client().messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        sentences = json.loads(raw)
        if not isinstance(sentences, list):
            raise ValueError("Response is not a list")
        result = {"sentences": [str(s) for s in sentences]}
    except Exception as e:
        result = {"error": str(e)}

    return Response(json.dumps(result), mimetype="application/json")
