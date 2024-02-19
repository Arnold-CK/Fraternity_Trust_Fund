import random
import re
from datetime import datetime

import altair as alt
import gspread
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from gspread_dataframe import get_as_dataframe
from millify import millify
from pytz import timezone
from streamlit_option_menu import option_menu as option_menu
from yaml.loader import SafeLoader

import functions as fx


def load_data():
    fraternity_workbook = load_workbook()
    payments_worksheet = open_sheet("Payments")
    uap_worksheet = open_sheet("UAP Portfolio")

    payments_df = get_as_dataframe(payments_worksheet, parse_dates=True)
    uap_df = get_as_dataframe(uap_worksheet, parse_dates=True)

    return payments_df, uap_df, fraternity_workbook


@st.cache_resource
def load_workbook():
    sheet_credentials = st.secrets["sheet_credentials"]
    google_spreadsheet_client = gspread.service_account_from_dict(sheet_credentials)
    workbook = google_spreadsheet_client.open_by_key(st.secrets["sheet_key"])
    return workbook


def open_sheet(sheet_name):
    try:
        fraternity_workbook = load_workbook()
        worksheet = fraternity_workbook.worksheet(sheet_name)
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        # Handle the case where the worksheet with the given name is not found.
        return None


def general_dashboard(payments_df, uap_df):
    search_year, search_month = st.columns(2)
    with search_year:
        selected_year = st.selectbox("Year", fx.get_years_since_2022())
    with search_month:
        selected_month = st.selectbox(
            "Month",
            fx.get_all_months(),
        )

    year_filtered_payments_df = payments_df[payments_df["Year"] == selected_year]
    year_filtered_uap_df = uap_df[payments_df["Year"] == selected_year]

    month_filtered_payments_df = year_filtered_payments_df[
        year_filtered_payments_df["Month"] == selected_month
    ]
    month_filtered_uap_df = year_filtered_uap_df[
        year_filtered_uap_df["Month"] == selected_month
    ]

    total_payment = payments_df["Amount Deposited"].sum()
    average_interest = uap_df["Interest rate"].mean()
    closing_balance_df = pd.DataFrame(
        {
            "Date": pd.to_datetime(uap_df["Data Date"]),
            "Amount": uap_df["Closing Balance"],
        }
    )
    max_date = closing_balance_df["Date"].max()
    amount_on_max_date = closing_balance_df.loc[
        closing_balance_df["Date"] == max_date, "Amount"
    ]

    st.write("---")

    ttl_payments, ttl_uap, ttl_interest = st.columns(3)

    with ttl_payments:
        st.metric(
            "Amount paid by Members",
            millify(total_payment, precision=2),
            help="Total Member Payments (Including Non-UAP Deposits)",
        )
    with ttl_uap:
        st.metric(
            "Amount on UAP",
            millify(amount_on_max_date, precision=2),
            help="Total Amount on UAP",
        )
    with ttl_interest:
        st.metric("Average Interest Earned", "{:.2%}".format(average_interest))

    st.write("---")

    filtered_df = uap_df[uap_df["Year"] == selected_year]

    interest_df = pd.DataFrame(
        {
            "Month": pd.to_datetime(filtered_df["Data Date"]),
            "Interest Rate (%)": filtered_df["Interest rate"] * 100,
        }
    )
    line = (
        alt.Chart(interest_df)
        .mark_line()
        .encode(
            x=alt.X("Month:T", timeUnit="month"),
            y=alt.Y("Interest Rate (%):Q"),
        )
        .properties(
            title=alt.TitleParams(
                text="Interest rate by Month", anchor="middle", fontSize=35
            )
        )
    )

    points = line.mark_point()

    st.altair_chart(line + points, use_container_width=True)

    closing_balance_graph_df = pd.DataFrame(
        {
            "Month": pd.to_datetime(filtered_df["Data Date"]),
            "Account Balance": filtered_df["Closing Balance"],
        }
    )
    closing_balance_graph = (
        alt.Chart(closing_balance_graph_df)
        .mark_area()
        .encode(
            x=alt.X("Month:T", timeUnit="month"),
            y=alt.Y("Account Balance:Q"),
        )
        .properties(
            title=alt.TitleParams(
                text="UAP Acct Closing Balance by Month",
                anchor="middle",
                fontSize=35,
            )
        )
    )

    c_points = closing_balance_graph.mark_point()

    st.altair_chart(closing_balance_graph + c_points, use_container_width=True)


def personal_dashboard(current_user, payments_df, uap_df):
    user_filtered_payments_df = payments_df[payments_df["Name"] == current_user]
    user_filtered_payments_df = user_filtered_payments_df.sort_values(
        by="Payment Month", ascending=False
    )
    average_interest = uap_df["Interest rate"].mean()
    user_payments, user_interest, user_ttl = st.columns(3)

    user_ttl_paid = user_filtered_payments_df["Amount Deposited"].sum()
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

    transactions_df["Year"] = pd.to_datetime(
        transactions_df["Year"].astype(int), format="%Y"
    )
    transactions_df["Year"] = transactions_df["Year"].dt.strftime("%Y")

    st.dataframe(
        transactions_df,
        use_container_width=True,
        hide_index=True,
    )


# Streamlit setup
st.set_page_config(page_title="Fraternity Trust Fund", page_icon="💰", layout="wide")

with open("./config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["preauthorized"],
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    current_user = st.session_state["name"]

    payments_df, uap_df, fraternity_workbook = load_data()

    years = fx.get_years_since_2022()
    months = fx.get_all_months()

    options = (
        ["Data Entry"]
        if current_user == "Data Entrant"
        else (["Dashboard", "Data Entry"] if current_user == "Alvin Mulumba" else ["Dashboard"])
    )

    option_icons = (
        ["bar-chart-line", "clipboard-data"]
        if current_user == "Alvin Mulumba"
        else ["bar-chart-line"]
    )

    with st.sidebar:
        nav_bar = option_menu(
            current_user, options, icons=option_icons, menu_icon="person-circle"
        )

    if nav_bar == "Dashboard":
        general, personal = st.tabs(["🎡 General", "🕴🏾 Personal"])

        with general:
            general_dashboard(payments_df, uap_df)

        with personal:
            personal_dashboard(current_user, payments_df, uap_df)

    if nav_bar == "Data Entry":
        costs, payments, uap = st.tabs(["📕 Costs", "📗 Payments", "💹 UAP"])

        with costs:
            st.title(":red[Costs]")
            with st.form(key="costs", clear_on_submit=True):
                st.markdown(
                    "**Hi Alvin, please choose the month and year for which you are entering data**"
                )

                month, year = st.columns(2)

                with month:
                    selected_month = st.selectbox("Month", months)

                with year:
                    selected_year = st.selectbox("Year", years)

                st.write("---")

                st.markdown("**Monthly Fund Costs**")

                item, amount, narrative = st.columns(3)

                item.markdown("_Cost Item_")
                amount.markdown("_Amount_")
                narrative.markdown("_Narrative_")

                identifier = dict()

                counter = 1

                for i in range(0, 3):
                    item_key = f"cost_key{counter}"
                    amount_key = f"cost_key{counter + 1}"
                    narrative_key = f"cost_key{counter + 2}"

                    identifier[i] = [item_key, amount_key, narrative_key]

                    with item:
                        st.text_input(
                            label=" ",
                            label_visibility="collapsed",
                            disabled=False,
                            key=item_key,
                        )
                    with amount:
                        st.text_input(
                            placeholder="ugx",
                            label=" ",
                            label_visibility="collapsed",
                            disabled=False,
                            key=amount_key,
                        )
                    with narrative:
                        st.text_input(
                            label=" ",
                            label_visibility="collapsed",
                            disabled=False,
                            key=narrative_key,
                        )

                    counter += 3

                submitted = st.form_submit_button("Save")

                if submitted:
                    costs_for_insertion = []
                    timezone = timezone("Africa/Nairobi")

                    with st.spinner("Validating form..."):
                        cost_form_entry_isValid = True

                        for identifier, input_list in identifier.items():
                            cost_item = st.session_state.get(input_list[0], "")
                            cost_amount = st.session_state.get(input_list[1], "")
                            cost_narrative = st.session_state.get(input_list[2], "")

                            if (
                                not cost_item.strip()
                                and not cost_amount.strip()
                                and not cost_narrative.strip()
                            ):
                                continue

                            if cost_item.strip():
                                if cost_amount.strip():
                                    cost_amount_value = int(cost_amount.strip())
                                    if cost_amount_value <= 0:
                                        cost_form_entry_isValid = False
                                        st.error(
                                            "🚨 Please enter a cost amount greater than zero"
                                        )
                                else:
                                    cost_form_entry_isValid = False
                                    st.error("⚠️ Cost amount cannot be blank")

                            if cost_amount.strip() and not cost_item.strip():
                                cost_form_entry_isValid = False
                                st.error("⚠️ Cost item cannot be blank")

                            if cost_form_entry_isValid:
                                timestamp = datetime.now(timezone).strftime(
                                    "%d-%b-%Y %H:%M:%S" + " EAT"
                                )

                                date_string = f"1 {selected_month} {selected_year}"
                                data_date = datetime.strptime(
                                    date_string, "%d %B %Y"
                                ).date()

                                data = [
                                    timestamp,
                                    selected_month,
                                    cost_item.strip(),
                                    cost_amount_value,
                                    cost_narrative.strip(),
                                    selected_year,
                                    str(data_date),
                                ]

                                costs_for_insertion.append(data)

                    if costs_for_insertion:
                        with st.spinner("Saving Cost data..."):
                            worksheet = open_sheet("Costs")

                            all_values = worksheet.get_all_values()

                            next_row_index = len(all_values) + 1

                            worksheet.append_rows(
                                costs_for_insertion,
                                value_input_option="user_entered",
                                insert_data_option="insert_rows",
                                table_range=f"a{next_row_index}",
                            )

                            st.success(
                                "✅ Cost data Saved Successfully. Feel free to close the application"
                            )
        with payments:
            names = fx.get_all_names()

            st.title(":blue[Payments]")

            with st.form(key="payments", clear_on_submit=True):
                st.markdown(
                    "**Hi Alvin, please choose the month and year for which you are entering data**"
                )

                month, year = st.columns(2)

                with month:
                    selected_month = st.selectbox("Month", months)

                with year:
                    selected_year = st.selectbox("Year", years)

                st.write("---")

                st.markdown("**Member Payments**")

                name_column, amount = st.columns(2)

                name_column.markdown("_Name_")
                amount.markdown("_Amount_")

                name_input = dict()

                emoji_options = ["😃", "😄", "🐪", "😊", "🙂", "😎", "💰", "😁"]

                counter = 1

                for name in names:
                    amount_key = f"payments_key{counter}"

                    name_input[name] = amount_key

                    emoji = random.choice(emoji_options)

                    with name_column:
                        st.write(emoji, " ", name)
                        st.write("")
                    with amount:
                        st.text_input(
                            placeholder="ugx",
                            label=" ",
                            label_visibility="collapsed",
                            disabled=False,
                            key=amount_key,
                        )

                    counter += 1

                submitted = st.form_submit_button("Save")

                if submitted:
                    with st.spinner("Validating Payments Form..."):
                        payments_form_isvalid = True
                        validation_list = list()

                        payments_for_insertion = []
                        timezone = timezone("Africa/Nairobi")

                        for name, amount_key in name_input.items():
                            amount_entered = st.session_state.get(amount_key, "")

                            if amount_entered.strip():
                                amount_paid = int(amount_entered.strip())
                            else:
                                continue

                            timestamp = datetime.now(timezone).strftime(
                                "%d-%b-%Y %H:%M:%S" + " EAT"
                            )

                            date_string = f"1 {selected_month} {selected_year}"
                            data_date = datetime.strptime(
                                date_string, "%d %B %Y"
                            ).date()

                            data = [
                                timestamp,
                                selected_month,
                                name,
                                amount_paid,
                                selected_year,
                                str(data_date),
                            ]

                            payments_for_insertion.append(data)
                            validation_list.append(amount_paid)

                    payments_form_isvalid = all(item > 0 for item in validation_list)
                    if not payments_form_isvalid:
                        st.error("🚨 All payments entered must be greater than zero")

                    if payments_form_isvalid:
                        with st.spinner("Saving payments data..."):
                            worksheet = open_sheet("Payments")

                            all_values = worksheet.get_all_values()

                            next_row_index = len(all_values) + 1

                            worksheet.append_rows(
                                payments_for_insertion,
                                value_input_option="user_entered",
                                insert_data_option="insert_rows",
                                table_range=f"a{next_row_index}",
                            )

                            st.success(
                                "✅ Payments Saved Successfully. Feel free to close the application"
                            )
        with uap:
            st.title(":green[UAP]")

            with st.form(key="UAP", clear_on_submit=True):
                st.markdown(
                    "**Hi Alvin, please choose the month and year for which you are entering data**"
                )

                month, year = st.columns(2)

                with month:
                    selected_month = st.selectbox("Month", months)

                with year:
                    selected_year = st.selectbox("Year", years)

                st.write("---")

                st.markdown("**UAP Portfolio Monthly Details**")

                st.caption("_As shown in the Investment Statement_")

                counter = 0

                opening_key = f"uap_key{counter}"
                closing_key = f"uap_key{counter + 1}"
                interest_key = f"uap_key{counter + 2}"

                holder_column, dummy_column = st.columns(2)

                with holder_column:
                    st.text_input(
                        label="Opening Balance",
                        placeholder="ugx",
                        disabled=False,
                        help="Please enter a value greater than zero",
                        key=opening_key,
                    )

                    st.text_input(
                        placeholder="ugx",
                        label="Closing Balance",
                        disabled=False,
                        help="Please enter a value greater than zero",
                        key=closing_key,
                    )

                    st.text_input(
                        label="Interest Rate",
                        placeholder="%",
                        help="Please enter a value greater than zero",
                        disabled=False,
                        key=interest_key,
                    )

                submitted = st.form_submit_button("Save")

                if submitted:
                    is_valid = True

                    with st.spinner("🔍 Validating form..."):
                        uap_opening = st.session_state.get(opening_key, "")
                        uap_closing = st.session_state.get(closing_key, "")
                        uap_interest = st.session_state.get(interest_key, "")

                        uap_interest_value = 0
                        uap_opening_value = 0
                        uap_closing_value = 0

                        if uap_opening.strip():
                            uap_opening_value = float(uap_opening.strip())
                            if uap_opening_value <= 0.0:
                                is_valid = False
                                st.error(
                                    "🚨 Please enter an opening balance greater than zero"
                                )
                        else:
                            is_valid = False
                            st.error("⚠️ Opening Balance cannot be blank")

                        if uap_closing.strip():
                            uap_closing_value = float(uap_closing.strip())
                            if uap_closing_value <= 0.0:
                                is_valid = False
                                st.error(
                                    "🚨 Please enter a closing balance greater than zero"
                                )
                        else:
                            is_valid = False
                            st.error("⚠️ Closing Balance cannot be blank")

                        if uap_interest.strip():
                            if uap_interest.endswith("%"):
                                uap_interest_value = (
                                    float(uap_interest.strip("%")) / 100.0
                                )
                            else:
                                uap_interest_value = float(uap_interest.strip()) / 100.0
                            if uap_interest_value <= 0.0:
                                is_valid = False
                                st.error(
                                    "🚨 Please enter an interest rate greater than zero"
                                )
                        else:
                            is_valid = False
                            st.error("⚠️ Interest rate cannot be blank")

                    if is_valid:
                        st.info("👍 Form is Valid")

                        with st.spinner("Saving UAP data..."):
                            timezone = timezone("Africa/Nairobi")

                            timestamp = datetime.now(timezone).strftime(
                                "%d-%b-%Y %H:%M:%S" + " EAT"
                            )

                            date_string = f"1 {selected_month} {selected_year}"
                            data_date = datetime.strptime(
                                date_string, "%d %B %Y"
                            ).date()

                            data = [
                                timestamp,
                                selected_month,
                                selected_year,
                                uap_closing_value,
                                uap_opening_value,
                                uap_interest_value,
                                str(data_date),
                            ]
                            worksheet = open_sheet("UAP Portfolio")

                            all_values = worksheet.get_all_values()

                            next_row_index = len(all_values) + 1

                            worksheet.append_row(
                                data,
                                value_input_option="user_entered",
                                insert_data_option="insert_rows",
                                table_range=f"a{next_row_index}",
                            )

                            st.success(
                                "✅ UAP data Saved Successfully. Feel free to close the application"
                            )

    authenticator.logout("Logout", "sidebar", key="unique_key")

elif authentication_status is False:
    st.error("Username/Password is incorrect")

elif authentication_status is None:
    st.info("Please enter your **Firstname** and Password")
