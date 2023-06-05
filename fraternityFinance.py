# -*- coding: utf-8 -*-
"""
Created on Thu May 25 07:36:42 2023

@author: ArnoldKigonya
"""

from datetime import datetime
from random import choice
from pytz import timezone
import streamlit as st
import functions as fx
import gspread

st.set_page_config(page_title="Fraternity Trust Fund",page_icon="💰")

years = fx.get_years_since_2022()
months = fx.get_all_months()

sheet_credentials = st.secrets["credentials"]
gc = gspread.service_account_from_dict(sheet_credentials)

sidebar_selection = st.sidebar.selectbox("What would you like to enter?", ('Payments', 'Costs', 'UAP'))

if sidebar_selection == 'Payments':

    names = fx.get_all_names()

    st.title(':blue[Payments]')

    with st.form(key="payments",clear_on_submit=True):

        st.markdown("**Hi Alvin, please choose the month and year for which you are entering data**")

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

        emoji_options = ["😃", "😄", "🐪", "😊", "🙂", "😎","💰","😁"]
        
        counter = 1

        for name in names:

            amount_key = f"key{counter}"

            name_input[name] = amount_key

            emoji = choice(emoji_options)

            with name_column:
                st.write(emoji, " ", name)
                st.write("")
            with amount:
                    st.text_input(
                    placeholder="ugx", 
                    label=" ", 
                    label_visibility="collapsed", 
                    disabled=False, 
                    key=amount_key)
                    
            counter += 1
        
        submitted = st.form_submit_button("Save")
        
        if submitted:
            
            with st.spinner("Saving Payments Data..."):

                payments_for_insertion=[]
                timezone = timezone("Africa/Nairobi")
            
                for name, amount_key in name_input.items():
                    
                    amount_entered = st.session_state.get(amount_key,"")
            
                    if amount_entered.strip() != "" and int(amount_entered) > 0:
                        
                        timestamp = datetime.now(timezone).strftime("%d-%b-%Y %H:%M:%S" + " EAT")
                        data = [timestamp, selected_month, name, amount_entered, selected_year]
            
                        payments_for_insertion.append(data)

                if payments_for_insertion:
                        
                    fraternity_sheet = gc.open_by_key(st.secrets["sheet_key"])
                    worksheet = fraternity_sheet.worksheet("Payments")

                    all_values = worksheet.get_all_values()
                
                    next_row_index = len(all_values) + 1

                    worksheet.append_rows(
                            payments_for_insertion,
                            value_input_option='user_entered',
                            insert_data_option='insert_rows',
                            table_range=f"a{next_row_index}"
                        )
                    
                    st.success("✅ Payments Saved Successfully. Feel free to close the application")

                else:
                    st.info("⚠️ Please enter an amount greater than zero in at least **ONE** of the text boxes")

if sidebar_selection == 'Costs':
     
     st.title(':red[Costs]')

     with st.form(key="costs",clear_on_submit=True):

        st.markdown("**COSTS!!!**")

        submitted = st.form_submit_button("Save")

if sidebar_selection == 'UAP':
     
    st.title(':green[UAP]')

    with st.form(key="UAP",clear_on_submit=True):

        st.markdown("**UAP**")
        submitted = st.form_submit_button("Save")