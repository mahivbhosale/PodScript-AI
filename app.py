"""
app.py — Main Streamlit UI for Podcast Script Generator
Run with: streamlit run app.py
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.document_parser import parse_multiple_documents, save_uploaded_file
from backend.topic_extractor import extract_topics, validate_manual_topics
from backend.script_generator import generate_script, modify_script
from backend.utils import validate_inputs, estimate_word_count

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎙️ Podcast Script Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1DB954;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
        font-size: 1.05rem;
    }
    .step-badge {
        background: #1DB954;
        color: white;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .error-box {
        background: #ffe0e0;
        border-left: 4px solid #e00;
        padding: 1rem;
        border-radius: 6px;
        color: #900;
    }
    .success-box {
        background: #e0ffe6;
        border-left: 4px solid #1DB954;
        padding: 1rem;
        border-radius: 6px;
    }
    .script-box {
        background: #1a1a2e;
        color: #e0e0e0;
        padding: 1.5rem;
        border-radius: 10px;
        font-family: 'Courier New', monospace;
        font-size: 0.92rem;
        line-height: 1.7;
        white-space: pre-wrap;
        max-height: 600px;
        overflow-y: auto;
    }
    div[data-testid="stButton"] button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ─── Session State Init ──────────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,  # 1=inputs, 2=topics, 3=script
        "parsed_docs": None,  # result from parse_multiple_documents
        "extracted_topics": [],  # list of topic strings from LLM
        "selected_topics": [],  # user-confirmed topics
        "manual_topics_result": None,  # {"included": [], "ignored": []}
        "script": None,  # current generated script
        "speaker_config": {},  # host/guest settings
        "duration": 10,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">🎙️ Podcast Script Generator</div>', unsafe_allow_html=True
)
st.markdown(
    '<div class="sub-header">Upload documents → Select topics → Generate a natural podcast conversation</div>',
    unsafe_allow_html=True,
)

# ─── Sidebar: Restart ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔄 Flow Control")
    if st.button("↺ Restart (Reset All)", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Progress")
    steps = ["1️⃣ Setup Inputs", "2️⃣ Topic Selection", "3️⃣ Script Review"]
    for i, s in enumerate(steps, 1):
        if st.session_state.step == i:
            st.markdown(
                f"**→ {s}** ✅" if i < st.session_state.step else f"**→ {s}** ◀️"
            )
        elif i < st.session_state.step:
            st.markdown(f"~~{s}~~ ✅")
        else:
            st.markdown(f"{s}")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("Powered by **HuggingFace + LLaMA 3.1**")
    st.markdown("Set `HF_API_KEY` in your `.env` file.")


# ════════════════════════════════════════════════════════════════════════════
# STEP 1: Inputs
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown("## 📋 Step 1: Configure Your Podcast")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎤 Host Details")
        host_name = st.text_input("Host Name *", placeholder="e.g. Sarah Mitchell")
        host_gender = st.selectbox("Host Gender *", ["male", "female"])
        host_speed = st.slider(
            "Host Speaking Speed *",
            min_value=50,
            max_value=150,
            value=100,
            help="50 = slow & deliberate | 100 = moderate | 150 = fast & energetic",
        )
        st.caption(
            f"{'🐢 Slow & deliberate' if host_speed < 75 else '🎯 Moderate pace' if host_speed < 115 else '⚡ Fast & energetic'}"
        )

    with col2:
        st.markdown("#### 🎧 Guest Details")
        guest_name = st.text_input("Guest Name *", placeholder="e.g. Dr. James Patel")
        guest_gender = st.selectbox("Guest Gender *", ["male", "female"])
        guest_speed = st.slider(
            "Guest Speaking Speed *",
            min_value=50,
            max_value=150,
            value=100,
            help="50 = slow & deliberate | 100 = moderate | 150 = fast & energetic",
        )
        st.caption(
            f"{'🐢 Slow & deliberate' if guest_speed < 75 else '🎯 Moderate pace' if guest_speed < 115 else '⚡ Fast & energetic'}"
        )

    st.markdown("---")
    st.markdown("#### 📄 Upload Documents *")
    st.caption("Upload at least one document. Supported formats: PDF, DOCX, TXT")
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.success(
            f"✅ {len(uploaded_files)} file(s) uploaded: {', '.join([f.name for f in uploaded_files])}"
        )

    st.markdown("---")
    st.markdown("#### ⏱️ Target Duration *")
    duration = st.select_slider(
        "Podcast duration (minutes)",
        options=[5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
        value=10,
    )
    target_words = estimate_word_count(
        duration, host_speed if host_speed else 100, guest_speed if guest_speed else 100
    )
    st.caption(f"📝 Estimated script length: ~{target_words:,} words")

    st.markdown("---")

    if st.button(
        "▶️ Extract Topics & Continue", type="primary", use_container_width=True
    ):
        # Validate
        errors = validate_inputs(
            host_name,
            guest_name,
            host_gender,
            guest_gender,
            host_speed,
            guest_speed,
            duration,
            uploaded_files if uploaded_files else [],
        )

        if errors:
            st.markdown(
                '<div class="error-box">⚠️ <b>Please fix the following before continuing:</b><br>• '
                + "<br>• ".join(errors)
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            with st.spinner("📖 Parsing documents..."):
                try:
                    saved_paths = [save_uploaded_file(f) for f in uploaded_files]
                    parsed = parse_multiple_documents(saved_paths)
                    st.session_state.parsed_docs = parsed

                    if parsed["errors"]:
                        st.warning(
                            "⚠️ Some files had issues:\n" + "\n".join(parsed["errors"])
                        )

                except Exception as e:
                    st.error(f"❌ Document parsing failed: {e}")
                    st.stop()

            with st.spinner("🧠 Extracting topics with AI..."):
                try:
                    topics = extract_topics(parsed["combined_text"])
                    if not topics:
                        st.error(
                            "❌ No topics could be extracted. Please upload more detailed documents."
                        )
                        st.stop()
                    st.session_state.extracted_topics = topics
                except Exception as e:
                    st.error(f"❌ Topic extraction failed: {e}")
                    st.info(
                        "💡 If you see '429 Too Many Requests', wait 1-2 minutes and try again (HuggingFace free tier rate limit)."
                    )
                    st.stop()

            # Save speaker config
            st.session_state.speaker_config = {
                "host_name": host_name.strip(),
                "host_gender": host_gender,
                "host_speed": host_speed,
                "guest_name": guest_name.strip(),
                "guest_gender": guest_gender,
                "guest_speed": guest_speed,
            }
            st.session_state.duration = duration
            st.session_state.step = 2
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# STEP 2: Topic Selection
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown("## 🏷️ Step 2: Select Topics")

    cfg = st.session_state.speaker_config
    docs = st.session_state.parsed_docs

    st.info(
        f"📄 Parsed **{len(docs['documents'])} document(s)** | "
        f"**{docs['total_words']:,} words** total | "
        f"Found **{len(st.session_state.extracted_topics)} topics**"
    )

    st.markdown("#### ✅ Select topics to include in the podcast:")
    st.caption("Check the topics you want covered. At least 1 required.")

    selected = []
    cols = st.columns(2)
    for i, topic in enumerate(st.session_state.extracted_topics):
        with cols[i % 2]:
            if st.checkbox(topic, key=f"topic_{i}", value=True):
                selected.append(topic)

    st.markdown("---")
    st.markdown("#### ✏️ Add manual topics (optional)")
    st.caption(
        "Enter extra topics separated by commas. We'll check if they exist in your documents."
    )
    manual_input = st.text_input(
        "Extra topics",
        placeholder="e.g. Future of AI, Climate Change, Quantum Computing",
        label_visibility="collapsed",
    )

    if st.button("🔍 Validate Manual Topics", disabled=not manual_input.strip()):
        manual_list = [t.strip() for t in manual_input.split(",") if t.strip()]
        with st.spinner("Checking topics against documents..."):
            result = validate_manual_topics(
                manual_list,
                docs["combined_text"],
                st.session_state.extracted_topics,
            )
            st.session_state.manual_topics_result = result

    if st.session_state.manual_topics_result:
        r = st.session_state.manual_topics_result
        col_a, col_b = st.columns(2)
        with col_a:
            if r["included"]:
                st.success(
                    "✅ **Topics found in documents:**\n\n"
                    + "\n".join([f"• {t}" for t in r["included"]])
                )
        with col_b:
            if r["ignored"]:
                st.warning(
                    "⚠️ **Topics NOT found (will be ignored):**\n\n"
                    + "\n".join([f"• {t}" for t in r["ignored"]])
                )

        # Add included manual topics to selection
        for t in r["included"]:
            if t not in selected:
                selected.append(t)

    st.markdown("---")

    if selected:
        st.markdown(
            f"**Selected {len(selected)} topic(s):** "
            + " • ".join([f"`{t}`" for t in selected])
        )
    else:
        st.warning("⚠️ Please select at least one topic.")

    col_back, col_gen = st.columns([1, 3])
    with col_back:
        if st.button("◀ Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    with col_gen:
        if st.button(
            "🎙️ Generate Podcast Script",
            type="primary",
            use_container_width=True,
            disabled=not selected,
        ):
            st.session_state.selected_topics = selected
            cfg = st.session_state.speaker_config

            with st.spinner(
                "✍️ Writing your podcast script... This may take 30-60 seconds..."
            ):
                try:
                    script = generate_script(
                        host_name=cfg["host_name"],
                        host_gender=cfg["host_gender"],
                        host_speed=cfg["host_speed"],
                        guest_name=cfg["guest_name"],
                        guest_gender=cfg["guest_gender"],
                        guest_speed=cfg["guest_speed"],
                        selected_topics=selected,
                        combined_text=st.session_state.parsed_docs["combined_text"],
                        duration_minutes=st.session_state.duration,
                    )
                    st.session_state.script = script
                    st.session_state.step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Script generation failed: {e}")
                    st.info(
                        "💡 If you see '429 Too Many Requests', wait 1-2 minutes and try again (HuggingFace free tier rate limit)."
                    )


# ════════════════════════════════════════════════════════════════════════════
# STEP 3: Script Review & Modify
# ════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown("## 📜 Step 3: Your Podcast Script")

    cfg = st.session_state.speaker_config
    script = st.session_state.script
    word_count = len(script.split())
    est_duration = round(word_count / 130, 1)

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("📝 Word Count", f"{word_count:,}")
    with col_m2:
        st.metric("⏱️ Est. Duration", f"~{est_duration} min")
    with col_m3:
        st.metric("🎯 Target", f"{st.session_state.duration} min")

    st.markdown("---")

    # Script display
    st.markdown("#### 🎙️ Generated Script")
    st.markdown(
        f'<div class="script-box">{script.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # Download button
    st.download_button(
        label="⬇️ Download Script (.txt)",
        data=script,
        file_name=f"podcast_{cfg['host_name'].replace(' ', '_')}_{cfg['guest_name'].replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("#### ✏️ Request Modifications")
    st.caption(
        "Describe what you'd like to change. A completely new script will be generated."
    )

    mod_request = st.text_area(
        "Modification request",
        placeholder='e.g. "Make the tone more casual and add more humor"\n"Go deeper on the topic of machine learning"\n"Make the opening more energetic"',
        height=100,
        label_visibility="collapsed",
    )

    col_back2, col_modify = st.columns([1, 3])
    with col_back2:
        if st.button("◀ Change Topics", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with col_modify:
        if st.button(
            "🔄 Regenerate with Changes",
            type="primary",
            use_container_width=True,
            disabled=not mod_request.strip(),
        ):
            with st.spinner("✍️ Rewriting script based on your feedback..."):
                try:
                    new_script = modify_script(
                        existing_script=st.session_state.script,
                        modification_request=mod_request,
                        host_name=cfg["host_name"],
                        guest_name=cfg["guest_name"],
                        selected_topics=st.session_state.selected_topics,
                        combined_text=st.session_state.parsed_docs["combined_text"],
                        duration_minutes=st.session_state.duration,
                        host_speed=cfg["host_speed"],
                        guest_speed=cfg["guest_speed"],
                    )
                    st.session_state.script = new_script
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Modification failed: {e}")
                    st.info(
                        "💡 If you see '429 Too Many Requests', wait 1-2 minutes and try again (HuggingFace free tier rate limit)."
                    )
