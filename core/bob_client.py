import os
import json
import logging

try:
    import ibm_bob_sdk
    BOB_AVAILABLE = True
except ImportError:
    BOB_AVAILABLE = False

class BobClient:
    """
    Client for IBM Bob integration.
    Handles deep repository understanding and context extraction.
    Falls back to mock mode if the Bob SDK is unavailable or errors occur.
    """
    
    def __init__(self, api_key: str = None, use_mock: bool = False):
        self.api_key = api_key or os.getenv("IBM_BOB_API_KEY")
        # If Bob SDK is not installed, we must use mock
        self.use_mock = use_mock or not BOB_AVAILABLE
        self.client = None
        
        if not self.use_mock:
            try:
                self.client = ibm_bob_sdk.Client(api_key=self.api_key)
            except Exception as e:
                logging.warning(f"Failed to initialize IBM Bob Client: {e}. Falling back to mock.")
                self.use_mock = True

    def analyze_repository(self, repo_path: str, file_contents: dict) -> str:
        """
        Send full repository context to Bob.
        file_contents: {filename: file_content_string} for all Python files
        Returns: Bob's natural language analysis of the codebase
        """
        if self.use_mock:
            return self._mock_analyze(file_contents)
            
        try:
            # Prepare context from all Python files
            full_context = "\n\n".join([f"--- FILE: {name} ---\n{content}" for name, content in file_contents.items()])
            
            instruction = (
                "You are analyzing a Python ML repository for the ContextForge tool. "
                "Read all provided files and give a comprehensive analysis covering: "
                "(1) overall architecture and data flow, "
                "(2) the purpose of each module, "
                "(3) how data flows from input to prediction output, "
                "(4) the design decisions made by the original developer, "
                "(5) potential issues or technical debt, "
                "(6) suggestions for the FastAPI wrapper design. "
                "Be specific and reference actual function and class names from the code."
            )
            
            # Real SDK call (assuming a chat/analyze interface)
            response = self.client.analyze(
                repo_path=repo_path,
                context=full_context,
                instruction=instruction
            )
            return response
        except Exception as e:
            logging.error(f"IBM Bob analyze_repository error: {e}")
            return self._mock_analyze(file_contents)
    
    def generate_documentation(self, analysis: dict, style: str = "developer-guide") -> str:
        """
        Ask Bob to generate documentation based on analysis.
        Returns: markdown documentation string
        """
        if self.use_mock:
            return self._mock_documentation(analysis)
            
        try:
            instruction = (
                "Generate a comprehensive developer onboarding guide in Markdown. "
                "A new developer joining the team should be able to understand the entire codebase, "
                "run it locally, and contribute to it after reading this guide. "
                "Include: project overview, architecture explanation with module map, "
                "key functions and their purpose, how to extend the model, and common gotchas."
            )
            
            # Pass full analysis and any existing metadata
            response = self.client.generate_docs(
                analysis=analysis,
                instruction=instruction
            )
            return response
        except Exception as e:
            logging.error(f"IBM Bob generate_documentation error: {e}")
            return self._mock_documentation(analysis)
    
    def suggest_api_design(self, entry_points: list) -> dict:
        """
        Ask Bob to suggest the best FastAPI endpoint design for the detected functions.
        Returns: {endpoint_path: {method, description, request_schema, response_schema}}
        """
        if self.use_mock:
            return self._mock_api_design(entry_points)
            
        try:
            instruction = (
                "Design a clean, production-ready FastAPI API for these ML model functions. "
                "For each function, suggest: the endpoint path, HTTP method, "
                "request body schema with field names and types, response schema, and any validation rules. "
                "Follow REST conventions."
            )
            
            response = self.client.suggest_design(
                entry_points=entry_points,
                instruction=instruction
            )
            
            # Ensure the response is a structured dict
            if isinstance(response, str):
                return json.loads(response)
            return response
        except Exception as e:
            logging.error(f"IBM Bob suggest_api_design error: {e}")
            return self._mock_api_design(entry_points)
    
    def _mock_analyze(self, file_contents: dict) -> str:
        """Returns realistic placeholder analysis for development without Bob."""
        file_list = list(file_contents.keys())
        return f"""
## Repository Analysis (Mock — Replace with IBM Bob)

This repository contains {len(file_list)} Python files. 
Key files identified: {', '.join(file_list[:5])}.

The codebase appears to follow a standard ML project structure with 
training, inference, and utility modules. The primary entry point for 
predictions appears to be in the main model file.

**Architecture Summary:**
The code separates data preprocessing, model definition, and inference 
into distinct modules — a clean separation of concerns that makes the 
FastAPI wrapper straightforward to generate.

**Design Decisions:**
- Model weights are loaded at startup to avoid per-request latency
- Input validation is handled before model inference
- The predict function returns a structured dict rather than raw arrays
"""
    
    def _mock_documentation(self, analysis: dict) -> str:
        return "# Developer Guide\n\n*Generated by IBM Bob (mock mode — real Bob coming soon)*\n\n" \
               "This guide will be populated with Bob's full codebase analysis once Bob access is available."
    
    def _mock_api_design(self, entry_points: list) -> dict:
        return {
            f"/predict/{ep.get('function_name', 'run')}": {
                "method": "POST",
                "description": f"Run inference using {ep.get('function_name', 'model')}",
                "request_schema": "PredictRequest",
                "response_schema": "PredictResponse"
            }
            for ep in entry_points
        }
