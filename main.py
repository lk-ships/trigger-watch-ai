import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go

st.set_page_config(page_title="Territory Suite", layout="wide")

# === BRAND STYLE ===
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

# === SIDEBAR ===
st.sidebar.title("📈 Territory Suite")
st.sidebar.caption("The Sales Mainframe")
section = st.sidebar.radio("Navigate", ["🏠 Home", "📊 Quota Tracker", "💼 Closed Deals"])

# === INIT SESSION STATE ===
if "deals" not in st.session_state:
    st.session_state.deals = []
if "quota" not in st.session_state:
    st.session_state.quota = 850000

# === CLOSED DEALS ===
def show_closed_deals():
    st.title("💼 Closed Deals")

    with st.form("deal_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            account_name = st.text_input("Account Name")
        with col2:
            deal_value = st.number_input("ACV ($)", min_value=0, step=5000)
        with col3:
            deal_type = st.selectbox("Deal Type", ["HR", "FINS", "PLN", "Full Suite", "HR + FINS", "FINS + PLN"])
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
                    "deal_type": deal_type,
                    "quarter": quarter_closed
                })
                st.success(f"✅ Deal added: {account_name} — ${deal_value:,.0f} — {quarter_closed}")

    if st.session_state.deals:
        st.markdown("### 📋 Your Closed Deals")
        for i, deal in enumerate(st.session_state.deals):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            col1.markdown(f"**{deal['account']}**")
            col2.markdown(f"${deal['acv']:,.0f}")
            col3.markdown(f"{deal['deal_type']}")
            col4.markdown(f"{deal['quarter']}")
            if col5.button("❌", key=f"delete_{i}"):
                st.session_state.deals.pop(i)
                st.experimental_rerun()

# === QUOTA TRACKER ===
def show_quota_tracker():
    st.title("📊 Quota Tracker")
    st.session_state.quota = st.number_input("Enter your quota target ($)", value=st.session_state.quota, step=10000)

    df = pd.DataFrame(st.session_state.deals)
    if not df.empty:
        df.columns = ["Account", "ACV", "Deal Type", "Quarter"]
        total_acv = df["ACV"].sum()

        # Count logos
        logo_types = ["HR", "FINS", "Full Suite", "HR + FINS", "FINS + PLN"]
        logo_deals = df[df["Deal Type"].isin(logo_types)]
        logo_count = len(logo_deals)

        st.markdown(f"### 💰 Booked: ${total_acv:,.0f} / ${st.session_state.quota:,.0f}")
        st.progress(min(total_acv / st.session_state.quota, 1.0), text=f"{(total_acv / st.session_state.quota) * 100:.1f}% to goal")

        st.markdown(f"### 🧩 Logos: {logo_count} / 4")
        if logo_count < 4:
            st.warning("You're below the minimum logo goal of 4.")
        else:
            st.success("✅ Logo goal met!")

        st.markdown("### 🗂️ Deals That Count Toward Logos")
        st.dataframe(logo_deals, use_container_width=True)
    else:
        st.info("No deals logged yet.")

# === HOME ===
def show_home():
    st.title("🏠 Territory Suite")
    st.subheader("Your Sales Mainframe")

    df = pd.DataFrame(st.session_state.deals)
    total_acv = df["acv"].sum() if not df.empty else 0
    remaining = max(st.session_state.quota - total_acv, 0)

    # Donut Chart
    fig = go.Figure(data=[go.Pie(
        labels=["Booked", "Remaining"],
        values=[total_acv, remaining],
        hole=0.6,
        marker_colors=["#10B981", "#E5E7EB"],
        textinfo="label+percent",
        hoverinfo="label+value"
    )])
    fig.update_layout(title_text="📈 Quota Progress", showlegend=False, height=400,
                      margin=dict(t=40, b=0, l=0, r=0), font=dict(family="Inter", size=14))
    st.plotly_chart(fig, use_container_width=True)

    # Logo Progress
    logo_types = ["HR", "FINS", "Full Suite", "HR + FINS", "FINS + PLN"]
    logo_count = sum(1 for d in st.session_state.deals if d["deal_type"] in logo_types)
    st.markdown("### 🧩 Logos Progress")
    st.progress(min(logo_count / 4, 1.0), text=f"{logo_count} / 4 Logos")

    st.markdown("### 🔧 Coming Soon:")
    st.markdown("- 📊 Top Metrics (Quota % to Goal, Pipeline Coverage)")
    st.markdown("- 🧠 AI-Identified Opportunities")
    st.markdown("- 📅 Deal Calendar & Close Dates")
    st.markdown("- 🔔 Trigger Alerts & Exec Moves")
    st.markdown("- 📥 Recommended Next Actions")

# === ROUTING ===
if section == "🏠 Home":
    show_home()
elif section == "📊 Quota Tracker":
    show_quota_tracker()
elif section == "💼 Closed Deals":
    show_closed_deals()
