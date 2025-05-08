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
    "🏠 Home", "📂 CRM", "📁 Upload Accounts",
    "🧠 AI Account Summaries", "💼 Closed Deals", "📊 Quota Tracker", "📞 Call Prep Sheet"
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
            return "NewsData.io API key not configured. Please add NEWSDATA_API_KEY to your secrets.toml file."

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
            return "No recent articles found."

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
        return f"Error fetching news: {str(e)}"

def generate_prep_sheet(company_info):
    """Generate call prep sheet using OpenAI"""
    try:
        # Get recent news using company name
        company_name = company_info['name']
        recent_news = fetch_news(company_name)
        
        prompt = f"""You are a sales intelligence analyst preparing a call prep brief. Based on the following recent company news:

{recent_news}

Create a comprehensive call prep summary that incorporates insights from the news above. Structure your response with these sections:

**Company Overview:**
- Brief summary of what the company does
- Headquarters location
- Whether the company is private or public
- Estimated employee size
- Industry classification

**Industry Trends:**
- Outline key trends, challenges, or economic forces shaping their industry
- Focus on insights relevant to business leaders (e.g. CFOs, CHROs, CEOs)
- Include relevant insights if they are in healthcare, staffing, tech, or retail

**Workday Value:**
- Based on the company's industry and size, explain why Workday would be a strong fit
- Highlight specific modules or functionality that are especially relevant (e.g. HR, finance, planning)
- Be specific to the company and industry where possible

**Sales Triggers:**
- Recent events like funding rounds, acquisitions, new executive hires (CEO, CHRO, CFO), new office openings, major PR/news events
- Try to identify real, recent signals the rep could act on in conversation

Format your response using markdown with bold headers and bullet points. Be specific and cite relevant information from the news articles provided. Focus on actionable insights that would be valuable for a sales call."""

        st.write("Sending request to OpenAI...")  # Debug info
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sales intelligence assistant helping to prepare for a sales call. Your responses should be detailed, specific, and incorporate insights from recent news articles. Use markdown formatting with bold headers and bullet points for clarity."},
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
                    
                    # Get recent news
                    recent_news = fetch_news(company_info['name'])
                    if recent_news and not recent_news.startswith("Error"):
                        st.markdown(f"""
                        <div class="response-text">
                            <h3>📰 Recent Company Updates</h3>
                            {recent_news}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Generate prep sheet
                    prep_content = generate_prep_sheet(company_info)
                    
                    if prep_content.startswith("Error"):
                        st.error(prep_content)
                        return
                    
                    # Display results in styled sections
                    st.markdown(f"""
                    <div class="response-text">
                        {prep_content}
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please check your internet connection and try again.")
        else:
            st.warning("Please enter a company website URL")

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
elif section == "📞 Call Prep Sheet":
    show_call_prep()
