import streamlit as st

def inject_carbon_theme():
    carbon_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif !important;
            letter-spacing: 0.16px !important;
            color: #161616;
        }

        h1, h2, h3, h4, h5, h6 {
            font-weight: 300 !important;
            color: #161616 !important;
        }

        .stApp {
            background-color: #ffffff;
        }

        /* Zero border radius and no shadows */
        div[data-baseweb="input"], 
        div[data-baseweb="select"], 
        div[data-baseweb="textarea"],
        button, 
        .stButton>button,
        .stTextInput>div>div>input,
        .stSelectbox>div>div,
        .stFileUpload {
            border-radius: 0px !important;
            border: 1px solid #e0e0e0 !important;
            box-shadow: none !important;
        }

        /* IBM Blue for buttons and active states */
        .stButton>button {
            background-color: #0f62fe !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            font-weight: 400 !important;
        }

        .stButton>button:hover {
            background-color: #0353e9 !important;
        }

        /* Elevation via borders */
        .stMetric, .stExpander, .stAlert {
            border: 1px solid #e0e0e0 !important;
            border-radius: 0px !important;
            background-color: #f4f4f4 !important;
            box-shadow: none !important;
        }

        /* Remove Streamlit default padding/decorations */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Custom container for surface elevation */
        .carbon-surface {
            background-color: #f4f4f4;
            padding: 1.5rem;
            border: 1px solid #e0e0e0;
            margin-bottom: 1rem;
        }
    </style>
    """
    st.markdown(carbon_css, unsafe_allow_html=True)
