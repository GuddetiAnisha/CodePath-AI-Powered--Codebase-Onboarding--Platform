# CodePath — AI Codebase Onboarding

CodePath is a thesis-ready prototype that turns an unfamiliar source repository into a guided onboarding experience. It indexes source code and documentation, retrieves cited evidence for questions, generates an architecture overview, guides newcomers through practical tasks, and records lightweight evaluation metrics.

## Features

- Repository ingestion for Python, JavaScript/TypeScript, Java, Go, Rust, C/C++, Markdown, YAML, JSON, and TOML
- Local TF-IDF retrieval with file-and-line citations (no API required)
- Optional OpenAI-compatible answer generation
- Architecture map based on imports and symbol extraction
- Guided onboarding journey: orient, trace, change, verify
- Self-check quizzes and task completion tracking
- Confidence, escalation, and feedback measurements
- SQLite persistence and downloadable CSV evaluation data
- Built-in demo repository

## Run

```bash
cd codepath_onboarding
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

To use an LLM, set `OPENAI_API_KEY`. Optional variables: `OPENAI_BASE_URL` and `OPENAI_MODEL` (default `gpt-4.1-mini`). The app remains fully usable without them.

## Test

```bash
pytest -q
```

## Ethical and security notes

Only index repositories you are authorized to process. Local retrieval keeps source on the machine; enabling an external LLM sends only retrieved excerpts and the question to that provider. Never index secrets. The prototype excludes common secret/build directories, but this is not a substitute for secret scanning or organizational approval.

