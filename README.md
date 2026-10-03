# CodePath — AI Codebase Onboarding

CodePath is a thesis-ready prototype that turns an unfamiliar source repository into a guided onboarding experience. It indexes source code and documentation, retrieves cited evidence for questions, generates an architecture overview, guides newcomers through practical tasks, and records lightweight evaluation metrics.

## Features

- Repository ingestion for Python, JavaScript/TypeScript, Java, Go, Rust, C/C++, Markdown, YAML, JSON, and TOML
- Local TF-IDF retrieval with file-and-line citations (no API required)
- Lightweight intent-aware reranking for implementation/definition queries and test-oriented queries
- Optional OpenAI-compatible answer generation
- Architecture map based on imports and symbol extraction
- Guided onboarding journey: orient, trace, change, verify
- Self-check quizzes and task completion tracking
- Confidence, escalation, and feedback measurements
- SQLite persistence and downloadable CSV evaluation data
- Built-in demo repository

## Run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

To use an LLM, set `OPENAI_API_KEY`. Optional variables: `OPENAI_BASE_URL` and `OPENAI_MODEL` (default `gpt-4.1-mini`). The app remains fully usable without them.

## Test

```bash
python -m pytest -q
```

## Validation results

CodePath was manually validated on its built-in deterministic demo repository and the same scenarios are now covered by an automated retrieval benchmark.

### Demo retrieval benchmark

| Query | Expected top source |
|---|---|
| Where is the checkout function implemented? | `service.py` |
| What discount is applied to orders above 100? | `service.py` |
| Which test verifies the discount behavior? | `test_service.py` |
| What should I run before changing discount behavior? | `README.md` |

Observed manual result on the four-query demo benchmark:

- **Top-1 retrieval accuracy: 4/4 (100%)**
- **Recall@3: 4/4 (100%)**
- File-and-line citations were returned for retrieved evidence.
- The implementation-location query improved from `service.py` at rank 3 under plain TF-IDF to rank 1 after intent-aware reranking.

The automated test suite now includes these four expected top-1 retrieval cases so the behavior can be reproduced with:

```bash
python -m pytest -q
```

### Validation scope

These results validate retrieval and citation behavior on a **small built-in synthetic demo repository**. They do not establish performance on large or unfamiliar production repositories. Stronger research evaluation should use multiple independent codebases, a larger question set, manually reviewed ground truth, and metrics such as Top-k accuracy, MRR, citation correctness, latency, and user-task completion.

## Ethical and security notes

Only index repositories you are authorized to process. Local retrieval keeps source on the machine; enabling an external LLM sends only retrieved excerpts and the question to that provider. Never index secrets. The prototype excludes common secret/build directories, but this is not a substitute for secret scanning or organizational approval.
