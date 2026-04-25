"""
topic_extractor.py
Extracts candidate topics using HuggingFace InferenceClient (chat completions).
Uses the new HuggingFace Inference Providers API (2025).
"""

import os
import json
from huggingface_hub import InferenceClient


def get_client() -> InferenceClient:
    api_key = os.environ.get("HF_API_KEY")
    if not api_key:
        raise EnvironmentError("HF_API_KEY not set. Please add it to your .env file.")
    return InferenceClient(
        provider="novita",
        api_key=api_key,
    )


def query_hf(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """Send a chat message to HuggingFace and return the response text."""
    client = get_client()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )

    return completion.choices[0].message.content.strip()


def extract_topics(combined_text: str, max_topics: int = 15) -> list:
    """Extract key topics from document text using HuggingFace LLM."""

    words = combined_text.split()
    if len(words) > 3000:
        combined_text = " ".join(words[:3000]) + "\n[...truncated...]"

    system_prompt = (
        "You are a content analyst. Extract discussion topics from documents. "
        "Always respond with ONLY a valid JSON array of strings. "
        "No explanation, no markdown, no extra text."
    )

    user_prompt = f"""Read this document and extract the {max_topics} most important topics suitable for a podcast discussion.
Each topic must be a clear phrase of 3-8 words.
Return ONLY a JSON array like: ["Topic One", "Topic Two", "Topic Three"]

Document:
{combined_text}"""

    raw = query_hf(system_prompt, user_prompt, max_tokens=600)

    # Clean markdown fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            topics = json.loads(raw[start:end])
            if isinstance(topics, list) and len(topics) > 0:
                return [str(t).strip() for t in topics if t]
    except json.JSONDecodeError:
        pass

    # Fallback: line by line
    lines = raw.replace("[", "").replace("]", "").split("\n")
    topics = [l.strip().strip('",').strip() for l in lines if len(l.strip()) > 3]
    if topics:
        return topics[:max_topics]

    raise ValueError(f"Could not parse topics from response: {raw[:200]}")


def validate_manual_topics(
    manual_topics: list,
    combined_text: str,
    extracted_topics: list,
) -> dict:
    """Check which manually entered topics exist in the documents."""

    if not manual_topics:
        return {"included": [], "ignored": []}

    words = combined_text.split()
    if len(words) > 2000:
        combined_text = " ".join(words[:2000]) + "\n[...truncated...]"

    system_prompt = (
        "You are a content relevance checker. "
        "Respond ONLY with valid JSON. No explanation, no markdown."
    )

    user_prompt = f"""Check which of these topics are relevant to the document below.

Document excerpt:
{combined_text[:1500]}

Topics to check:
{json.dumps(manual_topics)}

Return ONLY this JSON format:
{{"included": ["topics found in doc"], "ignored": ["topics not found"]}}"""

    try:
        raw = query_hf(system_prompt, user_prompt, max_tokens=300)
        raw = raw.replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        result = json.loads(raw[start:end])
        return {
            "included": result.get("included", []),
            "ignored": result.get("ignored", manual_topics),
        }
    except Exception:
        return {"included": [], "ignored": manual_topics}
