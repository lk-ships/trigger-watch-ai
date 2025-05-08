import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Page config
st.set_page_config(page_title="Trigger Watch AI", layout="wide")

# === HEADER ===
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        font-size: 40px;
        font-weight: bold;
        padding-top: 10px;
        color: #222;
    }
    .sub-header {
        text-align: center;
        font-size: 18px;
        color: #666;
        margin-bottom: 20px;
    }
    .card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 30px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-header'>🚀 Trigger Watch AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Your Executive Command Center for Strategic Sales Prospecting</div>", unsafe_allow_html=True)

# === FILE UPLOAD ===
st.markdown("<div class='section-title'>📂 Upload Your Accounts</div>", unsafe_allow_html=True)
