# 🎙️ Podcast Script Generator

An AI-powered system that generates natural, conversational podcast scripts between a Host and Guest — grounded in your uploaded documents.

## ✨ Features

- 📄 Upload PDF, DOCX, or TXT documents as source material
- 🧠 Automatic AI topic extraction using LLaMA 3.1 via HuggingFace Inference API
- ✅ Topic selection with manual topic validation (included vs ignored)
- 🎙️ Full Host–Guest dialogue generation (opening → topics → closing)
- ⏱️ Duration-aware script length (5–60 minutes)
- 🗣️ Speaker gender and speaking speed influence script pacing
- 🔄 Unlimited modification cycles (full script regeneration each time)
- 🖥️ Streamlit UI + CLI fallback

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| LLM | Meta LLaMA 3.1 8B Instruct via [HuggingFace Inference API](https://huggingface.co) (Open Source) |
| UI | Streamlit |
| PDF Parsing | PyMuPDF (fitz) |
| DOCX Parsing | python-docx |
| LLM Client | huggingface_hub (InferenceClient) |
| Env Management | python-dotenv |

---

## ⚙️ Setup

### 1. Clone / download the project

```bash
cd podcast_generator
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your HuggingFace API key

```bash
cp .env.example .env
# Open .env and replace: HF_API_KEY=your_actual_key_here
```

Get a free HuggingFace API token at: https://huggingface.co/settings/tokens

> **Important:** When creating your token, make sure to enable the **"Make calls to Inference Providers"** permission.

---

## 🚀 How to Run

### Option A: Streamlit UI (Recommended)

```bash
streamlit run app.py
```

Or if `streamlit` is not recognized:

```bash
python -m streamlit run app.py
```

Then open http://localhost:8501 in your browser.

**Flow:**
1. Fill in Host & Guest details (name, gender, speaking speed)
2. Upload at least one document (PDF/DOCX/TXT)
3. Choose podcast duration (5–60 minutes)
4. Review AI-extracted topics → select which to include
5. Optionally add manual topics (system validates against documents)
6. Generate script → review → optionally modify (unlimited cycles)
7. Download the final script as .txt

---

### Option B: Terminal / CLI (Fallback)

```bash
python cli.py
```

The CLI will guide you through all steps interactively via the terminal and save the final script as a `.txt` file.

---

## 📁 Project Structure

```
podcast_generator/
│
├── app.py                      # Streamlit UI (main entry)
├── cli.py                      # CLI fallback
├── requirements.txt
├── .env.example                # Template for API key
├── README.md
│
├── backend/
│   ├── __init__.py
│   ├── document_parser.py      # PDF, DOCX, TXT parsing
│   ├── topic_extractor.py      # LLM-powered topic extraction + validation
│   ├── script_generator.py     # Core script generation + modification
│   └── utils.py                # Validation, word count, duration helpers
│
└── sample_outputs/
    └── sample_script.txt       # Example generated script for review
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `HF_API_KEY` | Your HuggingFace API token (with Inference Providers permission) | ✅ Yes |

---

## 📝 Sample Output

See `sample_outputs/sample_script.txt` for an example generated script.

---

## ⚠️ Notes

- Never commit your `.env` file (add it to `.gitignore`)
- HuggingFace free tier has rate limits — if you see a "429 Too Many Requests" error, wait 1-2 minutes and retry
- If the model is cold-starting (503 error), wait 30 seconds and retry
- All facts in the generated script are strictly grounded in the uploaded documents
- Each modification request regenerates the complete script (no partial edits)