import streamlit as st
import os
import shutil
import time
from dotenv import load_dotenv

load_dotenv()
from core.analyzer import RepoAnalyzer
from core.generator import ContextForgeGenerator
from core.ai_client import AIEngine
from utils.repo_handler import extract_zip, clone_github_repo, read_all_python_files, create_output_zip, remove_readonly

# --- CARBON DESIGN SYSTEM CSS ---
CARBON_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, .stApp, p, li, label, h1, h2, h3, h4, h5, h6, .stButton, .stTextInput, .stSelectbox {
    font-family: 'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif !important;
}

*, *::before, *::after {
    box-sizing: border-box;
}

/* Page Background */
.stApp {
    background-color: #ffffff !important;
}

/* Remove Streamlit default rounding and styling */
.stButton > button, .stDownloadButton > button {
    border-radius: 0px !important;
    background-color: #0f62fe !important;
    color: white !important;
    border: none !important;
    padding: 12px 16px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    letter-spacing: 0.16px !important;
    transition: background-color 0.2s ease;
    width: auto;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background-color: #0353e9 !important;
    border: none !important;
    color: white !important;
}
.stButton > button:active, .stDownloadButton > button:active {
    background-color: #002d9c !important;
}

/* Secondary Button Selector */
[data-testid="stBaseButton-secondary"] {
    background-color: #161616 !important;
    color: white !important;
}

/* Text inputs — Carbon style */
.stTextInput > div > div > input {
    border-radius: 0px !important;
    border: none !important;
    border-bottom: 1px solid #8c8c8c !important;
    background-color: #f4f4f4 !important;
    padding: 11px 16px !important;
    font-size: 16px !important;
    letter-spacing: 0.16px !important;
    color: #161616 !important;
}
.stTextInput > div > div > input:focus {
    border-bottom: 2px solid #0f62fe !important;
    outline: none !important;
    box-shadow: none !important;
}

/* File uploader */
.stFileUploader {
    border-radius: 0px !important;
}
.stFileUploader > section {
    border-radius: 0px !important;
    border: 1px dashed #e0e0e0 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important;
    border-bottom: 1px solid #e0e0e0 !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0px !important;
    font-size: 14px !important;
    letter-spacing: 0.16px !important;
    padding: 12px 16px !important;
    background-color: transparent !important;
    border: none !important;
    color: #161616 !important;
    font-weight: 400 !important;
}
.stTabs [aria-selected="true"] {
    border-bottom: 2px solid #0f62fe !important;
    font-weight: 600 !important;
}

/* Cards & Containers */
.carbon-card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 0px;
    padding: 24px;
    margin-bottom: 16px;
}

/* Navigation Bar */
.top-nav {
    height: 48px;
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
}
.nav-wordmark {
    font-weight: 300;
    font-size: 20px;
    color: #161616;
}
.nav-powered {
    font-size: 12px;
    color: #525252;
}

/* Hero Section */
.hero-section {
    padding: 48px;
    background-color: #ffffff;
    margin-top: 48px;
}
.hero-headline {
    font-size: 42px;
    font-weight: 300;
    color: #161616;
    margin-bottom: 8px;
}
.hero-subheadline {
    font-size: 18px;
    color: #525252;
    margin-bottom: 32px;
}

/* Labels and Headers */
h1, h2, h3, h4, h5, h6, label, p, li, .stMarkdown p, .stMarkdown li, .stWidgetLabel p {
    color: #161616 !important;
}

/* Code Blocks — Make them more colorful and readable */
code {
    color: #da1e28 !important; /* Carbon Red for inline code */
    background-color: #f4f4f4 !important;
    padding: 2px 4px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

.stCodeBlock div {
    background-color: #f4f4f4 !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 0px !important;
}

/* Ensure code block text is NOT forced to black so highlighting works */
.stCodeBlock span {
    color: inherit !important;
}

/* Status Bar */
.status-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 32px;
    background-color: #f4f4f4;
    border-top: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-size: 12px;
    color: #525252;
    z-index: 1000;
}

/* Badges */
.badge {
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}
.badge-success { background-color: #24a148; color: white; }
.badge-warning { background-color: #f1c21b; color: #161616; }
.badge-error { background-color: #da1e28; color: white; }

/* Expanders */
.stExpander {
    border-radius: 0px !important;
    border: 1px solid #e0e0e0 !important;
    background-color: #ffffff !important;
}

/* Main Content Padding */
.main-content {
    padding: 0 48px 64px 48px;
}

footer { visibility: hidden; }
header { visibility: hidden; }
</style>
"""

def main():
    st.set_page_config(page_title="ContextForge", page_icon="⚒️", layout="wide")
    st.markdown(CARBON_CSS, unsafe_allow_html=True)

    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'generated_files' not in st.session_state:
        st.session_state.generated_files = None
    if 'status_msg' not in st.session_state:
        st.session_state.status_msg = "Ready"

    # Top Nav
    st.markdown('<div class="top-nav"><div class="nav-wordmark">ContextForge</div><div class="nav-powered">AI-Powered Repository Understanding</div></div>', unsafe_allow_html=True)

    # Hero
    st.markdown('<div class="hero-section"><div class="hero-headline">From repo to production.</div><div class="hero-subheadline">Understand any ML codebase and deploy it as an API — forged with IBM Bob.</div></div>', unsafe_allow_html=True)
    
    hero_cols = st.columns([0.15, 0.15, 0.7])
    with hero_cols[0]:
        st.button("Upload Repository", key="hero_upload")
    with hero_cols[1]:
        if st.button("Try with example", key="hero_example", type="secondary"):
             st.session_state.github_url = "https://github.com/scikit-learn/scikit-learn"



    col1, col2 = st.columns([0.4, 0.6], gap="large")

    with col1:
        st.subheader("Input Panel")
        repo_zip = st.file_uploader("Upload .zip repository", type=["zip"])
        st.markdown('<p style="font-size: 14px; color: #525252; margin: 16px 0 8px 0;">OR</p>', unsafe_allow_html=True)
        github_url = st.text_input("GitHub URL", value=st.session_state.get('github_url', ""), placeholder="https://github.com/user/repo")
        
        # Advanced Options
        with st.expander("Advanced Options"):
            model_type = st.selectbox("Model type selector", ["Auto-detect", "sklearn", "PyTorch", "TensorFlow"])
            api_prefix = st.text_input("API prefix input", value="/api/v1")
            include_tests = st.checkbox("Include unit tests", value=True)
            include_compose = st.checkbox("Include docker-compose", value=True)

        if st.button("Analyze Repository", use_container_width=True):
            st.session_state.status_msg = "Preparing repository..."
            temp_dir = "temp_repo"
            try:
                if repo_zip:
                    actual_temp, repo_name = extract_zip(repo_zip, temp_dir)
                elif github_url:
                    actual_temp, repo_name = clone_github_repo(github_url, temp_dir)
                else:
                    st.error("Please provide a repository.")
                    return

                # 1. Analyze
                st.session_state.status_msg = "Analyzing codebase (AST)..."
                analyzer = RepoAnalyzer(actual_temp)
                analysis = analyzer.full_analysis()
                analysis["repo_name"] = repo_name  # Ensure name is passed through
                
                # 2. Consult AI
                st.session_state.status_msg = "Consulting ContextForge AI Engine..."
                ai_engine = AIEngine()
                py_files = read_all_python_files(actual_temp)
                ai_summary = ai_engine.analyze_repository(actual_temp, py_files)
                
                # 3. Generate
                st.session_state.status_msg = "Forging API and documentation..."
                config = {
                    "model_type": model_type,
                    "api_prefix": api_prefix,
                    "include_tests": include_tests,
                    "include_compose": include_compose
                }
                generator = ContextForgeGenerator(analysis, config)
                generated = generator.generate_all()
                generated['developer_guide'] = generator.generate_developer_guide(ai_summary)
                
                # Mock QA Report Data
                analysis["qa_issues"] = [
                    {"type": "Success", "msg": f"Detected {analysis['framework']} framework", "severity": "Success"},
                    {"type": "Warning", "msg": f"Found {len(analysis['entry_points'])} potential entry points", "severity": "Warning"},
                    {"type": "Error", "msg": "No unit tests found in source repo", "severity": "Error"}
                ]

                st.session_state.analysis_result = analysis
                st.session_state.generated_files = generated
                st.session_state.status_msg = "Analysis complete."
                
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, onerror=remove_readonly)
                    
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.session_state.status_msg = "Error during analysis."
        


    with col2:
        tab1, tab2, tab3 = st.tabs(["Developer Guide", "API Package", "QA Report"])
        
        if st.session_state.analysis_result:
            with tab1:
                st.markdown(st.session_state.generated_files['developer_guide'], unsafe_allow_html=True)
                guide_bytes = st.session_state.generated_files['developer_guide'].encode()
                st.download_button("Download Guide (Markdown)", guide_bytes, "DEVELOPER_GUIDE.md")

            with tab2:
                gen = st.session_state.generated_files
                files = {
                    "main.py": gen['fastapi_main'],
                    "models.py": gen['pydantic_models'],
                    "Dockerfile": gen['dockerfile'],
                    "requirements.txt": gen['requirements']
                }
                if 'docker_compose' in gen: files["docker-compose.yml"] = gen['docker_compose']
                if 'unit_tests' in gen: files["test_api.py"] = gen['unit_tests']
                
                selected_file = st.selectbox("Select file to view", list(files.keys()))
                st.code(files[selected_file], language="python" if ".py" in selected_file else "yaml")
                
                zip_bytes = create_output_zip(files)
                st.download_button("Download All Files (.zip)", zip_bytes, "contextforge_api.zip")

            with tab3:
                st.markdown("#### Recommendations from Bob")
                for issue in st.session_state.analysis_result.get("qa_issues", []):
                    border_color = {'Success': '#24a148', 'Warning': '#f1c21b', 'Error': '#da1e28'}[issue['severity']]
                    st.markdown(f'<div style="margin-bottom: 12px; border-left: 4px solid {border_color}; padding: 8px 12px; background: #f4f4f4;"><span class="badge badge-{issue["severity"].lower()}">{issue["type"].upper()}</span><span style="margin-left: 8px; font-size: 14px;">{issue["msg"]}</span></div>', unsafe_allow_html=True)
        else:
            st.info("Run analysis to view results.")

    st.markdown('<div class="status-bar"><span>Analysis Step: ' + st.session_state.status_msg + '</span></div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
