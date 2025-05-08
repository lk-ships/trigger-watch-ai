
import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Territory Suite", layout="wide")

# === STYLES ===
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
section = st.sidebar.radio("Navigate", [
    "🏠 Home", "📊 Quota Tracker", "💼 Closed Deals",
    "🧠 AI Account Summaries", "📁 Upload Accounts", "📂 CRM"
])

# === SESSION STATE INIT ===
if "deals" not in st.session_state:
    st.session_state.deals = []
if "quota" not in st.session_state:
    st.session_state.quota = 850000
if "pipeline" not in st.session_state:
    st.session_state.pipeline = []
if "uploaded_accounts" not in st.session_state:
    st.session_state.uploaded_accounts = None

# === HOME ===
def show_home():
    st.title("🏠 Territory Suite")
    st.subheader("Your Sales Mainframe")

    df = pd.DataFrame(st.session_state.deals)
    total_acv = df["acv"].sum() if not df.empty else 0
    remaining = max(st.session_state.quota - total_acv, 0)

    fig = go.Figure(data=[go.Pie(
        labels=["Booked", "Remaining"],
        values=[total_acv, remaining],
        hole=.6,
        marker_colors=["#10B981", "#E5E7EB"],
        textinfo='label+percent',
        hoverinfo='label+value'
    )])
    fig.update_layout(title_text="📈 Quota Progress", showlegend=False, height=400,
                      margin=dict(t=40, b=0, l=0, r=0), font=dict(family="Inter", size=14))
    st.plotly_chart(fig, use_container_width=True)

    logo_types = ["HR", "FINS", "Full Suite", "HR + FINS", "FINS + PLN"]
    logo_count = sum(1 for d in st.session_state.deals if d["deal_type"] in logo_types)
    st.markdown("### 🧩 Logos Progress")
    st.progress(min(logo_count / 4, 1.0), text=f"{logo_count} / 4 Logos")

# === QUOTA TRACKER ===
def show_quota_tracker():
    st.title("📊 Quota Tracker")
    st.session_state.quota = st.number_input("Enter your quota target ($)", value=st.session_state.quota, step=10000)

    df = pd.DataFrame(st.session_state.deals)
    if not df.empty:
        df.columns = ["Account", "ACV", "Deal Type", "Quarter"]
        total_acv = df["ACV"].sum()
        logo_types = ["HR", "FINS", "Full Suite", "HR + FINS", "FINS + PLN"]
        logo_deals = df[df["Deal Type"].isin(logo_types)]
        logo_count = len(logo_deals)

        st.markdown(f"### 💰 Booked: ${total_acv:,.0f} / ${st.session_state.quota:,.0f}")
        st.progress(min(total_acv / st.session_state.quota, 1.0), text=f"{(total_acv / st.session_state.quota) * 100:.1f}% to goal")
        st.markdown(f"### 🧩 Logos: {logo_count} / 4")
        st.dataframe(logo_deals, use_container_width=True)
    else:
        st.info("No deals logged yet.")

# === CLOSED DEALS ===
def show_closed_deals():
    st.title("💼 Closed Deals")
with open("sample_closed_deals_upload_named.csv", "rb") as f:
    st.download_button(
        label="📥 Download Template",
        data=f,
        file_name="sample_closed_deals_upload_named.csv",
        mime="text/csv"
    )

    st.subheader("📤 Upload Closed Deals CSV")
    uploaded_deals_file = st.file_uploader("Upload CSV for Closed Deals", type="csv", key="closed_deals")
    if uploaded_deals_file:
        try:
            df_uploaded = pd.read_csv(uploaded_deals_file)
            required_cols = {"account", "acv", "deal_type", "quarter"}
            if required_cols.issubset(df_uploaded.columns):
                for _, row in df_uploaded.iterrows():
                    if row["account"].lower() not in [d["account"].lower() for d in st.session_state.deals]:
                        st.session_state.deals.append({
                            "account": row["account"],
                            "acv": row["acv"],
                            "deal_type": row["deal_type"],
                            "quarter": row["quarter"]
                        })
                st.success("✅ Uploaded closed deals added.")
            else:
                st.warning("⚠️ CSV must include columns: account, acv, deal_type, quarter")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")


def show_closed_deals():
    st.title("💼 Closed Deals")
with open("closed_deals_template.csv", "rb") as f:
    st.download_button(
        label="📥 Download Template",
        data=f,
        file_name="sample_closed_deals_upload_named.csv",
        mime="text/csv"
    )
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
        existing_accounts = [d["account"].lower() for d in st.session_state.deals]

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
                st.success(f"✅ Deal added: {account_name}")

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

# === AI ACCOUNT SUMMARIES (DUMMY) ===
def show_ai_summaries():
    st.title("🧠 AI Account Summaries")
    if st.session_state.uploaded_accounts is not None:
        st.markdown("Summaries coming soon...")
        st.dataframe(st.session_state.uploaded_accounts)
    else:
        st.info("⬆️ Upload an account list first from the sidebar.")

# === UPLOAD ACCOUNTS ===
def show_upload_section():
    st.title("📁 Upload Account List")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_accounts = df
        st.success("✅ File uploaded.")
        st.dataframe(df)

# === CRM PIPELINE ===
def show_crm_pipeline():
    st.title("📂 CRM – Pipeline Manager")
with open("sample_crm_upload_named.csv", "rb") as f:
    st.download_button(
        label="📥 Download Template",
        data=f,
        file_name="sample_crm_upload_named.csv",
        mime="text/csv"
    )

    st.subheader("📤 Upload Opportunities CSV")
    uploaded_pipeline_file = st.file_uploader("Upload CSV for Pipeline", type="csv", key="pipeline")
    if uploaded_pipeline_file:
        try:
            df_uploaded = pd.read_csv(uploaded_pipeline_file)
            required_cols = {"account", "acv", "stage", "confidence", "close_date", "notes"}
            if required_cols.issubset(df_uploaded.columns):
                for _, row in df_uploaded.iterrows():
                    st.session_state.pipeline.append({
                        "account": row["account"],
                        "acv": row["acv"],
                        "stage": row["stage"],
                        "confidence": row["confidence"],
                        "close_date": row["close_date"],
                        "notes": row["notes"]
                    })
                st.success("✅ Uploaded opportunities added.")
            else:
                st.warning("⚠️ CSV must include columns: account, acv, stage, confidence, close_date, notes")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")


def show_crm_pipeline():
    st.title("📂 CRM – Pipeline Manager")
with open("crm_template.csv", "rb") as f:
    st.download_button(
        label="📥 Download Template",
        data=f,
        file_name="sample_crm_upload_named.csv",
        mime="text/csv"
    )
    with st.form("add_pipeline_opportunity"):
        st.subheader("➕ Add Opportunity")
        col1, col2, col3 = st.columns(3)
        with col1:
            account = st.text_input("Account Name")
        with col2:
            acv = st.number_input("Deal Value (ACV $)", min_value=0, step=5000)
        with col3:
            stage = st.selectbox("Stage", ["Prospecting", "Discovery", "Demo", "Proposal", "Commit", "Closed Won"])
        col4, col5 = st.columns(2)
        with col4:
            confidence = st.slider("Confidence (%)", 0, 100, 50)
        with col5:
            close_date = st.date_input("Expected Close Date", value=date.today())
        notes = st.text_area("Notes / Next Steps")
        submitted = st.form_submit_button("Add Opportunity")

        if submitted:
            st.session_state.pipeline.append({
                "account": account,
                "acv": acv,
                "stage": stage,
                "confidence": confidence,
                "close_date": str(close_date),
                "notes": notes
            })
            st.success(f"✅ Opportunity for {account} added.")

    if st.session_state.pipeline:
        st.subheader("📋 Pipeline Table")
        df = pd.DataFrame(st.session_state.pipeline)
        df["Weighted ACV"] = df["acv"] * (df["confidence"] / 100)
        st.dataframe(df[["account", "acv", "stage", "confidence", "close_date", "notes", "Weighted ACV"]], use_container_width=True)
        st.subheader("📊 Summary")
        st.markdown(f"**Total Pipeline ACV:** ${df['acv'].sum():,.0f}")
        st.markdown(f"**Weighted Pipeline:** ${df['Weighted ACV'].sum():,.0f}")
        for stage in df["stage"].unique():
            st.markdown(f"- **{stage}**: {df[df['stage'] == stage].shape[0]} deals")
    else:
        st.info("No deals in pipeline.")

# === ROUTER ===
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
elif section == "📂 CRM":
    show_crm_pipeline()
