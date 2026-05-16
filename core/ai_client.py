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
        
        # Check if key is missing OR still using the placeholder from .env.example
        if not self.api_key or "your_gemini_api_key_here" in self.api_key:
            logging.warning("GEMINI_API_KEY not found or invalid. Running in Mock mode.")
            self.use_mock = True
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
                self.use_mock = False
            except Exception as e:
                logging.error(f"Failed to initialize Gemini: {e}")
                self.use_mock = True

    @property
    def is_mock(self) -> bool:
        return self.use_mock

    def analyze_repository(self, repo_path: str, file_contents: dict) -> str:
        """
        Analyzes repository context using Gemini with a high-detail prompt.
        """
        if self.use_mock:
            return self._mock_analyze(file_contents)
            
        try:
            # Prepare context
            files_str = "\n\n".join([f"--- FILE: {name} ---\n{content}" for name, content in file_contents.items()])
            
            prompt = (
                f"You are an expert Senior Machine Learning Engineer and Architect. "
                f"Analyze this Python ML repository: {repo_path}\n\n"
                f"Files and Code contents:\n{files_str}\n\n"
                "Task: Provide a deep technical analysis of this codebase for the ContextForge Developer Guide. "
                "The analysis MUST be comprehensive and include:\n"
                "1. **Architecture & Logic Flow**: Explain how the model is loaded and how data is transformed from input to output. "
                "Mention specific class names and function names found in the code.\n"
                "2. **Internal Dependencies**: Explain the relationship between modules (e.g., how the main app utilizes feature extractors).\n"
                "3. **Production Recommendations**: Identify technical debt, missing error handling, and performance bottlenecks. "
                "Suggest specific Pydantic models for the FastAPI request body.\n"
                "4. **Infrastructure Needs**: What specific environment configurations are needed for this model?\n\n"
                "FORMAT: Use Markdown with professional headings. Do NOT use placeholders. Be specific to the code provided."
            )
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini analysis error: {e}")
            # Return a clearer error message instead of generic mock
            return f"### ⚠️ AI Analysis Interrupted\n\nGemini was active but encountered an error: `{str(e)}`. \n\nPlease check your internet connection or API quota. Falling back to basic simulation below:\n\n" + self._mock_analyze(file_contents)

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
