"""
script_generator.py
Core script generation using HuggingFace InferenceClient (chat completions).
Uses the new HuggingFace Inference Providers API (2025).
"""

import os
from huggingface_hub import InferenceClient
from .utils import estimate_word_count, format_speaker_style


def get_client() -> InferenceClient:
    api_key = os.environ.get("HF_API_KEY")
    if not api_key:
        raise EnvironmentError("HF_API_KEY not set. Please add it to your .env file.")
    return InferenceClient(
        provider="novita",
        api_key=api_key,
    )


def query_hf(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """Send a chat message and return the response."""
    client = get_client()

    completion = client.chat.completions.create(
        model="meta-llama/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=0.75,
    )

    return completion.choices[0].message.content.strip()


def generate_script(
    host_name,
    host_gender,
    host_speed,
    guest_name,
    guest_gender,
    guest_speed,
    selected_topics,
    combined_text,
    duration_minutes,
) -> str:
    """Generate a full podcast script using HuggingFace LLM."""

    target_words = estimate_word_count(duration_minutes, host_speed, guest_speed)
    host_style = format_speaker_style(host_name, host_gender, host_speed)
    guest_style = format_speaker_style(guest_name, guest_gender, guest_speed)

    words = combined_text.split()
    if len(words) > 3000:
        combined_text = " ".join(words[:3000]) + "\n[...content truncated...]"

    topics_str = "\n".join([f"{i+1}. {t}" for i, t in enumerate(selected_topics)])

    system_prompt = (
        "You are a professional podcast scriptwriter. "
        "You write natural, engaging, humanoid podcast conversations. "
        "Always write the complete script from opening to closing."
    )

    user_prompt = f"""Write a complete podcast script with these details:

HOST: {host_style}
GUEST: {guest_style}

TOPICS TO COVER:
{topics_str}

SOURCE MATERIAL (base all facts on this):
{combined_text}

REQUIREMENTS:
- Target length: {target_words} words (~{duration_minutes} minutes of audio)
- Format every line as: {host_name.upper()}: [what they say]  OR  {guest_name.upper()}: [what they say]
- Start with a warm opening where {host_name} introduces the show and welcomes {guest_name}
- Cover ALL topics above with smooth transitions between them
- End with a proper closing where {host_name} thanks {guest_name} and wraps up
- Use natural fillers like "um", "uh", "you know", "right" occasionally (not every line)
- Include reactions like "That's fascinating!", "Exactly!", "Wait, really?" to feel real
- Make it sound like a REAL human conversation with follow-up questions and reactions
- All facts must come strictly from the source material

Write the complete script now:"""

    return query_hf(system_prompt, user_prompt, max_tokens=2500)


def modify_script(
    existing_script,
    modification_request,
    host_name,
    guest_name,
    selected_topics,
    combined_text,
    duration_minutes,
    host_speed,
    guest_speed,
) -> str:
    """Regenerate the complete script with user's modifications."""

    target_words = estimate_word_count(duration_minutes, host_speed, guest_speed)
    topics_str = ", ".join(selected_topics)

    words = combined_text.split()
    if len(words) > 2000:
        combined_text = " ".join(words[:2000]) + "\n[...truncated...]"

    system_prompt = (
        "You are a professional podcast scriptwriter. "
        "Rewrite complete scripts based on user feedback. "
        "Always produce the full script from opening to closing."
    )

    user_prompt = f"""Rewrite this podcast script based on the modification request.

ORIGINAL SCRIPT (for reference):
{existing_script[:2500]}

MODIFICATION REQUEST:
{modification_request}

REQUIREMENTS:
- Rewrite the COMPLETE script from opening to closing
- Keep covering these topics: {topics_str}
- Target: {target_words} words (~{duration_minutes} minutes)
- Format: {host_name.upper()}: [dialogue]  OR  {guest_name.upper()}: [dialogue]
- Apply the requested changes throughout the whole script

Write the complete modified script now:"""

    return query_hf(system_prompt, user_prompt, max_tokens=2500)
