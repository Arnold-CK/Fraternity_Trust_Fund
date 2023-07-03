# -*- coding: utf-8 -*-
"""
Created on Thu May 25 19:59:24 2023

@author: ArnoldKigonya
"""

import calendar
import uuid
from datetime import date

import gspread
import streamlit as st


def get_years_since_2022():
    current_year = date.today().year
    return list(range(2022, current_year + 1))


@st.cache_data
def get_all_months():
    return list(calendar.month_name)[1:]


@st.cache_data
def get_all_names():
    names = [
        "Alvin Mulumba",
        "Edwin Mpoza",
        "Dennis Ssekimpi",
        "Arnold Kigonya",
        "Adrean Mugalaasi",
        "Phillip Musumba",
    ]

    names.sort()
    return names


def create_guid():
    guid = uuid.uuid4()
    return guid


def get_key_by_value(dictionary, value):
    for key, val in dictionary.items():
        if val == value:
            return key
    return None


@st.cache_data
def get_month_number(month):
    month_order = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    return month_order[month]


def open_connection():
    sheet_credentials = st.secrets["credentials"]
    gc = gspread.service_account_from_dict(sheet_credentials)
    fraternity_sheet = gc.open_by_key(st.secrets["sheet_key"])
    return fraternity_sheet


def sign_in(username, password):
    user_passwords = {
        "Alvin Mulumba": 456,
        "Edwin Mpoza": 123,
        "Dennis Ssekimpi": 123,
        "Arnold Kigonya": 123,
        "Adrean Mugalaasi": 123,
        "Phillip Musumba": 123,
    }

    actual_password = user_passwords[username]
    if actual_password == password:
        return True
    else:
        return False


def switch_page(page_name: str):
    from streamlit.runtime.scriptrunner import RerunData, RerunException
    from streamlit.source_util import get_pages

    def standardize_name(name: str) -> str:
        return name.lower().replace("_", " ")

    page_name = standardize_name(page_name)

    pages = get_pages("home.py")  # OR whatever your main page is called

    for page_hash, config in pages.items():
        if standardize_name(config["page_name"]) == page_name:
            raise RerunException(
                RerunData(
                    page_script_hash=page_hash,
                    page_name=page_name,
                )
            )

    page_names = [standardize_name(config["page_name"]) for config in pages.values()]

    raise ValueError(f"Could not find page {page_name}. Must be one of {page_names}")


def is_alvin(password):
    if password == 456:
        return True
    else:
        return False
