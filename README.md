# ⚒️ ContextForge

**ContextForge** is a production-grade developer productivity engine designed to bridge the gap between complex ML repositories and deployment-ready APIs. It analyzes existing Python codebases using static analysis (AST) and AI-driven insights to generate high-quality developer documentation and a complete FastAPI wrapper.

---

## 🚀 Features

- **Automated Repository Analysis**: Identifies ML frameworks (sklearn, pytorch, tensorflow), entry points, and internal dependency maps.
- **AI-Powered Developer Guide**: Generates an interactive onboarding guide covering architecture, module flow, and design decisions using **IBM Bob**.
- **FastAPI Scaffolding**: Produces production-ready `main.py` with lifespan model loading, Pydantic request/response models, and health checks.
- **Containerization Ready**: Generates `Dockerfile` and `docker-compose.yml` optimized for the detected framework.
- **Carbon Design UI**: A sleek, professional frontend built with **Streamlit** following the **IBM Carbon Design System**.

## 🛠️ Project Structure

```bash
ContextForge/
├── app.py              # Streamlit frontend entry point
├── core/
│   ├── analyzer.py     # AST-based repository analysis engine
│   ├── generator.py    # Jinja2 template orchestration
│   ├── bob_client.py   # IBM Bob SDK integration & fallback logic
│   └── templates/      # Jinja2 templates for FastAPI, Docker, etc.
├── utils/
│   ├── repo_handler.py # Filesystem and Git operations
│   └── ast_parser.py   # AST parsing utilities
├── requirements.txt    # Project dependencies
└── README.md           # You are here
```

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/contextforge.git
   cd contextforge
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up IBM Bob API Key:**
   Export your API key as an environment variable:
   ```bash
   export IBM_BOB_API_KEY="your_api_key_here"
   ```

## 🚀 Usage

Run the Streamlit application:
```bash
streamlit run app.py
```

1. **Upload** a `.zip` repository or provide a **GitHub URL**.
2. **Configure** API prefix and optional components (Tests, Docker Compose).
3. **Analyze**: Let ContextForge map the dependencies and consult Bob for architecture insights.
4. **Download**: Get your generated Developer Guide and API Package as a ZIP.

## 🧰 Tech Stack

- **Frontend**: Streamlit
- **Logic**: Python 3.10+
- **Analysis**: Python AST, GitPython
- **AI Intelligence**: IBM Bob SDK
- **Templating**: Jinja2
- **UI System**: IBM Carbon Design System

---

