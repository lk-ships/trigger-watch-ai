
# === CRM PIPELINE ===
def show_crm_pipeline():
    st.title("📂 CRM – Pipeline Manager")

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = []

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
            close_date = st.date_input("Expected Close Date")

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
            st.success(f"Opportunity for {account} added!")

    if st.session_state.pipeline:
        st.subheader("📋 Current Pipeline")
        df = pd.DataFrame(st.session_state.pipeline)
        df["Weighted ACV"] = df["acv"] * (df["confidence"] / 100)
        st.dataframe(df[["account", "acv", "stage", "confidence", "close_date", "notes", "Weighted ACV"]], use_container_width=True)

        st.subheader("📊 Summary Metrics")
        total_acv = df["acv"].sum()
        weighted_acv = df["Weighted ACV"].sum()
        stage_counts = df["stage"].value_counts()

        st.markdown(f"**Total Pipeline ACV:** ${total_acv:,.0f}")
        st.markdown(f"**Weighted Pipeline:** ${weighted_acv:,.0f}")
        st.markdown("**Deals by Stage:**")
        for stage, count in stage_counts.items():
            st.markdown(f"- {stage}: {count} deal(s)")
    else:
        st.info("No opportunities in pipeline yet.")
