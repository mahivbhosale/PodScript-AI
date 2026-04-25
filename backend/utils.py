"""
utils.py
Helper utilities for word count estimation, duration calculation, and validation.
"""


def estimate_word_count(duration_minutes: int, speaking_speed_host: int, speaking_speed_guest: int) -> int:
    """
    Estimate total word count for a podcast script based on duration and speaking speeds.

    Speaking speed scale: 50 (slow) → 150 (fast)
    Average human speaking speed ≈ 130 words per minute.
    We map the 50–150 scale linearly to 100–160 wpm.
    """
    def scale_to_wpm(speed: int) -> int:
        # Map 50–150 → 100–160 wpm
        return int(100 + ((speed - 50) / 100) * 60)

    host_wpm = scale_to_wpm(speaking_speed_host)
    guest_wpm = scale_to_wpm(speaking_speed_guest)
    avg_wpm = (host_wpm + guest_wpm) / 2

    # Both speakers share the total speaking time
    total_words = int(avg_wpm * duration_minutes)
    return total_words


def estimate_duration_from_words(word_count: int, avg_speed: int = 100) -> float:
    """Estimate duration in minutes given a word count and average speed."""
    wpm = int(100 + ((avg_speed - 50) / 100) * 60)
    return round(word_count / wpm, 1)


def validate_inputs(
    host_name: str,
    guest_name: str,
    host_gender: str,
    guest_gender: str,
    host_speed: int,
    guest_speed: int,
    duration: int,
    documents: list,
) -> list[str]:
    """
    Validate all mandatory inputs.
    Returns a list of error messages (empty if all valid).
    """
    errors = []

    if not host_name or not host_name.strip():
        errors.append("Host Name is required.")
    if not guest_name or not guest_name.strip():
        errors.append("Guest Name is required.")
    if host_gender not in ("male", "female"):
        errors.append("Host Gender must be 'male' or 'female'.")
    if guest_gender not in ("male", "female"):
        errors.append("Guest Gender must be 'male' or 'female'.")
    if not (50 <= host_speed <= 150):
        errors.append("Host Speaking Speed must be between 50 and 150.")
    if not (50 <= guest_speed <= 150):
        errors.append("Guest Speaking Speed must be between 50 and 150.")
    if duration not in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]:
        errors.append("Duration must be one of: 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60 minutes.")
    if not documents or len(documents) == 0:
        errors.append("At least one document (PDF, DOCX, or TXT) must be uploaded.")

    return errors


def format_speaker_style(name: str, gender: str, speed: int) -> str:
    """
    Return a natural language description of a speaker's style for LLM prompting.
    """
    pace = (
        "speaks slowly and deliberately, taking pauses to emphasize points"
        if speed < 75
        else "speaks at a moderate, comfortable pace"
        if speed < 115
        else "speaks quickly and energetically, full of enthusiasm"
    )
    pronoun = "He" if gender == "male" else "She"
    return f"{name} ({pronoun}/{pronoun.lower()}): {pronoun} {pace}."


def chunk_text(text: str, max_words: int = 3000) -> list[str]:
    """Split a large text into chunks of max_words for LLM processing."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i:i + max_words]))
    return chunks
