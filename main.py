import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
from datetime import date
from openai import OpenAI
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import json

st.set_page_config(page_title="Territory Suite", layout="wide")

# Initialize OpenAI client with Streamlit secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key:
        raise ValueError("API key is empty")
    client = OpenAI(api_key=api_key)
    # Test the client with a simple call
    client.models.list()
except Exception as e:
    st.error(f"⚠️ Error initializing OpenAI client: {str(e)}")
    st.info("Please check your secrets.toml file and make sure it contains a valid OPENAI_API_KEY")
    st.stop()

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

/* Response Text Styles */
.response-text {
    background-color: #f8f9fa;
    color: #212529;
    padding: 1.5rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 1px solid #e9ecef;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    line-height: 1.6;
}
.response-text p {
    margin-bottom: 1rem;
}
.response-text p:last-child {
    margin-bottom: 0;
}
.response-text ul, .response-text ol {
    margin: 1rem 0;
    padding-left: 1.5rem;
}
.response-text li {
    margin-bottom: 0.5rem;
}
.response-text h1, .response-text h2, .response-text h3, .response-text h4 {
    color: #1a1a1a;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}
.response-text code {
    background-color: #e9ecef;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}

/* Call Prep Sheet Styles */
.prep-section {
    background-color: #f8fafc;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid #e2e8f0;
}
.prep-section h3 {
    color: #1e293b;
    margin-bottom: 15px;
}
.prep-section p {
    color: #475569;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.title("📈 Territory Suite")
st.sidebar.caption("The Sales Mainframe")
section = st.sidebar.radio("Navigate", [
    "🏠 Home", "📂 CRM", "📁 Top Targets",
    "🔍 Account Search", "📊 Quota Tracker"
])

# === SESSION STATE INIT ===
if "deals" not in st.session_state:
    st.session_state.deals = []
if "quota" not in st.session_state:
    st.session_state.quota = 850000
if "pipeline" not in st.session_state:
    st.session_state.pipeline = []
if "top_targets" not in st.session_state:
    st.session_state.top_targets = pd.DataFrame(columns=['Company Name', 'Website', 'Last Updated'])
if "uploaded_accounts" not in st.session_state:
    st.session_state.uploaded_accounts = None
if "last_updated" not in st.session_state:
    st.session_state.last_updated = {}

# === HOME ===
def show_home():
    st.title("🏠 Territory Suite")
    st.subheader("Your Sales Mainframe")

    # Initialize session state for deals if not present
    if "deals" not in st.session_state:
        st.session_state.deals = []
    if "quota" not in st.session_state:
        st.session_state.quota = 850000

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
    
    # Initialize quota in session state if not present
    if "quota" not in st.session_state:
        st.session_state.quota = 850000
    
    # Quota input with persistence
    new_quota = st.number_input("Enter your quota target ($)", value=st.session_state.quota, step=10000)
    if new_quota != st.session_state.quota:
        st.session_state.quota = new_quota
        st.success("✅ Quota updated!")
    
    # Calculate and display metrics
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

# === ACCOUNT SEARCH ===
def show_account_search():
    st.title("🔍 Account Search")
    
    # Add custom CSS for the search interface
    st.markdown("""
    <style>
    .search-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .response-text {
        background-color: #f8f9fa;
        color: #212529;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        line-height: 1.6;
    }
    .response-text p {
        margin-bottom: 1rem;
    }
    .response-text p:last-child {
        margin-bottom: 0;
    }
    .response-text ul, .response-text ol {
        margin: 1rem 0;
        padding-left: 1.5rem;
    }
    .response-text li {
        margin-bottom: 0.5rem;
    }
    .response-text h1, .response-text h2, .response-text h3, .response-text h4 {
        color: #1a1a1a;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for different search methods
    tab1, tab2 = st.tabs(["🔍 Search by Name", "📁 Upload CSV"])
    
    with tab1:
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        company_name = st.text_input("Enter Company Name", placeholder="e.g., Acme Corporation")
        if st.button("Search", key="search_name"):
            if company_name:
                try:
                    with st.spinner("Generating company summary..."):
                        # Generate summary
                        summary = generate_company_summary(company_name)
                        
                        if summary.startswith("Error"):
                            st.error(summary)
                        else:
                            # Display the summary in a styled block
                            st.markdown(f"""
                            <div class="response-text">
                                {summary}
                            </div>
                            """, unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    st.info("Please check your internet connection and try again.")
            else:
                st.warning("Please enter a company name")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload Company List (CSV)", type="csv")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                if 'Company Name' not in df.columns:
                    st.error("❌ CSV must contain a 'Company Name' column")
                else:
                    st.success(f"✅ Found {len(df)} companies")
                    for company in df['Company Name']:
                        with st.expander(f"🔍 {company}"):
                            try:
                                with st.spinner(f"Generating summary for {company}..."):
                                    summary = generate_company_summary(company)
                                    if summary.startswith("Error"):
                                        st.error(summary)
                                    else:
                                        st.markdown(f"""
                                        <div class="response-text">
                                            {summary}
                                        </div>
                                        """, unsafe_allow_html=True)
                            except Exception as e:
                                st.error(f"Error generating summary for {company}: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)

# === TOP TARGETS ===
def fetch_company_intelligence(company_name, website):
    """Generate strategic company summary using OpenAI"""
    try:
        # Get recent news
        news = fetch_news(company_name)
        
        # Build the prompt for OpenAI
        prompt = f"""As a senior business strategy expert, create a concise 1-page strategic summary for {company_name} ({website}). Focus on actionable insights and strategic implications.

Recent News:
{news if news else 'No recent news available.'}

Structure your analysis with these exact sections:

**Company Summary:**
- Core business model and market position
- Key products/services and value proposition
- Target markets and customer segments
- Recent strategic initiatives

**Industry Trends:**
- Major market dynamics and competitive landscape
- Regulatory or technological changes
- Economic factors affecting the sector
- Growth opportunities and threats

**Workday Fit/Value:**
- Current technology landscape and gaps
- Potential areas for digital transformation
- Specific Workday value propositions
- ROI scenarios and business impact

**Trigger Events:**
- Recent executive changes or hires
- Funding rounds or financial developments
- M&A activity or partnerships
- Office expansions or relocations
- Other strategic shifts

Format the response in clear, concise bullet points. Focus on insights that would be valuable for a technology sales conversation. If information is not available for a section, indicate that clearly."""

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior business strategy expert providing executive-level company summaries. Focus on strategic insights, actionable intelligence, and clear business implications. Avoid generic statements and prioritize specific, data-driven insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error generating intelligence: {str(e)}"

def show_top_targets():
    st.title("🎯 Top Targets")
    
    # Initialize session state for top targets if not present
    if "top_targets" not in st.session_state:
        st.session_state.top_targets = pd.DataFrame(columns=['Company Name', 'Website', 'Last Updated'])
    if "last_updated" not in st.session_state:
        st.session_state.last_updated = {}
    
    # Add custom CSS for the intelligence cards
    st.markdown("""
    <style>
    .intelligence-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        margin: 24px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .company-header {
        color: #1e293b;
        font-size: 1.5em;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 2px solid #f1f5f9;
    }
    .company-website {
        color: #64748b;
        font-size: 0.9em;
        margin-top: 4px;
    }
    .intelligence-content {
        color: #475569;
        line-height: 1.6;
    }
    .intelligence-content h3 {
        color: #1e293b;
        font-size: 1.2em;
        margin: 20px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #e2e8f0;
    }
    .intelligence-content ul {
        margin: 0;
        padding-left: 20px;
    }
    .intelligence-content li {
        margin-bottom: 8px;
    }
    .last-updated {
        color: #64748b;
        font-size: 0.9em;
        background-color: #f8fafc;
        padding: 4px 8px;
        border-radius: 4px;
    }
    .signal-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .signal-funding { background-color: #dcfce7; color: #166534; }
    .signal-hiring { background-color: #dbeafe; color: #1e40af; }
    .signal-news { background-color: #fef3c7; color: #92400e; }
    .signal-tech { background-color: #f3e8ff; color: #6b21a8; }
    </style>
    """, unsafe_allow_html=True)
    
    # File upload section
    uploaded_file = st.file_uploader("Upload Top Targets CSV", type="csv")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_columns = ['Company Name', 'Website']
            if not all(col in df.columns for col in required_columns):
                st.error("❌ CSV must contain 'Company Name' and 'Website' columns")
                return
                
            # Add timestamp for last update
            df['Last Updated'] = pd.Timestamp.now()
            
            # Update session state
            st.session_state.top_targets = df
            st.success("✅ Top targets uploaded successfully!")
        except Exception as e:
            st.error(f"❌ Error uploading file: {str(e)}")
    
    # Display intelligence cards for each company
    if not st.session_state.top_targets.empty:
        st.markdown("### 📊 Strategic Intelligence Dashboard")
        
        for _, row in st.session_state.top_targets.iterrows():
            company_name = row['Company Name']
            website = row['Website']
            last_updated = row['Last Updated']
            
            # Store last update time in session state
            st.session_state.last_updated[company_name] = last_updated
            
            with st.container():
                st.markdown(f"""
                <div class="intelligence-card">
                    <div class="company-header">
                        <div>
                            <span>{company_name}</span>
                            <div class="company-website">{website}</div>
                        </div>
                        <span class="last-updated">Last updated: {last_updated.strftime('%Y-%m-%d %H:%M')}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Generate and display intelligence
                with st.spinner(f"Generating strategic summary for {company_name}..."):
                    intelligence = fetch_company_intelligence(company_name, website)
                    
                    # Add signal badges if available
                    if "funding" in intelligence.lower():
                        st.markdown('<span class="signal-badge signal-funding">💰 Funding Update</span>', unsafe_allow_html=True)
                    if "hire" in intelligence.lower() or "appoint" in intelligence.lower():
                        st.markdown('<span class="signal-badge signal-hiring">👥 Executive Change</span>', unsafe_allow_html=True)
                    if "news" in intelligence.lower():
                        st.markdown('<span class="signal-badge signal-news">📰 Recent News</span>', unsafe_allow_html=True)
                    if "workday" in intelligence.lower() or "hris" in intelligence.lower() or "erp" in intelligence.lower():
                        st.markdown('<span class="signal-badge signal-tech">💻 Tech Signal</span>', unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div class="intelligence-content">
                        {intelligence}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("👆 Upload a CSV file with your top target accounts to get started.")

# === UPLOAD ACCOUNTS ===
def show_upload_section():
    st.title("📁 Top Targets")
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
                # Clear existing pipeline if new file is uploaded
                st.session_state.pipeline = []
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
            acv = st.number_input("Deal Value (ACV $)", min_value=0.0, step=5000.0, value=0.0)
        with col3:
            stage = st.selectbox("Stage", ["Prospecting", "Discovery", "Demo", "Proposal", "Commit", "Closed Won"])
        col4 = st.columns(1)[0]
        with col4:
            close_date = st.date_input("Expected Close Date", value=date.today(), format="MM/DD/YYYY")
        notes = st.text_area("Notes / Next Steps")
        submitted = st.form_submit_button("Add Opportunity")

        if submitted:
            if stage == "Closed Won":
                # Add directly to closed deals
                st.session_state.deals.append({
                    "account": account,
                    "acv": float(acv),
                    "deal_type": "HR",  # Default to HR, can be updated later
                    "quarter": f"Q{(date.today().month-1)//3 + 1}"  # Current quarter
                })
                st.success(f"✅ Deal for {account} added to Closed Won.")
            else:
                # Add to pipeline
                st.session_state.pipeline.append({
                    "account": account,
                    "acv": float(acv),
                    "stage": stage,
                    "close_date": str(close_date),
                    "notes": notes
                })
                st.success(f"✅ Opportunity for {account} added to pipeline.")

    # Display Active Pipeline
    if st.session_state.pipeline:
        st.subheader("📋 Active Pipeline")
        
        # Filter out any deals that might have been marked as Closed Won
        active_pipeline = [deal for deal in st.session_state.pipeline if deal['stage'] != "Closed Won"]
        
        # Process each deal for potential updates
        for i, deal in enumerate(active_pipeline):
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])
            
            # Account name (read-only)
            col1.markdown(f"**{deal['account']}**")
            
            # ACV (editable)
            new_acv = col2.number_input(
                "ACV",
                value=float(deal['acv']),
                min_value=0.0,
                step=5000.0,
                key=f"acv_{i}"
            )
            
            # Stage (editable)
            new_stage = col3.selectbox(
                "Stage",
                ["Prospecting", "Discovery", "Demo", "Proposal", "Commit", "Closed Won"],
                index=["Prospecting", "Discovery", "Demo", "Proposal", "Commit", "Closed Won"].index(deal['stage']),
                key=f"stage_{i}"
            )
            
            # Notes (editable)
            new_notes = col4.text_area(
                "Notes",
                value=deal['notes'],
                key=f"notes_{i}"
            )
            
            # Find the actual index in session state
            actual_index = next((idx for idx, d in enumerate(st.session_state.pipeline) 
                               if d['account'] == deal['account']), None)
            
            if actual_index is not None:
                # Handle ACV changes
                if new_acv != deal['acv']:
                    st.session_state.pipeline[actual_index]['acv'] = float(new_acv)
                
                # Handle stage changes
                if new_stage != deal['stage']:
                    if new_stage == "Closed Won":
                        # Add to closed deals
                        st.session_state.deals.append({
                            "account": deal['account'],
                            "acv": float(deal['acv']),
                            "deal_type": "HR",
                            "quarter": f"Q{(date.today().month-1)//3 + 1}"
                        })
                        # Remove from pipeline
                        st.session_state.pipeline.pop(actual_index)
                    else:
                        st.session_state.pipeline[actual_index]['stage'] = new_stage
                
                # Handle notes changes
                if new_notes != deal['notes']:
                    st.session_state.pipeline[actual_index]['notes'] = new_notes
                
                # Handle delete
                if col5.button("❌", key=f"delete_{i}"):
                    st.session_state.pipeline.pop(actual_index)
            
            st.markdown("---")
        
        # Display summary
        st.subheader("📊 Pipeline Summary")
        df = pd.DataFrame(active_pipeline)
        total_acv = df['acv'].sum()
        st.markdown(f"**Total Pipeline ACV:** ${total_acv:,.0f}")
        
        # Stage breakdown
        for stage in ["Prospecting", "Discovery", "Demo", "Proposal", "Commit"]:
            stage_deals = df[df['stage'] == stage]
            if not stage_deals.empty:
                st.markdown(f"- **{stage}**: {len(stage_deals)} deals (${stage_deals['acv'].sum():,.0f})")
    else:
        st.info("No deals in pipeline.")

    # Display Closed Won Deals
    if st.session_state.deals:
        st.subheader("🏆 Closed Won Deals")
        for i, deal in enumerate(st.session_state.deals):
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            col1.markdown(f"**{deal['account']}**")
            col2.markdown(f"${deal['acv']:,.0f}")
            col3.markdown(f"{deal['deal_type']}")
            col4.markdown(f"{deal['quarter']}")
            if col5.button("❌", key=f"delete_closed_{i}"):
                st.session_state.deals.pop(i)
            st.markdown("---")
        
        # Calculate and display total Closed Won ACV
        total_closed_acv = sum(deal['acv'] for deal in st.session_state.deals)
        st.markdown(f"**Total Closed Won ACV:** ${total_closed_acv:,.0f}")
        
        # Display progress towards quota if quota is set
        if st.session_state.quota:
            quota_percentage = (total_closed_acv / st.session_state.quota) * 100
            st.progress(min(quota_percentage / 100, 1.0), text=f"{quota_percentage:.1f}% to quota")

# === CALL PREP SHEET ===
def extract_company_info(url):
    """Extract basic company information from website"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get company name from title
        company_name = soup.title.string if soup.title else urlparse(url).netloc
        
        # Get meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        description = meta_desc['content'] if meta_desc else ""
        
        return {
            "name": company_name,
            "description": description,
            "url": url
        }
    except Exception as e:
        return {
            "name": urlparse(url).netloc,
            "description": "",
            "url": url
        }

def fetch_news(company_name):
    """Fetch recent news about a company using NewsData.io API"""
    try:
        # Get NewsData API key from Streamlit secrets
        newsdata_api_key = st.secrets.get("NEWSDATA_API_KEY")
        if not newsdata_api_key:
            st.warning("⚠️ NewsData.io API key not configured. Please add NEWSDATA_API_KEY to your secrets.toml file.")
            return None

        # NewsData.io API endpoint
        search_url = "https://newsdata.io/api/1/news"
        
        # Prepare the request
        params = {
            'apikey': newsdata_api_key,
            'q': company_name,
            'language': 'en',
            'size': 5  # Get 5 most recent articles
        }

        # Make the API call
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        news_data = response.json()

        if not news_data.get('results'):
            st.warning(f"⚠️ No recent news found for {company_name}")
            return None

        # Format the news articles
        news_items = []
        for article in news_data['results']:
            title = article.get('title', 'No title')
            description = article.get('description', 'No description')
            pub_date = article.get('pubDate', 'No date')
            link = article.get('link', '#')
            
            # Format the date
            try:
                from datetime import datetime
                date_obj = datetime.strptime(pub_date, "%Y-%m-%d %H:%M:%S")
                formatted_date = date_obj.strftime("%B %d, %Y")
            except:
                formatted_date = pub_date

            # Format each article as a markdown bullet point
            news_items.append(f"* **{title}** ({formatted_date})\n  {description}\n  [Read more]({link})")

        # Return formatted news as a markdown list
        return "\n\n".join(news_items)

    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return None

def generate_prep_sheet(company_info):
    """Generate call prep sheet using OpenAI"""
    try:
        # Get company name and recent news
        company_name = company_info['name']
        recent_news = fetch_news(company_name)
        
        # Build the prompt
        prompt = f"""You are a senior business strategy expert preparing a high-level briefing for a technology sales executive. Your analysis should focus on strategic implications, growth opportunities, and technology enablement.

Company Name: {company_name}

Recent Updates:
{recent_news if recent_news else "No recent news available."}

Create a strategic analysis that connects recent developments to business outcomes and technology opportunities. Structure your response with these sections:

**Strategic Business Context:**
- Core business model and market position
- Key growth drivers and revenue streams
- Recent strategic moves (M&A, funding, leadership changes)
- Competitive dynamics and market share implications

**Growth Triggers & Risk Factors:**
- Recent funding rounds and their strategic implications
- M&A activity and integration challenges/opportunities
- Leadership changes and organizational impact
- Regulatory changes affecting business model
- Market expansion or contraction signals

**Technology Enablement Opportunities:**
- Current technology gaps affecting growth or margins
- Digital transformation initiatives in progress
- Specific areas where Workday could drive:
  * Revenue expansion (e.g., new market entry, product innovation)
  * Margin improvement (e.g., operational efficiency, cost reduction)
  * Risk mitigation (e.g., compliance, talent management)
  * Strategic advantage (e.g., data-driven decision making)

**Executive Conversation Starters:**
- Key business challenges to explore
- Strategic initiatives to align with
- Metrics that matter to the executive team
- Recent developments to reference
- Potential ROI scenarios to discuss

Important:
- Use the exact company name: {company_name}
- Focus on strategic implications, not just facts
- Connect recent news to business outcomes
- Frame insights in terms of revenue, margin, and growth
- Use markdown formatting with bold headers and bullet points
- Be specific and cite relevant information from the news
- Maintain an executive-level perspective throughout"""

        st.write("Sending request to OpenAI...")  # Debug info
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior business strategy expert with deep experience in technology transformation. Your analysis should demonstrate strategic thinking, connect dots between recent developments and business outcomes, and focus on executive-level insights. Avoid generic statements and focus on specific, actionable insights that matter to C-level executives."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        st.write("Received response from OpenAI")  # Debug info
        
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Detailed error: {str(e)}")  # More detailed error message
        return f"Error generating prep sheet: {str(e)}"

def show_call_prep():
    st.title("📞 Call Prep Sheet")
    
    # Add custom CSS for the prep sheet styling
    st.markdown("""
    <style>
    .prep-sheet-container {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .prep-section {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #e2e8f0;
    }
    .prep-section h3 {
        color: #1e293b;
        margin-bottom: 15px;
        font-size: 1.2em;
    }
    .prep-content {
        color: #475569;
        line-height: 1.6;
        margin: 0;
    }
    .news-updates {
        background-color: #f0f9ff;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #bae6fd;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.info("You can set it by running: export OPENAI_API_KEY=your_api_key_here")
        return
    
    # URL input
    url = st.text_input("Enter Company Website URL", placeholder="https://www.example.com")
    
    if st.button("Generate Prep Sheet"):
        if url:
            try:
                with st.spinner("Analyzing company and generating prep sheet..."):
                    # Extract company info
                    company_info = extract_company_info(url)
                    
                    # Create main container for the prep sheet
                    with st.container():
                        st.markdown('<div class="prep-sheet-container">', unsafe_allow_html=True)
                        
                        # Company header
                        st.markdown(f"## {company_info['name']}")
                        st.markdown("---")
                        
                        # Get recent news
                        recent_news = fetch_news(company_info['name'])
                        if recent_news:
                            st.markdown('<div class="news-updates">', unsafe_allow_html=True)
                            st.markdown("### 📰 Recent Company Updates")
                            st.markdown(f"""
                            <div class="prep-content">
                                {recent_news}
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.write("")
                        
                        # Generate prep sheet
                        prep_content = generate_prep_sheet(company_info)
                        
                        if prep_content.startswith("Error"):
                            st.error(prep_content)
                            return
                        
                        # Company Summary
                        st.markdown('<div class="prep-section">', unsafe_allow_html=True)
                        st.markdown("### 📌 Company Summary")
                        st.markdown(f"""
                        <div class="prep-content">
                            {extract_section(prep_content, "Strategic Business Context") or "_No data available._"}
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.write("")
                        
                        # Industry Trends
                        st.markdown('<div class="prep-section">', unsafe_allow_html=True)
                        st.markdown("### 📈 Industry Trends")
                        st.markdown(f"""
                        <div class="prep-content">
                            {extract_section(prep_content, "Growth Triggers & Risk Factors") or "_No data available._"}
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.write("")
                        
                        # Workday Fit/Value
                        st.markdown('<div class="prep-section">', unsafe_allow_html=True)
                        st.markdown("### 💼 Workday Fit/Value")
                        st.markdown(f"""
                        <div class="prep-content">
                            {extract_section(prep_content, "Technology Enablement Opportunities") or "_No data available._"}
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.write("")
                        
                        # Trigger Events
                        st.markdown('<div class="prep-section">', unsafe_allow_html=True)
                        st.markdown("### 🚨 Trigger Events")
                        st.markdown(f"""
                        <div class="prep-content">
                            {extract_section(prep_content, "Executive Conversation Starters") or "_No data available._"}
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your internet connection and try again.")
        else:
            st.warning("Please enter a company website URL")

def extract_section(content, section_name):
    """Extract a specific section from the GPT response"""
    try:
        # Find the section header
        start_idx = content.find(f"**{section_name}:**")
        if start_idx == -1:
            return None
            
        # Find the next section or end of content
        next_section = content.find("**", start_idx + len(section_name) + 4)
        if next_section == -1:
            # This is the last section
            return content[start_idx:].strip()
        else:
            # Extract until the next section
            return content[start_idx:next_section].strip()
    except:
        return None

# === ROUTER ===
if section == "🏠 Home":
    show_home()
elif section == "📊 Quota Tracker":
    show_quota_tracker()
elif section == "🔍 Account Search":
    show_account_search()
elif section == "📁 Top Targets":
    show_top_targets()
elif section == "📂 CRM":
    show_crm_pipeline()
