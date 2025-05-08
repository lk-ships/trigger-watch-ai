import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from openai import OpenAI

# Setup
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
st.set_page_config(page_title="Territory Suite", layout="wide")

# === CUSTOM FONT & BRAND STYLE ===
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stDataFrame th {
        text-transform: capitalize;
        font-weight: 600;
    }

    .stTextInput label, .stNumberInput label, .stSelectbox label {
        font-weight: 600;
    }

    .stCaption {
        color: #64748B;
        font-size: 14px;
    }

    .stProgress > div > div > div {
        font-weight: 600 !important;
    }

    header .st-emotion-cache-18ni7ap { visibility: hidden; }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# === SIDEBAR MENU ===
st.sidebar.title("📈 Territory Suite")
st.sidebar.caption("The Sales Mainframe")
section = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📊 Quota Tracker", "💼 Closed Deals", "🧠 AI Account Summaries", "📁 Upload Accounts"]
)

# === SESSION STATE INIT ===
if "deals" not in st.session_state:
    st.session_state.deals = []
if "uploaded_accounts" not in st.session_state:
    st.session_state.uploaded_accounts = None
if "quota" not in st.session_state:
    st.session_state.quota = 750000

# === QUOTA CALC ===
def show_quota_tracker():
    st.title("📊 Quota Tracker")
    st.session_state.quota = st.number_input("Enter your quota target ($)", value=st.session_state.quota, step=10000)

    df_deals = pd.DataFrame(st.session_state.deals)
    if not df_deals.empty:
        df_deals.columns = ["Account", "ACV", "Quarter"]
        total_acv = df_deals["ACV"].sum()
        percent_to_quota = (total_acv / st.session_state.quota) * 100 if st.session_state.quota > 0 else 0

        st.markdown(f"### 💰 Booked: ${total_acv:,.0f} / ${st.session_state.quota:,.0f}")
        st.markdown(f"### 📈 Progress: {percent_to_quota:.1f}%")
        st.progress(min(percent_to_quota / 100, 1.0), text=f"{percent_to_quota:.1f}% to goal")
    else:
        st.info("No deals logged yet.")

# === CLOSED DEAL ENTRY ===
def show_closed_deals():
    st.title("💼 Closed Deals")

    with st.form("deal_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            account_name = st.text_input("Account Name")
        with col2:
            deal_value = st.number_input("ACV ($)", min_value=0, step=5000)
        with col3:
            quarter_closed = st.selectbox("Quarter Closed", ["Q1", "Q2", "Q3", "Q4"])

        submitted = st.form_submit_button("Add Deal")

        existing_accounts = [deal["account"].lower() for deal in st.session_state.deals]

        if submitted:
            if not account_name or deal_value == 0:
                st.warning("Please enter a valid account name and ACV greater than $0.")
            elif account_name.lower() in existing_accounts:
                st.warning("🚫 This account is already in your closed deal list.")
            else:
                st.session_state.deals.append({
                    "account": account_name,
                    "acv": deal_value,
                    "quarter": quarter_closed
                })
                st.success(f"✅ Deal added: {account_name} — ${deal_value:,.0f} — {quarter_closed}")

    if st.session_state.deals:
        df = pd.DataFrame(st.session_state.deals)
        df.columns = ["Account", "ACV", "Quarter"]
        st.dataframe(df, use_container_width=True)

# === AI SUMMARIES ===
def show_ai_summaries():
    st.title("🧠 AI Account Summaries")

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

    if st.session_state.uploaded_accounts is not None:
        st.subheader("📊 Strategic Briefs")

        for company in st.session_state.uploaded_accounts["Company Name"]:
            st.markdown(f"### {company}")
            if company in dummy_triggers:
                summary = generate_summary(company, dummy_triggers[company])
                st.markdown(summary)

                if company in dummy_articles:
                    st.markdown("#### 📰 Related Articles:")
                    for article in dummy_articles[company]:
                        st.markdown(
                            f"- [{article['title']}]({article['url']}) "
                            f"<span style='color: gray; font-size: 12px;'>({article['date']})</span>",
                            unsafe_allow_html=True
                        )
                st.markdown("---")
            else:
                st.info("No trigger data available for this account.")
    else:
        st.info("⬆️ Upload an account list first from the sidebar.")

# === UPLOAD ACCOUNTS ===
def show_upload_section():
    st.title("📁 Upload Account List")
    st.write("Upload a `.csv` file with a column labeled `Company Name`.")

    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_accounts = df
        st.success("✅ File uploaded and stored for AI analysis.")
        st.dataframe(df)

# === HOME DASHBOARD ===
def show_home():
    st.title("🏠 Territory Suite")
    st.subheader("Your Sales Mainframe")

    df_deals = pd.DataFrame(st.session_state.deals)
    total_acv = df_deals["acv"].sum() if not df_deals.empty else 0
    remaining = max(st.session_state.quota - total_acv, 0)

 import plotly.graph_objects as go

# Donut chart using Plotly
fig = go.Figure(data=[go.Pie(
    labels=["Booked", "Remaining"],
    values=[total_acv, remaining],
    hole=.6,
    marker_colors=["#10B981", "#E5E7EB"],
    textinfo='label+percent',
    hoverinfo='label+value'
)])
fig.update_layout(
    title_text="📈 Quota Progress",
    showlegend=False,
    height=400,
    margin=dict(t=40, b=0, l=0, r=0),
    font=dict(family="Inter", size=14)
)

st.plotly_chart(fig, use_container_width=True)


    st.markdown("### 🔧 Coming Soon:")
    st.markdown("- 📊 Top Metrics (Quota % to Goal, Pipeline Coverage)")
    st.markdown("- 🧠 AI-Identified Opportunities")
    st.markdown("- 📅 Deal Calendar & Close Dates")
    st.markdown("- 🔔 Trigger Alerts & Exec Moves")
    st.markdown("- 📥 Recommended Next Actions")

# === SECTION ROUTER ===
if section == "🏠 Home":
    show_home()
elif section == "📊 Quota Tracker":
    show_quota_tracker()
elif section == "💼 Closed Deals":
    show_closed_deals()
elif section == "🧠 AI Account Summaries":
    show_ai_summaries()
elif section == "📁 Upload Accounts":
    show_upload_section()
