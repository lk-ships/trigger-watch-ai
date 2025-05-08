import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Page config
st.set_page_config(page_title="Trigger Watch AI", layout="wide")

# === HEADER ===
st.title("🚀 Trigger Watch AI")
st.markdown("##### The CEO Dashboard for Running Your Territory Like a Business")
st.markdown("---")

# === FILE UPLOAD ===
st.subheader("📂 Upload Your Accounts")
st.write("Upload a `.csv` file with a column labeled `Company Name` to receive strategic summaries powered by AI.")

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

# === Dummy Trigger Data ===
dummy_triggers = {
    "Brightline": "Hired a new CHRO from Paylocity. Recently announced Series C funding.",
    "EnableComp": "Merged with a healthcare billing firm. CFO joined 3 months ago from HCA.",
    "PhyNet": "Opened a new HQ in Nashville. CEO previously used Workday at another company."
}

# === Generate GPT Summary ===
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

# === DISPLAY RESULTS ===
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully.")
    st.subheader("📊 AI Strategic Briefs")
    st.caption("Summaries tailored for Workday AEs based on recent company activity.")

    for company in df['Company Name']:
        st.markdown(f"### {company}")
        if company in dummy_triggers:
            summary = generate_summary(company, dummy_triggers[company])
            st.markdown(summary)
            st.markdown("---")
        else:
            st.info("No activity found for this account.")
else:
    st.info("⬆️ Upload a CSV to begin.")
