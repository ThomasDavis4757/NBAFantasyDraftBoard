import requests
import pandas as pd
import io
import numpy as np 
import time
from fuzzywuzzy import fuzz, process
import streamlit as st

st.set_page_config(layout="wide")

# --- Make tabs bigger ---
st.markdown("""
    <style>
    /* Make the tabs bigger */
    div[role="tablist"] > button {
        font-size: 22px !important;
        padding: 12px 24px !important;
        margin-right: 8px !important;
        transition: all 0.3s ease;
    }

    /* Hover effect on tabs */
    div[role="tablist"] > button:hover {
        background-color: #d3d3c3 !important; /* soft hover */
        cursor: pointer;
    }

    /* Selected (active) tab */
    div[role="tablist"] > button[aria-selected="true"] {
        background-color: #F5F5DC !important; /* creamy active background */
        color: #1E2A38 !important; /* dark text */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -2px;
    }

    /* Fix the main section under tabs */
    section[tabindex="0"] {
        background-color: #1E2A38; /* match your dark background */
        border-top: 2px solid #F5F5DC;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Real Draftboard", "Mock Draftboard", "PlayerRankings"])

with tab1:
    st.header("A cat")
with tab2:
    st.header("A dog")
with tab3:
    st.header("An owl")