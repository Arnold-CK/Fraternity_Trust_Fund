# -*- coding: utf-8 -*-
"""
Created on Thu May 25 19:59:24 2023

@author: ArnoldKigonya
"""

import streamlit as st
from datetime import date
import calendar
import uuid

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
        "Phillip Musumba"
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

