# AI CV Reviewer & ATS Optimizer

ResumeAI is a premium, AI-powered professional resume critique and Applicant Tracking System (ATS) optimization application. It evaluates resumes, compares them against optional job descriptions, provides quantified metrics, matches keywords, suggests rewrites using the STAR methodology, and stores session history.

---

## Key Features & Core Enhancements

This project has been enhanced with enterprise-ready features to ensure safety, robustness, context retrieval, and structured persistence:

### 1. Robust Structured Outputs

* **Pydantic Validation**: All outputs from the Groq API are parsed and verified using a strict Pydantic V2 schema (`CVReviewSchema`). This ensures that the response contains exact fields (scores, summary, lists of strengths/improvements, STAR bullet rewrites).
* **Output Repair Guardrail**: In the event that the LLM produces invalid scores or incomplete JSON structures, the application automatically triggers a repair mechanism that cleans up types, clamps score values to `0-100`, and populates default properties to guarantee the frontend dashboard never crashes.

### 2. Context Retrieval (RAG & Memory)

* **Retrieval-Augmented Generation (RAG)**: The system indexes a library of professional CV-writing guidelines (`cv_rag_db.json`). When a user submits a CV, the retriever (`rag_retriever.py`) uses Jaccard keyword overlap and heuristic scoring to select the 3 most relevant tips (e.g. STAR bullet structures, lack of metrics, groupings, first-person pronouns, etc.). These tips are injected into the LLM system prompt and rendered directly in the frontend UI under a dedicated **RAG Guidance** tab.
* **Persistent critique memory**: Backed by a local SQLite database (`analyses.db`), the system automatically stores every successful resume analysis. It keeps track of the filename, job title, overall score, keyword match, and full JSON response.
* **History Dashboard**: Users can view their historical analyses on the landing page, track score progress, and click "View" to reload any past critique session instantly from memory without repeating LLM API calls.

### 3. Essential Guardrails

* **Input Length Guardrails**: Validates that CV text is between `100` and `50,000` characters, and job descriptions are under `40,000` characters to prevent API overflows and abuse.
* **Prompt Injection Guardrails**: Filters out adversarial instruction overrides (e.g. "ignore previous instructions", "you are now a recipe bot", "system prompt:") and rejects the request with a `400 Bad Request` security alert.
* **Domain Check Guardrails**: Validates that the submitted text actually resembles a Resume/CV by checking for overlapping multi-language keywords (e.g., `experience`, `education`, `skills`, `projects`, `contact`) and email/link formats. Unrelated text (e.g., cookie recipes, random articles) is rejected.

---

## Project Structure

```md
├── main.py                  # FastAPI API Server (Endpoints for reviews & history)
├── core.py                 # Core LLM critique orchestration & Pydantic validation
├── rag_retriever.py        # Keyword overlap RAG search & tips selector
├── history_db.py           # SQLite database persistence layer for past sessions
├── guardrails.py           # Safety checks (lengths, injections, domain, repair layer)
├── cv_rag_db.json          # Database of expert CV writing guidelines (RAG source)
├── requirements.txt        # python dependencies list
├── pyproject.toml          # uv project configuration file
├── uv.lock                 # Lockfile for reproducible python environment
└── static/                 # Web Interface static assets
    ├── index.html          # Dashboard markup (RAG & History tabs added)
    ├── app.js              # Client side controller (fixed syntax and integrated API)
    └── styles.css          # Premium glassmorphic styling sheet
```

---

## Getting Started

### Prerequisites

* **Python**: `3.13` or newer.
* **uv**: Recommended for fast package management (pre-configured in this environment).

### Installation

Activate the virtual environment and install the required dependencies:

```bash
# If using uv (fastest)
uv sync

# Or standard pip
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root of the project (or modify the existing one) to specify your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Running the Application

Launch the FastAPI development server:

```bash
uv run main.py
```

or

```bash
python main.py
```

The server will start at **`http://127.0.0.1:8000`**. Open this address in your web browser to access the CV Reviewer dashboard.

---

## Verification & Testing

To execute the automated system integration tests (verifying guardrails, SQLite DB saving, RAG retrieval, and Pydantic validation):

```bash
uv run python .\tests\test_system.py # On Windows
#or
# uv run python tests/test_system.py # On Linux/Mac

```
