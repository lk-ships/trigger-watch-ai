import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import date
import openai
from typing import List, Dict
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    "🏠 Home", "📂 CRM", "📁 Upload Accounts",
    "🧠 AI Account Summaries", "💼 Closed Deals", "📊 Quota Tracker"
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
    
    # Add file upload section
    st.subheader("📁 Upload Closed Deals")
    
    # Create and offer sample template download
    sample_closed_deals = pd.DataFrame({
        "account": ["Example Corp", "Sample Inc"],
        "acv": [50000, 75000],
        "deal_type": ["HR", "FINS"],
        "quarter": ["Q1", "Q2"]
    })
    csv = sample_closed_deals.to_csv(index=False)
    st.download_button(
        label="📥 Download Sample Template",
        data=csv,
        file_name="closed_deals_template.csv",
        mime="text/csv",
        key="closed_deals_template"
    )
    
    uploaded_file = st.file_uploader("Upload Closed Deals CSV", type="csv", key="closed_deals_upload")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = ["account", "acv", "deal_type", "quarter"]
            if all(col in df.columns for col in required_columns):
                for _, row in df.iterrows():
                    if row["account"].lower() not in [d["account"].lower() for d in st.session_state.deals]:
                        st.session_state.deals.append({
                            "account": row["account"],
                            "acv": float(row["acv"]),
                            "deal_type": row["deal_type"],
                            "quarter": row["quarter"]
                        })
                st.success("✅ Closed deals uploaded successfully!")
            else:
                st.error("❌ CSV must contain columns: account, acv, deal_type, quarter")
        except Exception as e:
            st.error(f"❌ Error uploading file: {str(e)}")

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
def get_company_info(company_name: str) -> Dict:
    """Get company information from external APIs"""
    # You can integrate with various APIs here like:
    # - Clearbit
    # - Crunchbase
    # - LinkedIn
    # - Company House
    # For now, we'll return a placeholder
    return {
        "industry": "Technology",
        "employees": "1000-5000",
        "founded": "2010",
        "headquarters": "San Francisco, CA",
        "website": "www.example.com"
    }

def generate_account_summary(company_name: str, company_info: Dict, deals: List[Dict]) -> str:
    """Generate AI summary for an account"""
    try:
        # Prepare context about the company
        company_context = f"""
        Company Name: {company_name}
        Industry: {company_info['industry']}
        Size: {company_info['employees']} employees
        Founded: {company_info['founded']}
        Location: {company_info['headquarters']}
        Website: {company_info['website']}
        """

        # Prepare deal history
        deal_history = ""
        if deals:
            deal_history = "\nDeal History:\n"
            for deal in deals:
                deal_history += f"- {deal['deal_type']} deal worth ${deal['acv']:,.0f} in {deal['quarter']}\n"

        # Generate summary using OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sales intelligence assistant. Generate concise, insightful summaries of companies based on their information and deal history."},
                {"role": "user", "content": f"Generate a concise summary of this company and their relationship with us:\n\n{company_context}\n{deal_history}"}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def show_ai_summaries():
    st.title("🧠 AI Account Summaries")
    
    if st.session_state.uploaded_accounts is not None:
        # Add refresh button
        if st.button("🔄 Refresh Summaries"):
            st.session_state.summaries = {}
            st.experimental_rerun()
            
        # Process each account
        for _, row in st.session_state.uploaded_accounts.iterrows():
            company_name = row['account'] if 'account' in row else row.iloc[0]
            
            # Create expandable section for each company
            with st.expander(f"📊 {company_name}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Get company information
                    company_info = get_company_info(company_name)
                    
                    # Get relevant deals from session state
                    company_deals = [deal for deal in st.session_state.deals 
                                   if deal['account'].lower() == company_name.lower()]
                    
                    # Generate or retrieve summary
                    if 'summaries' not in st.session_state:
                        st.session_state.summaries = {}
                    
                    if company_name not in st.session_state.summaries:
                        with st.spinner(f"Generating summary for {company_name}..."):
                            summary = generate_account_summary(company_name, company_info, company_deals)
                            st.session_state.summaries[company_name] = summary
                    
                    # Display summary
                    st.markdown(st.session_state.summaries[company_name])
                
                with col2:
                    # Display company information
                    st.markdown("### Company Information")
                    for key, value in company_info.items():
                        st.markdown(f"**{key.title()}:** {value}")
                    
                    # Display deal history
                    if company_deals:
                        st.markdown("### Deal History")
                        for deal in company_deals:
                            st.markdown(f"- {deal['deal_type']} (${deal['acv']:,.0f}) - {deal['quarter']}")
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
    
    # Add file upload section
    st.subheader("📁 Upload Pipeline")
    
    # Create and offer sample template download
    sample_pipeline = pd.DataFrame({
        "account": ["Example Corp", "Sample Inc"],
        "acv": [100000, 150000],
        "stage": ["Discovery", "Proposal"],
        "close_date": ["2024-06-30", "2024-07-15"],
        "notes": ["Initial meeting scheduled", "Waiting for legal review"]
    })
    csv = sample_pipeline.to_csv(index=False)
    st.download_button(
        label="📥 Download Sample Template",
        data=csv,
        file_name="pipeline_template.csv",
        mime="text/csv",
        key="pipeline_template"
    )
    
    uploaded_file = st.file_uploader("Upload Pipeline CSV", type="csv", key="pipeline_upload")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = ["account", "acv", "stage", "close_date", "notes"]
            if all(col in df.columns for col in required_columns):
                for _, row in df.iterrows():
                    st.session_state.pipeline.append({
                        "account": row["account"],
                        "acv": float(row["acv"]),
                        "stage": row["stage"],
                        "close_date": row["close_date"],
                        "notes": row["notes"]
                    })
                st.success("✅ Pipeline uploaded successfully!")
            else:
                st.error("❌ CSV must contain columns: account, acv, stage, close_date, notes")
        except Exception as e:
            st.error(f"❌ Error uploading file: {str(e)}")

    with st.form("add_pipeline_opportunity"):
        st.subheader("➕ Add Opportunity")
        col1, col2, col3 = st.columns(3)
        with col1:
            account = st.text_input("Account Name")
        with col2:
            acv = st.number_input("Deal Value (ACV $)", min_value=0, step=5000)
        with col3:
            stage = st.selectbox("Stage", ["Prospecting", "Discovery", "Demo", "Proposal", "Commit", "Closed Won"])
        col4 = st.columns(1)[0]
        with col4:
            close_date = st.date_input("Expected Close Date", value=date.today(), format="MM/DD/YYYY")
        notes = st.text_area("Notes / Next Steps")
        submitted = st.form_submit_button("Add Opportunity")

        if submitted:
            st.session_state.pipeline.append({
                "account": account,
                "acv": acv,
                "stage": stage,
                "close_date": str(close_date),
                "notes": notes
            })
            st.success(f"✅ Opportunity for {account} added.")

    if st.session_state.pipeline:
        st.subheader("📋 Pipeline Table")
        df = pd.DataFrame(st.session_state.pipeline)
        st.dataframe(df[["account", "acv", "stage", "close_date", "notes"]], use_container_width=True)
        st.subheader("📊 Summary")
        st.markdown(f"**Total Pipeline ACV:** ${df['acv'].sum():,.0f}")
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
