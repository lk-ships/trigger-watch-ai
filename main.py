import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set up OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Streamlit page config
st.set_page_config(page_title="Trigger Watch AI", layout="wide")

# === UI Header ===
st.title("🚀 Trigger Watch AI")
st.caption("Strategic territory dashboard for Workday AEs")
st.divider()

# === Upload Section ===
st.subheader("📂 Upload Your Account List")
st.write("Upload a `.csv` file with a column named `Company Name`. We'll generate AI-powered summaries with recent context.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

# === Dummy Triggers and Mocked Articles ===
dummy_triggers = {
    "Brightline": "Hired a new CHRO from Paylocity. Recently announced Series C funding.",
    "EnableComp": "Merged with a healthcare billing firm. CFO joined 3 months ago from HCA.",
    "PhyNet": "Opened a new HQ in Nashville. CEO previously used Workday at another company."
}

dummy_articles = {
    "Brightline": [
        {"title": "Brightline Raises Series C Funding", "url": "https://example.com/brightline-funding", "date": "March 2024"},
        {"title": "New CHRO Joins Brightline from Paylocity", "url": "https://example.com/brightline-chro", "date": "Feb 2024"}
    ],
    "EnableComp": [
        {"title": "EnableComp Merges with Billing Partner", "url": "https://example.com/enablecomp-merge", "date": "April 2024"},
    ],
    "PhyNet": [
        {"title": "PhyNet Dermatology Opens New HQ in Nashville", "url": "https://example.com/phynet-hq", "date": "Jan 2024"},
    ]
}

# === AI Summary Function ===
def generate_summary(company, trigger):
    prompt = f"""
You are a top-performing Workday AE preparing for outreach.

Summarize this company update in 3–5 sharp, analytical bullets.

Each bullet must include:
- What happened
- When it happened (e.g., “in Q1 2024,” “in March,” etc.)
- Why it signals disruption or opportunity
- Relevance to Workday’s HR, Finance, or Planning systems

Do not use promotional or salesy language.

Company: {company}
Trigger Update: {trigger}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250
    )
    return response.choices[0].message.content.strip()

# === Display Results ===
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Accounts uploaded successfully!")
    st.subheader("📊 Strategic Briefs")

    for company in df["Company Name"]:
        st.markdown(f"### {company}")
        
        if company in dummy_triggers:
            summary = generate_summary(company, dummy_triggers[company])
            st.markdown(summary)

            # Show related articles
            if company in dummy_articles:
                st.markdown("#### 📰 Related Articles:")
                for article in dummy_articles[company]:
                    st.markdown(f"- [{article['title']}]({article['url']}) <span style='color: gray; font-size: 12px;'>({article['date']})</span>", unsafe_allow_html=True)
            st.markdown("---")
        else:
            st.info("No trigger data available for this account.")
else:
    st.info("⬆️ Upload your CSV file to begin.")
