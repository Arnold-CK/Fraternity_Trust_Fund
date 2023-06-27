import streamlit as st

analysis_sidebar_selection = st.sidebar.selectbox(
    "Which analysis would you like to see?", ("General", "Individual")
)

if analysis_sidebar_selection == "General":
    st.title("General Analysis")

    ttl_payments, ttl_deposits, ttl_uap, ttl_interest = st.columns(4)

    with ttl_payments:
        st.metric("Payments", 1000000)
    with ttl_deposits:
        st.metric("Deposits", 1000000)
    with ttl_uap:
        st.metric("UAP", 1000000)
    with ttl_interest:
        st.metric("Interest", 1000000)
