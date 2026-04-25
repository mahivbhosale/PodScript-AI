"""
cli.py — Command Line Interface for Podcast Script Generator
Run with: python cli.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.document_parser import parse_multiple_documents
from backend.topic_extractor import extract_topics, validate_manual_topics
from backend.script_generator import generate_script, modify_script
from backend.utils import validate_inputs, estimate_word_count


def prompt(text, default=None):
    val = input(text).strip()
    if not val and default is not None:
        return default
    return val


def prompt_choice(text, choices):
    while True:
        val = input(text).strip().lower()
        if val in choices:
            return val
        print(f"  ❌ Please enter one of: {', '.join(choices)}")


def prompt_int(text, min_val, max_val, default=None):
    while True:
        raw = input(text).strip()
        if not raw and default is not None:
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  ❌ Must be between {min_val} and {max_val}.")
        except ValueError:
            print("  ❌ Please enter a valid number.")


def main():
    print("\n" + "="*60)
    print("  🎙️  PODCAST SCRIPT GENERATOR  —  CLI Mode")
    print("="*60 + "\n")

    # ── Step 1: Speaker Info ──────────────────────────────────────
    print("── STEP 1: SPEAKER INFORMATION ──\n")

    host_name = prompt("Host Name: ")
    while not host_name:
        print("  ❌ Host name is required.")
        host_name = prompt("Host Name: ")

    host_gender = prompt_choice("Host Gender (male/female): ", ["male", "female"])
    host_speed = prompt_int("Host Speaking Speed (50–150): ", 50, 150, default=100)

    guest_name = prompt("Guest Name: ")
    while not guest_name:
        print("  ❌ Guest name is required.")
        guest_name = prompt("Guest Name: ")

    guest_gender = prompt_choice("Guest Gender (male/female): ", ["male", "female"])
    guest_speed = prompt_int("Guest Speaking Speed (50–150): ", 50, 150, default=100)

    # ── Step 2: Documents ─────────────────────────────────────────
    print("\n── STEP 2: DOCUMENT UPLOAD ──\n")
    print("Enter file paths (one per line). Supported: .pdf, .docx, .txt")
    print("Press Enter on an empty line when done.\n")

    file_paths = []
    while True:
        fp = input(f"File {len(file_paths)+1} path (or Enter to finish): ").strip()
        if not fp:
            if file_paths:
                break
            print("  ❌ At least one document is required.")
        else:
            if os.path.exists(fp):
                file_paths.append(fp)
                print(f"  ✅ Added: {fp}")
            else:
                print(f"  ❌ File not found: {fp}")

    # ── Step 3: Duration ──────────────────────────────────────────
    print("\n── STEP 3: DURATION ──\n")
    valid_durations = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
    print(f"Valid options: {valid_durations}")

    while True:
        dur_input = input("Target duration (minutes): ").strip()
        try:
            duration = int(dur_input)
            if duration in valid_durations:
                break
            print(f"  ❌ Must be one of: {valid_durations}")
        except ValueError:
            print("  ❌ Please enter a valid number.")

    target_words = estimate_word_count(duration, host_speed, guest_speed)
    print(f"\n  📝 Target script length: ~{target_words:,} words\n")

    # ── Parse Documents ───────────────────────────────────────────
    print("── PARSING DOCUMENTS... ──")
    try:
        parsed = parse_multiple_documents(file_paths)
        print(f"  ✅ Parsed {len(parsed['documents'])} document(s) | {parsed['total_words']:,} words")
        if parsed["errors"]:
            print("  ⚠️  Errors:")
            for e in parsed["errors"]:
                print(f"    - {e}")
    except Exception as e:
        print(f"  ❌ Failed to parse documents: {e}")
        sys.exit(1)

    # ── Extract Topics ────────────────────────────────────────────
    print("\n── EXTRACTING TOPICS... ──")
    try:
        topics = extract_topics(parsed["combined_text"])
        print(f"  ✅ Found {len(topics)} topics:\n")
        for i, t in enumerate(topics, 1):
            print(f"    {i:2}. {t}")
    except Exception as e:
        print(f"  ❌ Topic extraction failed: {e}")
        sys.exit(1)

    # ── Select Topics ─────────────────────────────────────────────
    print("\n── STEP 4: SELECT TOPICS ──")
    print("Enter topic numbers separated by commas (e.g. 1,3,5) or 'all':\n")

    while True:
        selection = input("Your selection: ").strip()
        if selection.lower() == "all":
            selected_topics = topics
            break
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            if all(0 <= i < len(topics) for i in indices):
                selected_topics = [topics[i] for i in indices]
                break
            print(f"  ❌ Numbers must be between 1 and {len(topics)}.")
        except ValueError:
            print("  ❌ Invalid input. Use comma-separated numbers or 'all'.")

    print(f"\n  ✅ Selected: {', '.join(selected_topics)}")

    # ── Manual Topics ─────────────────────────────────────────────
    manual_input = input("\nAdd manual topics? (comma-separated, or press Enter to skip): ").strip()
    if manual_input:
        manual_list = [t.strip() for t in manual_input.split(",") if t.strip()]
        print("  🔍 Validating manual topics against documents...")
        result = validate_manual_topics(manual_list, parsed["combined_text"], topics)
        if result["included"]:
            print(f"  ✅ Included: {', '.join(result['included'])}")
            selected_topics.extend(result["included"])
        if result["ignored"]:
            print(f"  ⚠️  Ignored (not in docs): {', '.join(result['ignored'])}")

    # ── Generate Script ───────────────────────────────────────────
    print("\n── GENERATING SCRIPT... ──")
    print("  (This may take 30–60 seconds depending on length...)\n")

    try:
        script = generate_script(
            host_name=host_name,
            host_gender=host_gender,
            host_speed=host_speed,
            guest_name=guest_name,
            guest_gender=guest_gender,
            guest_speed=guest_speed,
            selected_topics=selected_topics,
            combined_text=parsed["combined_text"],
            duration_minutes=duration,
        )
    except Exception as e:
        print(f"  ❌ Script generation failed: {e}")
        sys.exit(1)

    word_count = len(script.split())
    print(f"  ✅ Script generated! ({word_count:,} words | ~{round(word_count/130, 1)} min)\n")

    # ── Review Loop ───────────────────────────────────────────────
    while True:
        print("\n" + "="*60)
        print(script)
        print("="*60)

        # Save to file
        output_file = f"podcast_{host_name.replace(' ', '_')}_{guest_name.replace(' ', '_')}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(script)
        print(f"\n  💾 Script saved to: {output_file}")

        action = input("\n  [M] Modify script | [Q] Quit: ").strip().upper()

        if action == "Q":
            print("\n  ✅ Done! Your podcast script is ready. Goodbye!\n")
            break
        elif action == "M":
            mod_request = input("  Describe your changes: ").strip()
            if mod_request:
                print("  🔄 Regenerating script with modifications...")
                try:
                    script = modify_script(
                        existing_script=script,
                        modification_request=mod_request,
                        host_name=host_name,
                        guest_name=guest_name,
                        selected_topics=selected_topics,
                        combined_text=parsed["combined_text"],
                        duration_minutes=duration,
                        host_speed=host_speed,
                        guest_speed=guest_speed,
                    )
                    word_count = len(script.split())
                    print(f"  ✅ Modified! ({word_count:,} words)")
                except Exception as e:
                    print(f"  ❌ Modification failed: {e}")


if __name__ == "__main__":
    main()
