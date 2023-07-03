from datetime import date

import altair as alt
import gspread
import pandas as pd
import streamlit as st
from gspread_dataframe import get_as_dataframe
from millify import millify

from Functions import functions as fx

st.set_page_config(page_title="Fraternity Trust Fund", page_icon="💰")

with st.spinner("🔃 Loading dashboard..."):
    sheet_credentials = st.secrets["sheet_credentials"]
    gc = gspread.service_account_from_dict(sheet_credentials)
    fraternity_sheet = gc.open_by_key(st.secrets["sheet_key"])

    payments_worksheet = fraternity_sheet.worksheet("Payments")
    payments_df = get_as_dataframe(payments_worksheet, parse_dates=True)

    uap_worksheet = fraternity_sheet.worksheet("UAP Portfolio")
    uap_df = get_as_dataframe(uap_worksheet, parse_dates=True)

    member_payments = payments_df["Amount Deposited"].sum()

    # sorted_uap_df = uap_df.sort_values(by=["Year, Month"], ascending=False)
    # amount_on_uap = sorted_uap_df["Closing Balance"].iloc[0]
    average_interest = uap_df["Interest rate"].mean()

    analysis_sidebar_selection = st.sidebar.selectbox(
        "Which analysis would you like to see?", ("General", "Individual")
    )

    if analysis_sidebar_selection == "General":
        st.title("Fraternity General Portfolio")

        ttl_payments, ttl_uap, ttl_interest = st.columns(3)

        with ttl_payments:
            st.metric(
                "Amount paid by Members",
                millify(member_payments, precision=2),
                help="Total Member Payments (Including Non-UAP Deposits)",
            )
        with ttl_uap:
            st.metric(
                "Amount on UAP",
                100,
                # millify(amount_on_uap, precision=2),
                help="Total Amount on UAP",
            )
        with ttl_interest:
            st.metric("Average Interest Earned", "{:.2%}".format(average_interest))

        current_year = date.today().year
        filtered_df = uap_df[uap_df["Year"] == current_year]

        df = pd.DataFrame(
            {
                "Month": pd.to_datetime(filtered_df["Data Date"]),
                "Interest Rate (%)": filtered_df["Interest rate"] * 100,
            }
        )
        line = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("Month:T", timeUnit="month"),
                y=alt.Y("Interest Rate (%):Q"),
            )
        )

        points = line.mark_point()

        st.altair_chart(line + points, use_container_width=True)

        c_df = pd.DataFrame(
            {
                "Month": pd.to_datetime(filtered_df["Data Date"]),
                "Account Balance": filtered_df["Closing Balance"],
            }
        )
        c_line = (
            alt.Chart(c_df)
            .mark_area()
            .encode(
                x=alt.X("Month:T", timeUnit="month"),
                y=alt.Y("Account Balance:Q"),
            )
            .properties(
                title=alt.TitleParams(
                    text="Closing Balance", anchor="middle", fontSize=35
                )
            )
        )

        c_points = c_line.mark_point()

        st.altair_chart(c_line + c_points, use_container_width=True)

    if analysis_sidebar_selection == "Individual":
        user_names = fx.get_all_names()

        user_is_logged_in = st.session_state.get("user_is_logged_in", False)

        if not user_is_logged_in:
            with st.form(key="individual_login"):
                user = st.selectbox("Who are you?", options=user_names, key="user")
                entered_password = st.text_input("Enter your password", type="password")

                login = st.form_submit_button("Enter")

                if login:
                    user_authenticated = fx.sign_in(
                        username=user, password=entered_password
                    )
                    if user_authenticated:
                        user_is_logged_in = True
                        user_filtered_payments_df = payments_df[
                            payments_df["Name"] == st.session_state.get("user")
                        ]

                        user_payments, user_interest, user_ttl = st.columns(3)

                        user_ttl_paid = user_filtered_payments_df[
                            "Amount Deposited"
                        ].sum()
                        ttl_earned = user_ttl_paid + (average_interest * user_ttl_paid)

                        with user_payments:
                            st.metric(
                                "Total Amount Paid",
                                millify(user_ttl_paid, precision=2),
                                help="Amount that you have so far put in Fraternity",
                            )
                        with user_interest:
                            st.metric(
                                "Average Interest Earned",
                                "{:.2%}".format(average_interest),
                            )
                        with user_ttl:
                            st.metric(
                                "Total Amount in Fraternity",
                                millify(ttl_earned, precision=2),
                            )

                        transactions_df = user_filtered_payments_df.loc[
                            :, ["Name", "Month", "Year", "Amount Deposited"]
                        ].dropna()

                        st.dataframe(transactions_df, use_container_width=True)

                    else:
                        st.error(f"❌ Please enter a valid password for {user}")
