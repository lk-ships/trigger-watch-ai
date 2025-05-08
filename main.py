import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Configure page
st.set_page_config(page_title="Trigger Watch AI", layout="wide")

# === Inject Custom CSS for Layout and Theme ===
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    background-color: #F8FAFC;
    color: #1E293B;
}

h1, h2, h3 {
    font-weight: 600;
}

.section-header {
    font-size: 22px;
    font-weight: 600;
    margin: 30px 0 10px 0;
}

.card {
    background-color: #FFFFFF;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

.footer {
    text-align: center;
    font-size: 13px;
    color: #94A3B8;
    margin-top: 40px;
}
</style>
""", unsafe_allow_html=True)

# === Header ===
st.markdown("<h1 style='text-align: center;'>🚀 Trigger Watch AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B;'>Your Strategic Command Center for Territory Management</p>", unsafe_allow_html=True)
st.markdown("---")

# === Upload Section ===
st.markdown("<div class='section-header'>📂 Upload Account CSV</div>", unsafe_allow_html=True)
st.write("Upload a `.csv` file with a column named `Company Name`. AI will summarize any known company changes relevant to prospecting.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

# === Dummy Data ===
dummy_triggers = {
    "Brightline": "Hired a new CHRO from Paylocity. Recently announced Series C funding.",
    "EnableComp": "Merged with a healthcare billing firm. CFO joined 3 months ago from HCA.",
    "PhyNet": "Opened a new HQ in Nashville. CEO previously used Workday at another company."
}

# === GPT Summary Logic ===
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

# === Results Section ===
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully.")
    st.markdown("<div class='section-header'>📊 AI Strategic Briefs</div>", unsafe_allow_html=True)

    for company in df['Company Name']:
        if company in dummy_triggers:
            summary = generate_summary(company, dummy_triggers[company])
            st.markdown(f"<div class='card'><h4>{company}</h4><p>{summary}</p></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='card'><h4>{company}</h4><p><i>No activity found for this company.</i></p></div>", unsafe_allow_html=True)
else:
    st.info("⬆️ Upload your account list to begin.")

# === Footer ===
st.markdown("<div class='footer'>Trigger Watch AI | Built for Workday AEs | Powered by OpenAI</div>", unsafe_allow_html=True)
