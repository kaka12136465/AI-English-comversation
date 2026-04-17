/**
 * Firebase Cloud Functions (gen1 / Node.js 20)
 * AI English Voice Coach — /chat (SSE) + /generate
 *
 * Set API key before deploying:
 *   Create  functions/.env  with:
 *     ANTHROPIC_API_KEY=sk-ant-api03-...
 *   Then run:
 *     firebase deploy --only functions
 */

"use strict";

const functions  = require("firebase-functions");
const Anthropic  = require("@anthropic-ai/sdk");

// ── Anthropic client ───────────────────────────────────────────────────────
const getClient = () =>
  new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

// ── System prompt ──────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are a warm and encouraging English conversation partner and teacher.

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
- ALWAYS perform the error check, even on the 2nd, 3rd, 4th message and beyond`;

// ── Shared CORS headers ────────────────────────────────────────────────────
const CORS = {
  "Access-Control-Allow-Origin":  "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

// ── /chat — SSE streaming conversation ────────────────────────────────────
exports.chat = functions
  .region("asia-northeast1")
  .runWith({ timeoutSeconds: 60, memory: "256MB" })
  .https.onRequest(async (req, res) => {
    Object.entries(CORS).forEach(([k, v]) => res.set(k, v));

    if (req.method === "OPTIONS") {
      res.status(204).send("");
      return;
    }

    const { message, history = [] } = req.body;
    if (!message) {
      res.status(400).json({ error: "message is required" });
      return;
    }

    const corrRe = /---CORRECTION---[\s\S]*?---END CORRECTION---/g;
    const messages = [
      ...history.map((m) => ({
        role: m.role,
        content: m.content.replace(corrRe, "").trim(),
      })),
      { role: "user", content: message },
    ];

    res.set("Content-Type",    "text/event-stream");
    res.set("Cache-Control",   "no-cache");
    res.set("X-Accel-Buffering", "no");
    res.set("Connection",      "keep-alive");

    try {
      const stream = getClient().messages.stream({
        model:      "claude-haiku-4-5",
        max_tokens: 1024,
        system:     SYSTEM_PROMPT,
        messages,
      });

      stream.on("text", (text) => {
        res.write(`data: ${JSON.stringify({ text })}\n\n`);
      });

      await stream.finalMessage();
      res.write(`data: ${JSON.stringify({ done: true })}\n\n`);
    } catch (err) {
      res.write(`data: ${JSON.stringify({ error: err.message })}\n\n`);
    }

    res.end();
  });

// ── /generate — AI sentence generation ────────────────────────────────────
exports.generate = functions
  .region("asia-northeast1")
  .runWith({ timeoutSeconds: 60, memory: "256MB" })
  .https.onRequest(async (req, res) => {
    Object.entries(CORS).forEach(([k, v]) => res.set(k, v));

    if (req.method === "OPTIONS") {
      res.status(204).send("");
      return;
    }

    const { difficulty = "Medium", topic = "", count = 5 } = req.body;
    const safeCount = Math.min(Math.max(parseInt(count) || 5, 1), 10);

    const diffGuide = {
      Easy:   "Simple vocabulary, present/past tense, short sentences (8–12 words).",
      Medium: "Varied grammar, multiple clauses, moderate length (12–20 words).",
      Hard:   "Advanced vocabulary, complex structures, longer sentences (20+ words).",
    }[difficulty] || "";

    const topicLine = topic.trim()
      ? `Topic: ${topic}`
      : "Topic: general everyday conversation";

    const prompt = [
      `Generate exactly ${safeCount} English sentences for speaking practice.`,
      `Difficulty: ${difficulty} — ${diffGuide}`,
      topicLine,
      "",
      "Return ONLY a valid JSON array of strings, with no extra text.",
      'Example: ["Sentence one.", "Sentence two."]',
    ].join("\n");

    try {
      const response = await getClient().messages.create({
        model:      "claude-haiku-4-5",
        max_tokens: 600,
        messages:   [{ role: "user", content: prompt }],
      });

      let raw = response.content[0].text.trim();
      if (raw.startsWith("```")) {
        raw = raw.replace(/^```[a-z]*\n?/, "").replace(/\n?```$/, "");
      }

      const sentences = JSON.parse(raw);
      if (!Array.isArray(sentences)) throw new Error("Response is not an array");

      res.json({ sentences: sentences.map(String) });
    } catch (err) {
      res.status(500).json({ error: err.message });
    }
  });
