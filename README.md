# ⚒️ ContextForge: From Repo to Production

**ContextForge** is a production-grade developer productivity engine designed to bridge the gap between messy ML repositories and deployment-ready APIs. It automates the "last mile" of machine learning engineering by providing deep code understanding and instant infrastructure generation.

> [!IMPORTANT]
> **Forged with IBM Bob**: This project was developed using **IBM Bob IDE** as the primary AI-powered development partner. Bob's contextual awareness and reasoning were instrumental in building the complex AST analysis engine and enforcing the strict IBM Carbon Design System.

---

## 🚀 Key Features

- **Intelligent Code Mapping**: Uses Python's Abstract Syntax Tree (AST) to map dependencies and detect model entry points automatically.
- **AI-Powered Repository Insights**: Leverages advanced LLMs (via Gemini or watsonx.ai) to generate interactive developer onboarding guides.
- **FastAPI Scaffolding**: Instant generation of production-ready `main.py`, Pydantic models, and lifespan handlers.
- **Infrastructure-as-Code**: Automatically generates `Dockerfile` and `docker-compose.yml` optimized for ML workloads.
- **IBM Carbon UI**: A sleek, professional dashboard built with **Streamlit** following mandatory Carbon Design rules.

## 🛠️ Project Structure

```text
ContextForge/
├── app.py              # Streamlit dashboard entry point
├── core/
│   ├── analyzer.py     # AST-based static analysis engine
│   ├── generator.py    # Jinja2 template orchestration
│   └── ai_client.py    # AI Engine integration (Gemini/watsonx)
├── utils/
│   ├── repo_handler.py # Repository extraction and cleanup
│   └── ...
├── bob_sessions/       # MANDATORY: IBM Bob interaction artifacts
├── requirements.txt    # Project dependencies
└── .env                # Environment configuration
```

## 📦 Getting Started

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/your-username/ContextForge.git
   cd ContextForge
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your API Key:
   ```bash
   cp .env.example .env
   # Open .env and add your GEMINI_API_KEY
   ```

3. **Launch Dashboard:**
   ```bash
   streamlit run app.py
   ```

## 🤖 The "Bob Factor" (Hackathon Submission)

This project strictly adheres to the IBM Bob Hackathon requirements. All core logic was written and refactored in collaboration with **IBM Bob IDE**. 

Evidence of this collaboration (exported task histories and consumption reports) can be found in the [bob_sessions/](bob_sessions/) directory.

## 🧰 Technology Stack

- **Frontend**: Streamlit (Python)
- **UI Design**: IBM Carbon Design System
- **Core Engine**: Python AST & Jinja2
- **AI Intelligence**: Google Gemini (via `google-generativeai`)
- **Development Partner**: IBM Bob IDE

---
*Developed for the IBM Bob Hackathon 2026.*
