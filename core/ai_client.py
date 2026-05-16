import os
import logging
import google.generativeai as genai

class AIEngine:
    """
    AI Engine for repository analysis.
    Uses Google Gemini for deep code understanding and insights.
    Maintains a consistent interface for the ContextForge application.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logging.warning("GEMINI_API_KEY not found. Running in Mock mode.")
            self.use_mock = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
                self.use_mock = False
            except Exception as e:
                logging.error(f"Failed to initialize Gemini: {e}")
                self.use_mock = True

    def analyze_repository(self, repo_path: str, file_contents: dict) -> str:
        """
        Analyzes repository context using Gemini.
        """
        if self.use_mock:
            return self._mock_analyze(file_contents)
            
        try:
            # Prepare context
            files_str = "\n\n".join([f"--- FILE: {name} ---\n{content}" for name, content in file_contents.items()])
            
            prompt = (
                f"Analyze this Python ML repository: {repo_path}\n\n"
                f"File contents:\n{files_str}\n\n"
                "Provide a detailed analysis covering:\n"
                "1. Architecture overview\n"
                "2. Logic flow from raw data to prediction\n"
                "3. Suggested FastAPI wrapper structure\n"
                "4. Critical improvements for production readiness.\n"
                "Keep the response professional and technical."
            )
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini analysis error: {e}")
            return self._mock_analyze(file_contents)

    def generate_documentation(self, analysis_text: str) -> str:
        """
        Generates a developer onboarding guide.
        """
        if self.use_mock:
            return "# Developer Onboarding Guide\n\n*Auto-generated Analysis Summary*\n\n" + analysis_text
            
        try:
            prompt = (
                f"Based on this codebase analysis:\n{analysis_text}\n\n"
                "Generate a comprehensive Developer Onboarding Guide in Markdown. "
                "Include sections for Installation, Usage, Project Structure, and How to Contribute."
            )
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini documentation error: {e}")
            return "# Developer Guide\n\n(Error generating full guide via AI)"

    def _mock_analyze(self, file_contents: dict) -> str:
        file_list = list(file_contents.keys())
        return f"""
### ⚒️ ContextForge Analysis (Simulation)

Codebase analyzed: {len(file_list)} modules detected.

**Key Architecture:**
- Data processing pipeline identified in `{file_list[0] if file_list else 'main'}`.
- Model serialization format: Joblib/Pickle detected.

**Recommendations:**
- Move global variables to environment configs.
- Implement Pydantic models for request validation.
- Add docstrings to core functions for better maintenance.
"""
