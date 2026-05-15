import streamlit as st

def render_api_panel(analysis_result):
    st.header("FastAPI Deployment Package")
    
    with st.container():
        st.markdown('<div class="carbon-surface">', unsafe_allow_html=True)
        
        files = {
            "main.py": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}",
            "models.py": "from pydantic import BaseModel\nclass Item(BaseModel):\n    name: str",
            "Dockerfile": "FROM python:3.9\nCOPY . /app\nWORKDIR /app\nRUN pip install -r requirements.txt\nCMD ['uvicorn', 'main:app']",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - '8000:8000'"
        }
        
        selected_file = st.selectbox("Generated Files", list(files.keys()))
        
        st.code(files[selected_file], language="python" if ".py" in selected_file else "yaml")
        
        st.button("Download Deployment Package (.zip)")
        
        st.markdown('</div>', unsafe_allow_html=True)
