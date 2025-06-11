import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import InvalidArgumentException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pandas as pd
from streamlit_sortables import sort_items


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
    .sortable-item {
        background-color: #f0f0f0 !important;  /* light background */
        color: black !important;              /* readable text */
        border: 1px solid #ccc !important;
        padding: 10px !important;
        border-radius: 6px !important;
        margin-bottom: 6px !important;
        font-weight: 500;
    }

    /* Optional: hover effect for better UX */
    .sortable-item:hover {
        background-color: #e0e0e0 !important;
        cursor: grab;
    }
    </style>
""", unsafe_allow_html=True)

# --- URL and Constants ---

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
    driver.get(draft_link)
    return driver

# === TABS ===
tab1, tab2, tab3, tab4 = st.tabs(["Real Draftboard", "Mock Draftboard", "PlayerRankings", "ModelChanging"])

with tab1:
    st.subheader("🏀 Live Draft Board (Sleeper)")

    # Create two columns: a thin "sidebar" and a wide main section
    col_sidebar, col_main = st.columns([1, 4])

    with col_sidebar:
        st.markdown("### 🛠️ Controls")



        draft_link = st.text_input("Enter Draft link:")
        #TURN THIS INTO JUST PUTTING IN ID INSTEAD OF FULL LINK! 
        league_link = st.text_input("Enter League Link")

        draft_participants = st.number_input("Number of Draft Participants", min_value=1, max_value=32, value=8, step=1)
        rounds = st.number_input("Number of Rounds", min_value=1, max_value=18, value=15, step=1)
        draft_picking_position = st.number_input("Draft Picking Position", min_value=1, max_value= draft_participants, value=1, step=1)

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

        st.session_state.auto_scrape = st.checkbox("Auto-scrape every 10s", value=st.session_state.auto_scrape)

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

    with col_main:

        position_dict = {
            "PG": ["Stephen Curry", "Jrue Holiday"],
            "SG": ["Devin Booker"],
            "SF": ["LeBron James", "Jayson Tatum", "Jimmy Butler"],
            "PF": ["Anthony Davis"],
            "C": ["Nikola Jokic", "Joel Embiid"]
        }

        # Find the max number of players in any position
        max_len = max(len(players) for players in position_dict.values())

        # Fill in columns with NaNs or empty strings to make even rows
        for pos in position_dict:
            players = position_dict[pos]
            position_dict[pos] = players + [""] * (max_len - len(players))

        # Convert to a DataFrame where each column is a position
        grid_df = pd.DataFrame(position_dict)

        st.dataframe(grid_df)

        

        st.markdown("---")


        col_all_players, col_position_players = st.columns([3,2])
        with col_all_players:
            st.subheader("Full Player List")
            data = pd.DataFrame({
            "Player": ["LeBron James", "Stephen Curry", "Nikola Jokic", "Jimmy Butler"],
            "Team": ["LAL", "GSW", "DEN", "MIA"],
            "Points": [27, 29, 26, 21]
            })

            
            highlighted_names = ["Stephen Curry", "Jimmy Butler"]

            def highlight_players(val):
                if val in highlighted_names:
                    return 'background-color: lightgreen; font-weight: bold'
                return ''

            styled_df = data.style.applymap(highlight_players, subset=["Player"])

            st.dataframe(styled_df, use_container_width=True)


        with col_position_players: 
            st.subheader("Position Specific Player List")
            options = st.multiselect(
                "Select Positions",
                ["PG", "SG", "SF", "PF",'C'],
                default=["C"],
            )
            data1 = pd.DataFrame({
            "Player": ["LeBron Poop", "Stephen Curry", "Nikola Poopik", "Jimmy Butler"],
            "Team": ["LAL", "GSW", "DEN", "MIA"],
            "Points": [27, 29, 26, 21]
            })

            
            highlighted_names = ["Stephen Curry", "Jimmy Butler"]

            def highlight_players(val):
                if val in highlighted_names:
                    return 'background-color: lightgreen; font-weight: bold'
                return ''

            styled_df = data.style.applymap(highlight_players, subset=["Player"])

            st.dataframe(styled_df, use_container_width=True)




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
    st.subheader("Mock Draftboard (Coming Soon)")

with tab3:
    st.subheader("Player Rankings (Coming Soon)")
    st.title("🧩 Drag and Drop List Example")

    raw_items = ["LeBron James", "Stephen Curry", "Nikola Jokic", "Kevin Durant"]

    # Wrap items in styled HTML
    styled_items = [
        f"<div style='background-color:#f0f0f0; color:black; padding:10px; border-radius:6px; margin-bottom:6px; font-weight:500;'>{player}</div>"
        for player in raw_items
    ]

    sorted_items = sort_items(styled_items, direction="vertical", key="sortable-players", use_text=False)

    # Extract plain text again if needed
    sorted_plain = [item.split('>')[-1].split('<')[0] for item in sorted_items]

    st.write("Sorted order:")
    st.write(sorted_plain)

with tab4:
    st.subheader("Model Changing (Coming Soon)")