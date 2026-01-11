"""
Gemini 2.5 Flash integration helpers for blog analysis and prompt-driven HTML generation.
[cite: 2025-12-23]
"""

import importlib
import asyncio
import json
import logging
import os

try:
    genai = importlib.import_module("google.genai")
except ModuleNotFoundError:
    genai = importlib.import_module("google_genai")

LOGGER = logging.getLogger("gemini_service")

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_MODEL = os.getenv("GENAI_MODEL_NAME", "gemini-2.5-flash")

if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
else:
    LOGGER.warning("GENAI_API_KEY not configured; Gemini calls will fail.")


async def _call_chat(messages: list[dict]) -> str:
    def sync_call():
        response = genai.chat.completions.create(model=GENAI_MODEL, messages=messages, temperature=0.3)
        candidate = response.candidates[0]
        return candidate.content if hasattr(candidate, "content") else candidate.message.content

    try:
        return await asyncio.to_thread(sync_call)
    except Exception as exc:
        LOGGER.error("Gemini request failed: %s", exc)
        raise


async def analyze_blog(blog_url: str, alias: str | None) -> dict:
    """
    Analyze the given blog URL using Gemini and return category + prompt recommendations.
    """
    description = alias or blog_url
    messages = [
        {
            "role": "system",
            "content": "You are AI Ops that understands blog niches. Respond in JSON: {'category': str, 'prompt': str}.",
        },
        {
            "role": "user",
            "content": (
                f"Analyze this blog and suggest an optimal category plus a writing prompt that "
                f"optimizes SEO. URL/alias: {description}. Answer only the JSON object."
            ),
        },
    ]
    raw = await _call_chat(messages)
    try:
        data = json.loads(raw)
        return {"category": data.get("category", description), "prompt": data.get("prompt", "Write a post about " + description)}
    except json.JSONDecodeError:
        LOGGER.warning("Gemini analyze response not JSON; using fallback.")
        return {"category": description, "prompt": raw.strip()}


async def generate_html(topic: str, persona: str, prompt: str | None, word_count_range: tuple[int, int], image_count: int) -> dict:
    """
    Generate SEO-optimized HTML snippet based on topic, persona, and custom prompt.
    """
    min_words, max_words = word_count_range
    prompt_text = prompt or f"Write an SEO-optimized blog introduction for {topic} with persona {persona}."
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional editor. Respond in JSON with 'html' (string) and 'summary' (string). "
                "Stick to HTML tags for structure."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate HTML content for topic: {topic}. Persona: {persona}. "
                f"Use prompt: {prompt_text}. Aim for between {min_words} and {max_words} words. "
                f"Include a brief summary describing the SEO angle. Mention there will be {image_count} images."
            ),
        },
    ]
    raw = await _call_chat(messages)
    try:
        data = json.loads(raw)
        return {
            "html": data.get("html", raw),
            "summary": data.get("summary", ""),
        }
    except json.JSONDecodeError:
        LOGGER.warning("Gemini HTML response not JSON; returning raw text.")
        return {"html": raw, "summary": raw[:120]}

