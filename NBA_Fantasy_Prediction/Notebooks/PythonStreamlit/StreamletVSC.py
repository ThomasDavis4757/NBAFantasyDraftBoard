import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import InvalidArgumentException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from streamlit_autorefresh import st_autorefresh
from datetime import datetime


# Setup layout
st.set_page_config(layout="wide")

# --- Make tabs bigger ---
st.markdown("""
    <style>
    div[role="tablist"] > button {
        font-size: 22px !important;
        padding: 12px 24px !important;
        margin-right: 8px !important;
        transition: all 0.3s ease;
    }
    div[role="tablist"] > button:hover {
        background-color: #d3d3c3 !important;
        cursor: pointer;
    }
    div[role="tablist"] > button[aria-selected="true"] {
        background-color: #F5F5DC !important;
        color: #1E2A38 !important;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        border-bottom: 2px solid transparent !important;
        margin-bottom: -2px;
    }
    section[tabindex="0"] {
        background-color: #1E2A38;
        border-top: 2px solid #F5F5DC;
        padding: 1rem;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- URL and Constants ---
url = 'https://sleeper.com/draft/nba/1224830302833098752?ftue=commish'
REFRESH_INTERVAL_SEC = 10

# --- Session state tracking ---
if 'driver_active' not in st.session_state:
    st.session_state.driver_active = False
if 'driver' not in st.session_state:
    st.session_state.driver = None
if 'auto_scrape' not in st.session_state:
    st.session_state.auto_scrape = False
if 'last_scraped_data' not in st.session_state:
    st.session_state.last_scraped_data = []
if 'last_scrape_time' not in st.session_state:
    st.session_state.last_scrape_time = None

# --- Launch browser function ---
def launch_driver():
    options = webdriver.EdgeOptions()
    # Disable headless if you want to see the window
    # options.add_argument('--headless=new')
    edge_service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=edge_service)
    driver.get(url)
    return driver

# === TABS ===
tab1, tab2, tab3 = st.tabs(["Real Draftboard", "Mock Draftboard", "PlayerRankings"])

with tab1:
    st.subheader("🏀 Live Draft Board (Sleeper)")

    # === Controls ===
    col1, col2 = st.columns([1, 2])
    with col1:
        start_browser = st.toggle("Launch Browser", value=st.session_state.driver_active)
        if start_browser and not st.session_state.driver_active:
            st.session_state.driver = launch_driver()
            st.session_state.driver_active = True
            st.success("Browser launched!")
        elif not start_browser and st.session_state.driver_active:
            if st.session_state.driver:
                st.session_state.driver.quit()
                st.session_state.driver = None
            st.session_state.driver_active = False
            st.warning("Browser closed.")

        # Manual scrape
        if st.button("Scrape Now"):
            if st.session_state.driver_active and st.session_state.driver:
                try:
                    st.session_state.driver.refresh()
                    players = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.player-name')
                    names = [player.text for player in players]
                    st.session_state.last_scraped_data = names
                    st.session_state.last_scrape_time = datetime.now().strftime('%H:%M:%S')
                    st.success("Scraped successfully.")
                except Exception as e:
                    st.error(f"Scrape failed: {e}")
            else:
                st.warning("Browser not running.")

        # Auto scrape toggle
        st.session_state.auto_scrape = st.checkbox("Auto-scrape every 10s", value=st.session_state.auto_scrape)

    with col2:
        if st.session_state.auto_scrape:
            st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="auto-refresh")
            if st.session_state.driver_active and st.session_state.driver:
                try:
                    players = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.player-name')
                    names = [player.text for player in players]
                    st.session_state.last_scraped_data = names
                    st.session_state.last_scrape_time = datetime.now().strftime('%H:%M:%S')
                except Exception as e:
                    st.error(f"Auto-scrape failed: {e}")

    # === Display Results ===
    st.markdown("---")
    st.subheader("📋 Drafted Players")
    if st.session_state.last_scraped_data:
        st.caption(f"Last updated: {st.session_state.last_scrape_time}")
        st.dataframe(
            {"Pick #": list(range(1, len(st.session_state.last_scraped_data)+1)),
             "Player": st.session_state.last_scraped_data},
            use_container_width=True
        )
    else:
        st.info("No data scraped yet.")

# Placeholder tabs
with tab2:
    st.subheader("🐶 Mock Draftboard (Coming Soon)")

with tab3:
    st.subheader("🦉 Player Rankings (Coming Soon)")