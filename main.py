import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Territory Suite", layout="wide")

st.sidebar.title("📈 Territory Suite")
st.sidebar.caption("The Sales Mainframe")
section = st.sidebar.radio("Navigate", [
    "🏠 Home", "📊 Quota Tracker", "💼 Closed Deals",
    "📂 CRM"
])

if "deals" not in st.session_state:
    st.session_state.deals = []
if "quota" not in st.session_state:
    st.session_state.quota = 850000
if "pipeline" not in st.session_state:
    st.session_state.pipeline = []

def show_home():
    st.title("🏠 Territory Suite")
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

def show_quota_tracker():
    st.title("📊 Quota Tracker")
    st.session_state.quota = st.number_input("Enter your quota target ($)", value=st.session_state.quota, step=10000)
    df = pd.DataFrame(st.session_state.deals)
    if not df.empty:
        total_acv = df["acv"].sum()
        st.markdown(f"### 💰 Booked: ${total_acv:,.0f} / ${st.session_state.quota:,.0f}")
        st.progress(min(total_acv / st.session_state.quota, 1.0), text=f"{(total_acv / st.session_state.quota) * 100:.1f}% to goal")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No deals logged yet.")

def show_closed_deals():
    st.title("💼 Closed Deals")
    st.markdown("### 📤 Upload CSV for Closed Deals")
    uploaded_deals_file = st.file_uploader("Upload CSV for Closed Deals", type="csv", key="closed_deals_upload")
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
                st.warning("⚠️ CSV must include: account, acv, deal_type, quarter")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

    with open("sample_closed_deals_upload_named.csv", "rb") as f:
        st.download_button("📥 Download Template", f, file_name="sample_closed_deals_upload_named.csv", mime="text/csv")

def show_crm_pipeline():
    st.title("📂 CRM – Pipeline Manager")
    with st.form("add_pipeline_opportunity"):
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
                "close_date": close_date.strftime("%m/%d/%Y"),
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
        for stage in df["stage"].unique():
            st.markdown(f"- **{stage}**: {df[df["stage"] == stage].shape[0]} deals")
    else:
        st.info("No deals in pipeline.")

# === ROUTER ===
if section == "🏠 Home":
    show_home()
elif section == "📊 Quota Tracker":
    show_quota_tracker()
elif section == "💼 Closed Deals":
    show_closed_deals()
elif section == "📂 CRM":
    show_crm_pipeline()
