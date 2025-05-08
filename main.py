import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Set up OpenAI client
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

# Streamlit page config
st.set_page_config(page_title="Trigger Watch AI", layout="wide")

# === QUOTA TRACKER WITH DEAL LOGGING ===
st.markdown("## 📊 Quota Tracker")
st.caption("Track closed deals and see how you're progressing toward your target")

# Initialize session state for deal tracking
if "deals" not in st.session_state:
    st.session_state.deals = []

# Inputs for quota + new deal
quota = st.number_input("Enter your quota target ($)", value=750000, step=10000)

st.markdown("### ➕ Add a Closed Deal")

with st.form("deal_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        account_name = st.text_input("Account Name")
    with col2:
        deal_value = st.number_input("ACV ($)", min_value=0, step=5000)
    with col3:
        quarter_closed = st.selectbox("Quarter Closed", ["Q1", "Q2", "Q3", "Q4"])

    submitted = st.form_submit_button("Add Deal")

    if submitted and account_name and deal_value:
        st.session_state.deals.append({
            "account": account_name,
            "acv": deal_value,
            "quarter": quarter_closed
        })
        st.success(f"✅ Deal added: {account_name} — ${deal_value:,.0f} — {quarter_closed}")

# Display deal table and progress
if st.session_state.deals:
    df_deals = pd.DataFrame(st.session_state.deals)
    total_acv = df_deals["acv"].sum()
    percent_to_quota = (total_acv / quota) * 100 if quota > 0 else 0

    st.markdown("### 📋 Closed Deals")
    st.dataframe(df_deals, use_container_width=True)

    st.markdown(f"### 💰 Booked: ${total_acv:,.0f} / ${quota:,.0f}")
    st.markdown(f"### 📈 Progress: {percent_to_quota:.1f}%")
    st.progress(min(percent_to_quota / 100, 1.0), text=f"{percent_to_quota:.1f}% to goal")

st.divider()

# === APP HEADER ===
st.title("🚀 Trigger Watch AI")
st.caption("Strategic territory dashboard for Workday AEs")
st.divider()

# === UPLOAD SECTION ===
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
        {"title": "PhyNet Opens HQ in Nashville", "url": "https://example.com/phynet-hq", "date": "Jan 2024"},
    ]
}

# === GPT Summary Function ===
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

# === Display AI Briefs ===
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ Accounts uploaded successfully!")
    st.subheader("📊 Strategic Briefs")

    for company in df["Company Name"]:
        st.markdown(f"### {company}")
        
        if company in dummy_triggers:
            summary = generate_summary(company, dummy_triggers[company])
            st.markdown(summary)

            # Related articles
            if company in dummy_articles:
                st.markdown("#### 📰 Related Articles:")
                for article in dummy_articles[company]:
                    st.markdown(f"- [{article['title']}]({article['url']}) <span style='color: gray; font-size: 12px;'>({article['date']})</span>", unsafe_allow_html=True)
            st.markdown("---")
        else:
            st.info("No trigger data available for this account.")
else:
    st.info("⬆️ Upload your CSV file to begin.")
