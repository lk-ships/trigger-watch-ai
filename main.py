import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set up OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

st.set_page_config(page_title="Trigger Watch AI", layout="wide")
st.title("🔍 Trigger Watch AI – Workday AE Edition")
st.write("Upload your accounts CSV and get strategic summaries for prospecting.")

# File upload
uploaded_file = st.file_uploader("Upload CSV file with 'Company Name' column", type="csv")

# Dummy trigger data
dummy_triggers = {
    "Brightline": "Hired a new CHRO from Paylocity. Recently announced Series C funding.",
    "EnableComp": "Merged with a healthcare billing firm. CFO joined 3 months ago from HCA.",
    "PhyNet": "Opened a new HQ in Nashville. CEO previously used Workday at another company."
}

def generate_summary(company, trigger):
    prompt = f"""
    You are a top-performing Workday account executive preparing for high-impact outbound prospecting.

    Summarize this company update in 3–5 sharp bullets, as if you're writing prep notes for a call with leadership.

    Each bullet should focus on:
    - Strategic change (exec hire, HQ, funding, M&A, tech shifts)
    - Why this creates disruption or opportunity
    - Relevance to Workday's HCM, Finance, or Planning solutions

    Tone should be tight, confident, and analytical — not promotional. Do not say “reach out now,” “could be a great opportunity,” or “keep an eye.” You are prepping to act, not observe.

    Company: {company}
    Update: {trigger}

    Output (3–5 short bullets):
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return response.choices[0].message.content.strip()

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV uploaded successfully.")
    st.divider()

    for company in df['Company Name']:
        if company in dummy_triggers:
            with st.expander(f"📌 {company} – AI Summary"):
                st.markdown(generate_summary(company, dummy_triggers[company]))
        else:
            with st.expander(f"📌 {company} – No Data Found"):
                st.info("No trigger data available for this account.")
