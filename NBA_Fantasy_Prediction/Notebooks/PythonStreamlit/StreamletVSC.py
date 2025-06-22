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
import streamlit_sortables
import requests
import os
from datetime import timedelta
from rapidfuzz import process, fuzz
import ast
import json
import numpy as np
import time

#print(streamlit_sortables.__version__)

test_front_page = False

    ####################################### Functions ##################################

def mark_as_good(player_positions, positions_equation, positions):
    if positions_equation == 'OR':
        for i in player_positions:
            if i in positions:
                return True
            else:
                continue
        return False
            
    elif positions_equation == 'AND':
        num_positions = len(positions)
        matching_positions = 0
        for i in player_positions:
            if i in positions:
                matching_positions += 1
        if num_positions == matching_positions:
            return True
        else:
            return False
        
    elif positions_equation == 'NOT':
        for i in player_positions:
            if i in positions:
                return False
            else:
                continue
        return True

########################################################################################################################################################
def get_best_match(name, reference_list, threshold=25):
    match = process.extractOne(name, reference_list, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        return match[0]
    return None 

########################################################################################################################################################
def get_draft_picks_list(draft_participants, rounds, picking_pos, not_owned_dps, newly_owned_dps):
    list_of_positions = []
    for i in range(int(rounds)):
        if (i+1) % 2 != 0:
            list_of_positions.append(str(i+1) + "." + str(picking_pos))
        else:
            list_of_positions.append(str(i+1) + "." + str(draft_participants - (picking_pos - 1)))
    

    list_not_owned = not_owned_dps.split(',')
    list_newly_owned = newly_owned_dps.split(',')
    cleaned_not_owned = []
    cleaned_newly_owned = []
    for i, j in zip(list_not_owned, list_newly_owned):
        cleaned_not_owned.append(i.strip())
        cleaned_newly_owned.append(j.strip())
        
    filtered = [item for item in list_of_positions if item not in cleaned_not_owned]
    final_list = filtered + [item for item in cleaned_newly_owned if item not in filtered] 
    final_list = [item for item in final_list if item.strip()]
    final_list_sorted = sorted(final_list, key=lambda x: (int(x.split('.')[0]), int(x.split('.')[1])))
    return final_list_sorted

########################################################################################################################################################

def format_name(full_name):
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0][0].upper()}. {parts[-1]}"
    else:
        return full_name  # fallback if name is malformed

########################################################################################################################################################

def highlight_row(row):
    formatted_name = format_name(row["Player"])
    player_team_key = f"{formatted_name} - {row['team']}"
    
    if player_team_key in team_highlighted_names:
        return ['background-color: lightgreen; font-weight: bold'] * len(row)
    elif player_team_key in not_team_highlighted_names:
        return ['background-color: indianred; font-weight: bold'] * len(row)
    
    return [''] * len(row)

########################################################################################################################################################

def highlight_row_mock(row):
    formatted_name = format_name(row["Player"])
    player_team_key = f"{formatted_name} - {row['team']}"

    # Green: players on your team
    team_df = st.session_state.team_players_with_positions_mock
    team_keys = set(f"{format_name(r['Player'])} - {r['team']}" for _, r in team_df.iterrows())

    # Red: players already picked by others
    picked_df = st.session_state.picked_players_mock
    picked_keys = set(f"{format_name(r['Player'])} - {r['team']}" for _, r in picked_df.iterrows())

    if player_team_key in team_keys:
        return ['background-color: lightgreen; font-weight: bold'] * len(row)
    elif player_team_key in picked_keys:
        return ['background-color: indianred; font-weight: bold'] * len(row)

    return [''] * len(row)

########################################################################################################################################################

def safe_format_name(x):
    try:
        return format_name(x)
    except Exception:
        return None
    
########################################################################################################################################################

def players_for_position(position, team_player_pos_df):

    def is_position(player_positions, position):
        for i in player_positions:
            if i == position:
                return True
        return False
    
    df = team_player_pos_df.copy()
    df['MeetPositionalRequirement'] = df['fantasy_positions'].apply(ast.literal_eval).apply(lambda player_positions: is_position(player_positions, position)) 
    df = df[df['MeetPositionalRequirement'] == True]
    name_list = df['Player'].tolist()

    return name_list

########################################################################################################################################################

def is_in_team_highlighted(row):
    formatted_name = format_name(row["Player"])
    player_team_key = f"{formatted_name} - {row['team']}"
    return player_team_key in team_highlighted_names


def list_of_all_draft_picks(rounds,num_participants):
    total_picks = rounds * num_participants
    list_of_dps = []
    for i in range(rounds):
        for j in range(num_participants):
            list_of_dps.append(str(i+1) + '.' + str(j+1))
    return list_of_dps


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
    
    /* Optional: hover effect for better UX */
    .sortable-item:hover {
        background-color: #e0e0e0 !important;
        cursor: grab;
    }
    li.sortable-item {
    background-color: #F5F5DC !important;
    color: black !important;
    font-weight: bold !important;
    font-size: 20px !important;
    padding: 12px !important;
    border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    /* Existing styles... */

    /* Multiselect override */
    .stMultiSelect > div {
        background-color: white !important;
        color: black !important;
    }

    .stMultiSelect div[data-baseweb="select"] span {
        color: black !important;
    }

    div[data-baseweb="popover"] {
        background-color: white !important;
        color: black !important;
    }

    div[data-baseweb="option"] {
        background-color: white !important;
        color: black !important;
    }

    div[data-baseweb="option"]:hover {
        background-color: #f0f0f0 !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <style>
    .card {
        background-color: #F5F5DC;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
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
if 'last_scraped_positions' not in st.session_state:
    st.session_state.last_scraped_positions = []
if 'last_scraped_draft_locations' not in st.session_state:
    st.session_state.last_scraped_draft_locations = []
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

    #sleeper API data (for fantasy accurate positions and teams)
    uploaded_data = pd.read_csv('../../data/sleeperapidata/updatedsleeperapidata1.csv')
    #current weight that is being used in the application.
    multi_weights = pd.read_csv('../../data/currentweight/currentpointvalues.csv')

    #rankingmodel is the ranking that is set as the main ranking, and this is also automatically converting
    #the names into the same names that are on sleeper. (Sleeper doesn't have suffix while Basketball ref. scraped data does.)
    reference_names = uploaded_data['full_name'].dropna().unique().tolist()
    folder_path = '../../data/current_ranking'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if csv_files:
        csv_path = os.path.join(folder_path, csv_files[0])
        rankingmodel = pd.read_csv(csv_path)
        rankingmodel['Player'] = rankingmodel['Player'].apply(lambda name: get_best_match(name, reference_names))
        current_ranking_name = os.path.splitext(csv_files[0])[0]
        #print(f"Loaded: {csv_files[0]}")
    else:
        print("No CSV files found.")
        
    #Getting data organized and prepared to display.
    
    rankingmodel['GamesPlayedRatio'] = rankingmodel['S_GamesPlayed'].astype(str) + " / " + rankingmodel['TotalGamesSeason'].astype(str)


    merged_data = rankingmodel.merge(
        uploaded_data[['full_name','fantasy_positions','team']],
        how='left',
        left_on='Player',
        right_on='full_name'
    )

    merged_data['PrevFantasyPoints'] = merged_data['S_FantasyPoints'] - (
        (merged_data['S_AvgPoints'] * 0.5) +
        (merged_data['S_AvgAssists'] * 1) +
        (merged_data['S_AvgRebounds'] * 1) +
        (merged_data['S_AvgTurnovers'] * -1) +
        (merged_data['S_AvgSteals'] * 2) +
        (merged_data['S_AvgBlocks'] * 2) +
        (merged_data['S_Avg3P'] * 0.5)
        )

    merged_data['PrevFantasyPoints'] = merged_data['PrevFantasyPoints'] + (
        (merged_data['S_AvgPoints'] * multi_weights['Points'].iloc[0]) +
        (merged_data['S_AvgAssists'] * multi_weights['Assists'].iloc[0]) +
        (merged_data['S_AvgRebounds'] * multi_weights['Rebounds'].iloc[0]) +
        (merged_data['S_AvgTurnovers'] * multi_weights['Turnovers'].iloc[0]) +
        (merged_data['S_AvgSteals'] * multi_weights['Steals'].iloc[0]) +
        (merged_data['S_AvgBlocks'] * multi_weights['Blocks'].iloc[0]) +
        (merged_data['S_Avg3P'] * multi_weights['ThreePointers'].iloc[0])
    )

    merged_data['PrevFantasyPoints'] = (
        (merged_data['PrevFantasyPoints'] * (1 - (multi_weights['GamesMadeWeight'].iloc[0] / 100))) +
        (merged_data['PrevFantasyPoints'] * (multi_weights['GamesMadeWeight'].iloc[0] / 100) * (merged_data['S_GamesPlayed'] / merged_data['TotalGamesSeason']))
    )

    displayed_df = merged_data[['Player','fantasy_positions','team','GamesPlayedRatio','PrevFantasyPoints','Predicted']]



    num_drafting_participants = 0
    num_drafting_rounds = 0

    with col_sidebar:
        st.markdown("### 🛠️ Controls")

        draft_link = st.text_input("Enter Draft link:")
        start_browser = st.toggle("Launch Browser", value=st.session_state.driver_active)

# Invalid link handling (always happens first)
        if start_browser and "sleeper" not in draft_link.lower():
            st.error("Link did not contain 'sleeper'. Try another link.")
            if st.session_state.driver:
                st.session_state.driver.quit()
                st.session_state.driver = None
            st.session_state.driver_active = False
        else:
            # Launching browser
            if start_browser and not st.session_state.driver_active:
                st.session_state.driver = launch_driver()
                st.session_state.driver_active = True
                st.success("Browser launched!")

        # Closing browser
            elif not start_browser and st.session_state.driver_active:
                if st.session_state.driver:
                    st.session_state.driver.quit()
                    st.session_state.driver = None
                st.session_state.last_scraped_data = []
                st.session_state.last_scraped_positions = []
                st.session_state.last_scraped_draft_locations = []
                styled_df = pd.DataFrame()
                styled_df_pos = pd.DataFrame()
                grid_df = pd.DataFrame()
                st.session_state.driver_active = False
                st.warning("Browser closed.")
        

        if start_browser and num_drafting_participants == 0:
            num_drafting_participants = len(st.session_state.driver.find_elements(By.CSS_SELECTOR, '.team-column'))
            if num_drafting_participants == 0:
                st.error("Could not parse sleeper website correctly for number of draft participants. Setting to default 8.")
                num_drafting_participants = 8

        if start_browser and num_drafting_rounds == 0:
            total_cells = len(st.session_state.driver.find_elements(By.CSS_SELECTOR, '.cell-container'))
            if total_cells == 0:
                st.error("Could not parse sleeper website correctly for number of draft rounds. Setting to default 14.")
                num_drafting_rounds = 14
            else:
                num_drafting_rounds = total_cells / num_drafting_participants


        if num_drafting_participants == 0:
            draft_picks = []
            pass
        else:
            draft_picking_position = st.number_input("Draft Picking Position", min_value=1, max_value=int(num_drafting_participants), value=1, step=1)
            lost_picks = st.text_input("Enter picks you do NOT have anymore (traded away):")
            added_picks = st.text_input("Enter picks you have aquired (gotten from trading)")

            with st.popover("Save Draft Settings"):
                draft_setting_name = st.text_input("Enter file name to save as.")

                st.markdown(f"Number of Participants: {num_drafting_participants}")
                st.markdown(f"Your Pick Location: {draft_picking_position}")
                st.markdown(f"Rounds: {num_drafting_rounds}")
                if len(lost_picks) == 0:
                    st.markdown(f"Didn't lose any picks.")
                else:
                    st.markdown(f"Picks you don't have anymore: {lost_picks}")
                if len(added_picks) == 0:
                    st.markdown(f"Didn't gain any extra picks.")
                else:
                    st.markdown(f"New picks that you gained: {added_picks}")
                if st.button("Confirm and save"):
                    settings = {
                        "num_drafting_participants": num_drafting_participants,
                        "draft_picking_position": draft_picking_position,
                        "num_drafting_rounds": num_drafting_rounds,
                        "lost_picks": lost_picks,
                        "added_picks": added_picks
                    }

                    df = pd.DataFrame([settings])  
                    df.to_csv(f"../../data/draft_settings/{draft_setting_name}.csv")
                    st.success("Successfully saved to file!")



            
            draft_picks = get_draft_picks_list(num_drafting_participants, num_drafting_rounds, draft_picking_position, lost_picks, added_picks)
        

            st.text("Must be in 'x.x' format, or 'x.x, x.x', or empty.")   
            
            if test_front_page:
                st.write(draft_picks)



        if st.button("Scrape Now"):
            if st.session_state.driver_active and st.session_state.driver:
                try:
                    st.session_state.driver.refresh()

                    drafted_cells = st.session_state.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'cell') and contains(@class, 'drafted')]"
                    )
                    if test_front_page:
                        st.write(len(drafted_cells))
                    draft_locations = []

                    for cell in drafted_cells:
                        try:
                            draft_locations.append(cell.find_element(By.CSS_SELECTOR, ".pick").text)
                        except Exception as e:
                            st.warning(f"Failed to parse a drafted cell: {e}")


                    st.session_state.last_scraped_draft_locations = draft_locations

                    players = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.player-name')
                    scraped_positions = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.position')

                    names = [player.text for player in players]
                    scraped_positions_list = [scrapos.text for scrapos in scraped_positions]

                    st.session_state.last_scraped_data = names
                    st.session_state.last_scraped_positions = scraped_positions_list

                    st.session_state.last_scrape_time = datetime.now().strftime('%H:%M:%S')
                    st.success("Scraped successfully.")
                except Exception as e:
                    st.error(f"Scrape failed: {e}")
            else:
                st.warning("Browser not running.")

        st.session_state.auto_scrape = st.checkbox("Auto-scrape every 10s", value=st.session_state.auto_scrape)

        # st.write(num_drafting_participants)
        # st.write(num_drafting_rounds)

        if st.session_state.auto_scrape:
            st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="auto-refresh")
            if st.session_state.driver_active and st.session_state.driver:
                try:
                    st.session_state.driver.refresh()

                    drafted_cells = st.session_state.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'cell') and contains(@class, 'drafted')]"
                    )

                    draft_locations = []

                    for cell in drafted_cells:
                        try:
                            draft_locations.append(cell.find_element(By.CSS_SELECTOR, ".pick").text)
                        except Exception as e:
                            st.warning(f"Failed to parse a drafted cell: {e}")

                    st.session_state.last_scraped_draft_locations = draft_locations

                    players = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.player-name')
                    scraped_positions = st.session_state.driver.find_elements(By.CSS_SELECTOR, '.position')

                    names = [player.text for player in players]
                    scraped_positions_list = [scrapos.text for scrapos in scraped_positions]

                    st.session_state.last_scraped_data = names
                    st.session_state.last_scraped_positions = scraped_positions_list

                    st.session_state.last_scrape_time = datetime.now().strftime('%H:%M:%S')
                except Exception as e:
                    st.error(f"Auto-scrape failed: {e}")

        picks_on_team = [item for item in st.session_state.last_scraped_draft_locations if item in draft_picks]
        picks_not_on_team = [item for item in st.session_state.last_scraped_draft_locations if item not in draft_picks]

        if test_front_page:
            st.write(picks_on_team)
            st.write(picks_not_on_team)

    with col_main:

        team_highlighted_names = [
             f"{name} - {position.split(' - ')[1]}"
             for name, position in zip(st.session_state.last_scraped_data, st.session_state.last_scraped_positions)
        ]

        not_team_highlighted_names = [
            f"{name} - {position.split(' - ')[1]}"
            for name, position in zip(st.session_state.last_scraped_data, st.session_state.last_scraped_positions)
        ]

        team_highlighted_names_no_pos = [
            name for name in st.session_state.last_scraped_data
        ]

        not_team_highlighted_names_no_pos = [
            name for name in st.session_state.last_scraped_data
        ]

        team_indicies = [i for i, val in enumerate(st.session_state.last_scraped_draft_locations) if val in draft_picks]
        non_team_indicies = [i for i, val in enumerate(st.session_state.last_scraped_draft_locations) if val not in draft_picks]

        team_highlighted_names = [team_highlighted_names[i] for i in team_indicies]
        not_team_highlighted_names = [not_team_highlighted_names[i] for i in non_team_indicies]

        team_highlighted_names_no_pos = [team_highlighted_names_no_pos[i] for i in team_indicies]
        not_team_highlighted_names_no_pos = [not_team_highlighted_names_no_pos[i] for i in non_team_indicies]

        # Apply the filtering
        team_rows_df = displayed_df[displayed_df.apply(is_in_team_highlighted, axis=1)]
        team_players_with_positions = team_rows_df[['Player','fantasy_positions']]
        #st.write(team_rows_df)


        if test_front_page:
            st.write(team_indicies)
            st.write(non_team_indicies)

        pgs = players_for_position("PG",team_players_with_positions)
        sgs = players_for_position("SG",team_players_with_positions)
        sfs = players_for_position("SF",team_players_with_positions)
        pfs = players_for_position("PF",team_players_with_positions)
        cs = players_for_position("C",team_players_with_positions)



        position_dict = {
            "PG": pgs,
            "SG": sgs,
            "SF": sfs,
            "PF": pfs,
            "C": cs
        }


        max_len = max(len(players) for players in position_dict.values())


        for pos in position_dict:
            players = position_dict[pos]
            position_dict[pos] = players + [""] * (max_len - len(players))


        grid_df = pd.DataFrame(position_dict)

        st.dataframe(grid_df)

        

        st.markdown("---")

        col_all_players, col_position_players = st.columns([3,2])

        with col_all_players:
            st.subheader("Full Player List")
            displayed_df.index = displayed_df.index + 1
            
            styled_df = displayed_df.style.apply(highlight_row, axis=1)

            st.dataframe(styled_df, use_container_width=True)


        with col_position_players: 
            st.subheader("Position Specific Player List")


            
            positions = st.multiselect(
                "Select Positions",
                ["PG", "SG", "SF", "PF",'C'],
                default=["C"],
            )
            
            positions_equation = st.selectbox(
                "Select Positions",
                ["AND","OR","NOT"],
                index = 1,
            )

                            
            specific_display = displayed_df.copy()
            specific_display.index = specific_display.index + 1
            specific_display['MeetPositionalRequirement'] = specific_display['fantasy_positions'].apply(ast.literal_eval).apply(lambda player_positions: mark_as_good(player_positions, positions_equation, positions)) 
            specific_display = specific_display[specific_display['MeetPositionalRequirement'] == True]
            specific_display = specific_display.drop('MeetPositionalRequirement', axis=1)


            styled_df_pos = specific_display.style.apply(highlight_row, axis=1)

            st.dataframe(styled_df_pos, use_container_width=True)
        if test_front_page:
            st.write("🔍 Scraped Players:", st.session_state.last_scraped_data)
            st.write("🔍 Scraped Positions:", st.session_state.last_scraped_positions)
            st.write("Scraped Draft Numbers:", st.session_state.last_scraped_draft_locations)
        #st.write("Highlighted Entries", highlighted_names)



        if st.session_state.last_scraped_data:
            if test_front_page:
                st.caption(f"Last updated: {st.session_state.last_scrape_time}")
                st.dataframe(
                    {"Pick #": list(range(1, len(st.session_state.last_scraped_data)+1)),
                    "Player": st.session_state.last_scraped_data},
                    use_container_width=True
                )
        else:
            st.info("No data scraped yet.")

##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################
##########################################################################################################################################################



# Placeholder tabs
with tab2:
    st.subheader("Mock Draftboard (Coming Soon)")


    # Create two columns: a thin "sidebar" and a wide main section
    col_sidebar, col_main = st.columns([1, 4])

    #sleeper API data (for fantasy accurate positions and teams)
    uploaded_data = pd.read_csv('../../data/sleeperapidata/updatedsleeperapidata1.csv')
    #current weight that is being used in the application.
    multi_weights = pd.read_csv('../../data/currentweight/currentpointvalues.csv')

    #rankingmodel is the ranking that is set as the main ranking, and this is also automatically converting
    #the names into the same names that are on sleeper. (Sleeper doesn't have suffix while Basketball ref. scraped data does.)
    reference_names = uploaded_data['full_name'].dropna().unique().tolist()
    folder_path = '../../data/current_ranking'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if csv_files:
        csv_path = os.path.join(folder_path, csv_files[0])
        rankingmodel = pd.read_csv(csv_path)
        rankingmodel['Player'] = rankingmodel['Player'].apply(lambda name: get_best_match(name, reference_names))
        current_ranking_name = os.path.splitext(csv_files[0])[0]
        #print(f"Loaded: {csv_files[0]}")
    else:
        print("No CSV files found.")
        
    #Getting data organized and prepared to display.
    
    rankingmodel['GamesPlayedRatio'] = rankingmodel['S_GamesPlayed'].astype(str) + " / " + rankingmodel['TotalGamesSeason'].astype(str)


    merged_data = rankingmodel.merge(
        uploaded_data[['full_name','fantasy_positions','team']],
        how='left',
        left_on='Player',
        right_on='full_name'
    )

    merged_data['PrevFantasyPoints'] = merged_data['S_FantasyPoints'] - (
        (merged_data['S_AvgPoints'] * 0.5) +
        (merged_data['S_AvgAssists'] * 1) +
        (merged_data['S_AvgRebounds'] * 1) +
        (merged_data['S_AvgTurnovers'] * -1) +
        (merged_data['S_AvgSteals'] * 2) +
        (merged_data['S_AvgBlocks'] * 2) +
        (merged_data['S_Avg3P'] * 0.5)
        )

    merged_data['PrevFantasyPoints'] = merged_data['PrevFantasyPoints'] + (
        (merged_data['S_AvgPoints'] * multi_weights['Points'].iloc[0]) +
        (merged_data['S_AvgAssists'] * multi_weights['Assists'].iloc[0]) +
        (merged_data['S_AvgRebounds'] * multi_weights['Rebounds'].iloc[0]) +
        (merged_data['S_AvgTurnovers'] * multi_weights['Turnovers'].iloc[0]) +
        (merged_data['S_AvgSteals'] * multi_weights['Steals'].iloc[0]) +
        (merged_data['S_AvgBlocks'] * multi_weights['Blocks'].iloc[0]) +
        (merged_data['S_Avg3P'] * multi_weights['ThreePointers'].iloc[0])
    )

    merged_data['PrevFantasyPoints'] = (
        (merged_data['PrevFantasyPoints'] * (1 - (multi_weights['GamesMadeWeight'].iloc[0] / 100))) +
        (merged_data['PrevFantasyPoints'] * (multi_weights['GamesMadeWeight'].iloc[0] / 100) * (merged_data['S_GamesPlayed'] / merged_data['TotalGamesSeason']))
    )

    displayed_df_2 = merged_data[['Player','fantasy_positions','team','GamesPlayedRatio','PrevFantasyPoints','Predicted']]

    if 'current_pick' not in st.session_state:
        st.session_state.current_pick = '1.1'
    if 'draft_picks' not in st.session_state:
        st.session_state.draft_picks = []
    if 'picked_players_mock' not in st.session_state:
        st.session_state.picked_players_mock = pd.DataFrame()
    if 'team_players_with_positions_mock' not in st.session_state:
        st.session_state.team_players_with_positions_mock = pd.DataFrame()
    if 'draft_board' not in st.session_state:
        st.session_state.draft_board = displayed_df_2.copy()
        st.session_state.draft_board['Rank'] = st.session_state.draft_board.index + 1
    if 'players_turn' not in st.session_state:
        st.session_state.players_turn = False



    num_drafting_participants = 0
    num_drafting_rounds = 0

    with col_sidebar:
        st.markdown("### 🛠️ Controls")

        num_draft_participants_mock = st.number_input("Number of Draft Participants:", min_value = 1, max_value = 32,value = 8)
        draft_picking_position_mock = st.number_input("Draft Position", min_value = 1, max_value = num_draft_participants_mock, value = 1)
        num_drafting_rounds_mock = st.number_input("Number of rounds", min_value = 1, max_value = 20, value = 16)
        lost_picks_mock = st.text_input("Enter picks you do NOT have anymore (traded away) ")
        added_picks_mock = st.text_input("Enter picks you have aquired (gotten from trading) ")
        st.text("Must be in 'x.x' format, or 'x.x, x.x', or empty.") 


        with st.popover("Save Draft Settings"):
            draft_setting_name_mock = st.text_input("Enter file name to save as. ")

            st.markdown(f"Number of Participants: {num_draft_participants_mock}")
            st.markdown(f"Your Pick Location: {draft_picking_position_mock}")
            st.markdown(f"Rounds: {num_drafting_rounds_mock}")
            if len(lost_picks_mock) == 0:
                st.markdown(f"Didn't lose any picks.")
            else:
                st.markdown(f"Picks you don't have anymore: {lost_picks_mock}")
            if len(added_picks_mock) == 0:
                st.markdown(f"Didn't gain any extra picks.")
            else:
                st.markdown(f"New picks that you gained: {added_picks_mock}")
            if st.button("Confirm and save:"):
                settings = {
                    "num_drafting_participants": num_draft_participants_mock,
                    "draft_picking_position": draft_picking_position_mock,
                    "num_drafting_rounds": num_drafting_rounds_mock,
                    "lost_picks": lost_picks_mock,
                    "added_picks": added_picks_mock
                }

                df_mock = pd.DataFrame([settings])  
                df_mock.to_csv(f"../../data/draft_settings/{draft_setting_name_mock}.csv")
                st.success("Successfully saved to file!")



        if st.button("Update Draft Settings:"): 
            st.session_state.draft_picks = get_draft_picks_list(num_draft_participants_mock, num_drafting_rounds_mock, draft_picking_position_mock, lost_picks_mock, added_picks_mock)
            st.session_state.current_pick = "1.1"
            st.session_state.picked_players_mock = pd.DataFrame()
            st.session_state.team_players_with_positions_mock = pd.DataFrame()
            
            st.session_state.draft_board = displayed_df_2.copy()
            st.session_state.draft_board['Rank'] = st.session_state.draft_board.index + 1
            st.session_state.players_turn = False
            st.success("Updated Draft settings for current mock draft")
          


    with col_main:

        col_start_draft, col_player_sel_dropdown, col_confirm_pick = st.columns([2,3.5,2])

        def get_random_pick(available_players_df):
            random_weight = np.random.normal(loc=1.0, scale=0.1) 
            print(random_weight)
            top_10 = available_players_df.head(10).sort_values('Rank',ascending = True)
            top_10['WeightedRank'] = (top_10['Rank'] - (top_10['Rank'].min() - 1)) ** random_weight
            top_10['Inverse_rank'] = 1 / top_10['WeightedRank']
            total = sum(top_10['Inverse_rank'])
            top_10['FinalProb'] = top_10['Inverse_rank'] / total

            chosen_index = np.random.choice(top_10.index, p=top_10["FinalProb"].values)

            selected_row = top_10.loc[chosen_index]
            rank_taken_out = selected_row[['Rank']].values[0]
            
            taken_player = available_players_df[available_players_df['Rank'] == rank_taken_out]
            rest_of_dataframe = available_players_df[available_players_df['Rank'] != rank_taken_out]

            return [taken_player,rest_of_dataframe]
        
        with col_start_draft:
            if st.button("Start/Continue Draft Picking"):
                if len(st.session_state.draft_picks) != 0:
                    if not st.session_state.players_turn:
                        try:
                            all_draft_picks = list_of_all_draft_picks(num_drafting_rounds_mock, num_draft_participants_mock)
                            draft_picks = st.session_state.draft_picks
                            
                            rest_of_draft_picks = all_draft_picks[all_draft_picks.index(st.session_state.current_pick):]

                            players_next_draft_pick = draft_picks[0]
                            draft_picks = draft_picks[1:]

                            picks_to_simulate = rest_of_draft_picks[:rest_of_draft_picks.index(players_next_draft_pick)]

                            for pick in picks_to_simulate:
                                time.sleep(0.25)
                                player_taken, st.session_state.draft_board = get_random_pick(st.session_state.draft_board)
                                st.session_state.picked_players_mock = pd.concat([st.session_state.picked_players_mock, player_taken], ignore_index=True)
                                st.session_state.current_pick = pick  

                            st.session_state.current_pick = players_next_draft_pick
                            st.session_state.draft_picks = draft_picks
                            st.success(f"Draft simulated up to your next pick ({st.session_state.current_pick})!")
                            st.session_state.players_turn = True
                        except Exception as e:
                            st.warning(f"Error during simulation: {e}")
                    else:
                        st.warning(f"It is pick {st.session_state.current_pick}, and it is your turn to draft.")
                else:
                    st.success("You are finished with the draft!")
                    st.session_state.players_turn = False
            if st.button("Reset Mock Draft"):
                st.session_state.draft_picks = get_draft_picks_list(num_draft_participants_mock, num_drafting_rounds_mock, draft_picking_position_mock, lost_picks_mock, added_picks_mock)
                st.session_state.current_pick = "1.1"
                st.session_state.picked_players_mock = pd.DataFrame()
                st.session_state.team_players_with_positions_mock = pd.DataFrame()
                
                st.session_state.draft_board = displayed_df_2.copy()
                st.session_state.draft_board['Rank'] = st.session_state.draft_board.index + 1
                st.session_state.players_turn = False
                st.success("Reset draft board.")


        with col_player_sel_dropdown:   
            players = st.session_state.draft_board['Player'].unique()
            selected_player = st.selectbox("Choose a player:", players)


        with col_confirm_pick:
            if st.button("Lock In Player:"):
                if st.session_state.players_turn:
                    confirmed_selected_player = selected_player
                    dataframe_player_row = st.session_state.draft_board[st.session_state.draft_board['Player'] == confirmed_selected_player].index[0]
                    selected_row_df = st.session_state.draft_board.loc[[dataframe_player_row]]
                    st.session_state.draft_board = st.session_state.draft_board.drop(dataframe_player_row)
                    st.session_state.team_players_with_positions_mock = pd.concat([st.session_state.team_players_with_positions_mock,selected_row_df], ignore_index = True)
                    st.session_state.players_turn = False

                    all_picks = list_of_all_draft_picks(num_drafting_rounds_mock, num_draft_participants_mock)
                    current_pick_index = all_picks.index(st.session_state.current_pick)
                    if current_pick_index + 1 < len(all_picks):
                        st.session_state.current_pick = all_picks[current_pick_index + 1]
                else:
                    st.warning(f"It is not your turn - please click 'Continue Draft Picking' to continue simulating.")

        if test_front_page:
            st.write(f'These are the players draft picks: {st.session_state.draft_picks}')
            st.dataframe(st.session_state.picked_players_mock)
            st.dataframe(st.session_state.team_players_with_positions_mock)

        st.markdown("---")
        
        try:
            pgs = players_for_position("PG",st.session_state.team_players_with_positions_mock)
            sgs = players_for_position("SG",st.session_state.team_players_with_positions_mock)
            sfs = players_for_position("SF",st.session_state.team_players_with_positions_mock)
            pfs = players_for_position("PF",st.session_state.team_players_with_positions_mock)
            cs = players_for_position("C",st.session_state.team_players_with_positions_mock)
        except:
            pgs = []
            sgs = []
            sfs = []
            pfs = []
            cs = []



        position_dict = {
            "PG": pgs,
            "SG": sgs,
            "SF": sfs,
            "PF": pfs,
            "C": cs
        }


        max_len = max(len(players) for players in position_dict.values())


        for pos in position_dict:
            players = position_dict[pos]
            position_dict[pos] = players + [""] * (max_len - len(players))


        grid_df = pd.DataFrame(position_dict)

        st.dataframe(grid_df)

        

        st.markdown("---")

        col_all_players, col_position_players = st.columns([3,2])

        with col_all_players:
            st.subheader("Full Player List")
            #displayed_df.index = displayed_df.index
            
            styled_df = displayed_df.style.apply(highlight_row_mock, axis=1)

            st.dataframe(styled_df, use_container_width=True)


        with col_position_players: 
            st.subheader("Position Specific Player List")


            
            positions = st.multiselect(
                "Select Positions ",
                ["PG", "SG", "SF", "PF",'C'],
                default=["C"],
            )
            
            positions_equation = st.selectbox(
                "Select Positions ",
                ["AND","OR","NOT"],
                index = 1,
            )

                            
            specific_display = displayed_df.copy()
            #specific_display.index = specific_display.index
            specific_display['MeetPositionalRequirement'] = specific_display['fantasy_positions'].apply(ast.literal_eval).apply(lambda player_positions: mark_as_good(player_positions, positions_equation, positions)) 
            specific_display = specific_display[specific_display['MeetPositionalRequirement'] == True]
            specific_display = specific_display.drop('MeetPositionalRequirement', axis=1)


            styled_df_pos = specific_display.style.apply(highlight_row_mock, axis=1)

            st.dataframe(styled_df_pos, use_container_width=True)



    

with tab3:
    st.subheader("Player Rankings (Coming Soon)")
    st.title("🧩 Drag and Drop List Example")

    col_sidebartab3, col_maintab3 = st.columns([2, 5])


    folder_path = '../../data/current_ranking'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    if csv_files:
        csv_path = os.path.join(folder_path, csv_files[0])
        rankingmodel = pd.read_csv(csv_path)
        current_ranking_name = os.path.splitext(csv_files[0])[0]
        #print(f"Loaded: {csv_files[0]}")
    else:
        print("No CSV files found.")

    uploaded_data = pd.read_csv('../../data/sleeperapidata/updatedsleeperapidata1.csv')
    multi_weights = pd.read_csv('../../data/currentweight/currentpointvalues.csv')

    reference_names = uploaded_data['full_name'].dropna().unique().tolist()

    def get_best_match(name, reference_list, threshold=25):
        match = process.extractOne(name, reference_list, scorer=fuzz.token_sort_ratio)
        if match and match[1] >= threshold:
            return match[0]
        return None 

    rankingmodel['Player'] = rankingmodel['Player'].apply(lambda name: get_best_match(name, reference_names))


    merged_data = rankingmodel.merge(
        uploaded_data[['full_name','fantasy_positions','team']],
        how='left',
        left_on='Player',
        right_on='full_name'
    )



    merged_data['FirstHalfDisplay'] = (
        merged_data['full_name'].astype(str) + " | " +
        merged_data['fantasy_positions'].astype(str) + " | " +
        merged_data['team'].astype(str)
    )

    merged_data['SecondHalfDisplay'] = merged_data['S_FantasyPoints'] - (
    (merged_data['S_AvgPoints'] * 0.5) +
    (merged_data['S_AvgAssists'] * 1) +
    (merged_data['S_AvgRebounds'] * 1) +
    (merged_data['S_AvgTurnovers'] * -1) +
    (merged_data['S_AvgSteals'] * 2) +
    (merged_data['S_AvgBlocks'] * 2) +
    (merged_data['S_Avg3P'] * 0.5)
    )

    merged_data['SecondHalfDisplay'] = merged_data['SecondHalfDisplay'] + (
        (merged_data['S_AvgPoints'] * multi_weights['Points'].iloc[0]) +
        (merged_data['S_AvgAssists'] * multi_weights['Assists'].iloc[0]) +
        (merged_data['S_AvgRebounds'] * multi_weights['Rebounds'].iloc[0]) +
        (merged_data['S_AvgTurnovers'] * multi_weights['Turnovers'].iloc[0]) +
        (merged_data['S_AvgSteals'] * multi_weights['Steals'].iloc[0]) +
        (merged_data['S_AvgBlocks'] * multi_weights['Blocks'].iloc[0]) +
        (merged_data['S_Avg3P'] * multi_weights['ThreePointers'].iloc[0])
    )

    merged_data['SecondHalfDisplay'] = (
        (merged_data['SecondHalfDisplay'] * (1 - (multi_weights['GamesMadeWeight'].iloc[0] / 100))) +
        (merged_data['SecondHalfDisplay'] * (multi_weights['GamesMadeWeight'].iloc[0] / 100) * (merged_data['S_GamesPlayed'] / merged_data['TotalGamesSeason']))
    )

    merged_data['FullDisplay'] = merged_data['FirstHalfDisplay'] + "  |  " + merged_data['SecondHalfDisplay'].round(2).astype(str)

    player_list = merged_data["FullDisplay"].dropna().tolist()
        

    rankings_folder = "../../data/rankings"
    available_rankings = [f for f in os.listdir(rankings_folder) if f.endswith(".csv")]

    if 'current_model' not in st.session_state:
        st.session_state.current_model = pd.DataFrame()
    if 'show_player_comp' not in st.session_state:
        st.session_state.show_player_comp = False
    if 'player1' not in st.session_state:
        st.session_state.player1 = ""
    if 'player2' not in st.session_state:
        st.session_state.player2 = ""
    if 'player3' not in st.session_state:
        st.session_state.player3 = ""
    if 'player4' not in st.session_state:
        st.session_state.player4 = ""


    all_player_data = pd.read_csv("../../data/seasonfullstatsreal/playerbasedatatotal.csv")
    only2025 = all_player_data[all_player_data['Season'] == 2025]
    player_names_2025 = only2025['Player'].unique().tolist()
    


    with col_maintab3:
        st.session_state.show_player_comp = st.toggle("Player Comparison", value = False)
        if st.session_state.show_player_comp:
            selected_year = st.number_input('Years', min_value = 2003, max_value = 2025, value = 2025)
            selected_data = all_player_data[all_player_data['Season'] == selected_year]

            col1, col2, col3, col4 = st.columns([1,1,1,1], border = True)
            with col1:
                
                st.session_state.player1 = st.selectbox("Player 1", player_names_2025, index=player_names_2025.index(st.session_state.player1) if st.session_state.player1 in player_names_2025 else 0)
                player1 = st.session_state.player1
                playerid1 = only2025[only2025['Player'] == player1].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid1}.jpg")
                p1Row = selected_data[selected_data['Player'] == player1].iloc[0]
                stats_df1 = pd.DataFrame({
                    "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                    "Value": [int(p1Row["Age"]), p1Row["Team"], p1Row["YearsExperience"], round(p1Row['S_GamesPlayed'] / p1Row['TotalGamesSeason'],2) * 100,  round(p1Row["S_FantasyPoints"], 2), round(p1Row["S_AvgPoints"], 2), round(p1Row["S_AvgAssists"], 2), round(p1Row["S_AvgRebounds"], 2), round(p1Row["S_AvgSteals"], 2), round(p1Row["S_AvgBlocks"], 2), round(p1Row["S_AvgTurnovers"], 2), round(p1Row["S_Avg3P"], 2)]
                })
                st.markdown(stats_df1.to_html(index=False), unsafe_allow_html=True)            
            with col2:

                st.session_state.player2 = st.selectbox("Player 2", player_names_2025, index=player_names_2025.index(st.session_state.player2) if st.session_state.player2 in player_names_2025 else 0)
                player2 = st.session_state.player2               
                playerid2 = only2025[only2025['Player'] == player2].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid2}.jpg")
                p2Row = selected_data[selected_data['Player'] == player2].iloc[0]
                stats_df2 = pd.DataFrame({
                    "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                    "Value": [int(p2Row["Age"]), p2Row["Team"], p2Row["YearsExperience"], round(p2Row['S_GamesPlayed'] / p2Row['TotalGamesSeason'],2) * 100, round(p2Row["S_FantasyPoints"], 2), round(p2Row["S_AvgPoints"], 2), round(p2Row["S_AvgAssists"], 2), round(p2Row["S_AvgRebounds"], 2), round(p2Row["S_AvgSteals"], 2), round(p2Row["S_AvgBlocks"], 2), round(p2Row["S_AvgTurnovers"], 2), round(p2Row["S_Avg3P"], 2)]
                })
                st.markdown(stats_df2.to_html(index=False), unsafe_allow_html=True)
            with col3:
                st.session_state.player3 = st.selectbox("Player 3", player_names_2025, index=player_names_2025.index(st.session_state.player3) if st.session_state.player3 in player_names_2025 else 0)
                player3 = st.session_state.player3
                playerid3 = only2025[only2025['Player'] == player3].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid3}.jpg")   
                p3Row = selected_data[selected_data['Player'] == player3].iloc[0]
                stats_df3 = pd.DataFrame({
                    "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                    "Value": [int(p3Row["Age"]), p3Row["Team"], p3Row["YearsExperience"], round(p3Row['S_GamesPlayed'] / p3Row['TotalGamesSeason'],2) * 100, round(p3Row["S_FantasyPoints"], 2), round(p3Row["S_AvgPoints"], 2), round(p3Row["S_AvgAssists"], 2), round(p3Row["S_AvgRebounds"], 2), round(p3Row["S_AvgSteals"], 2), round(p3Row["S_AvgBlocks"], 2), round(p3Row["S_AvgTurnovers"], 2), round(p3Row["S_Avg3P"], 2)]
                }) 
                st.markdown(stats_df3.to_html(index=False), unsafe_allow_html=True)      
            with col4:
                
                st.session_state.player4 = st.selectbox("Player 4", player_names_2025, index=player_names_2025.index(st.session_state.player4) if st.session_state.player4 in player_names_2025 else 0)
                player4 = st.session_state.player4
                playerid4 = only2025[only2025['Player'] == player4].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid4}.jpg")
                p4Row = selected_data[selected_data['Player'] == player4].iloc[0]
                stats_df4 = pd.DataFrame({
                    "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                    "Value": [int(p4Row["Age"]), p4Row["Team"], p4Row["YearsExperience"], round(p4Row['S_GamesPlayed'] / p4Row['TotalGamesSeason'],2) * 100, round(p4Row["S_FantasyPoints"], 2), round(p4Row["S_AvgPoints"], 2), round(p4Row["S_AvgAssists"], 2), round(p4Row["S_AvgRebounds"], 2), round(p4Row["S_AvgSteals"], 2), round(p4Row["S_AvgBlocks"], 2), round(p4Row["S_AvgTurnovers"], 2), round(p4Row["S_Avg3P"], 2)]
                }) 
                st.markdown(stats_df4.to_html(index=False), unsafe_allow_html=True)  

        col_player_ranking, col_player_model = st.columns([4,2.5])

        with col_player_ranking:
            custom_style = """
            .sortable-component {
                border: 3px solid #6495ED;
                border-radius: 10px;
                padding: 5px;
            }
            .sortable-container {
                background-color: #F0F0F0;
                counter-reset: item;
            }
            .sortable-container-header {
                background-color: #FFBFDF;
                padding-left: 1rem;
            }
            .sortable-container-body {
                background-color: #F0F0F0;
            }
            .sortable-item, .sortable-item:hover {
                background-color: #6495ED;
                color: #FFFFFF;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
            }
            .sortable-item::before {
                content: counter(item) ". ";
                counter-increment: item;
            }
            """

            sorted_items = sort_items(player_list, multi_containers=False, custom_style=custom_style, direction="vertical")
            st.session_state["player_list"] = sorted_items
            st.write("🔢 Sorted Items:")
            # for i, player in enumerate(sorted_items, start=1):
            #     st.write(f"{i}. {player}")



        with col_player_model:
            model_preset = st.selectbox("🔁 Load Existing Model", options=["None"] + available_rankings)

            if model_preset != "None" and st.button("📥 Load Model Preset"):
                st.session_state.current_model = pd.read_csv(os.path.join(rankings_folder, model_preset))[['Player','Predicted']]
                st.session_state.current_model.index = st.session_state.current_model.index + 1
                st.success(f"Model is loaded.") 
                st.rerun()
            st.dataframe(st.session_state.current_model)
            

            



    with col_sidebartab3:
        st.markdown("### 🛠️ Controls")



        NewRankingName = st.text_input("Name of new ranking:")
        
        if st.button("Save as new ranking"):
            sorted_names = [entry.split(" | ")[0] for entry in sorted_items]
            sorted_df = pd.DataFrame(sorted_names, columns=['Player'])
            

            saveable_data = sorted_df.merge(
                rankingmodel,
                how='left',
                left_on='Player',
                right_on='Player'
            )

            

            saveable_data = saveable_data[['Player','PlayerID','Predicted','S_GamesPlayed','TotalGamesSeason','S_FantasyPoints','S_AvgPoints','S_AvgAssists','S_AvgRebounds','S_AvgSteals','S_AvgBlocks','S_AvgTurnovers','S_Avg3P']]
            if len(NewRankingName) == 0:
                st.error('Please give a name for your ranking.')
            else:
                saveable_data.to_csv(f'../../data/rankings/{NewRankingName}.csv')
                folder_path = '../../data/current_ranking'
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                saveable_data.to_csv(f'../../data/current_ranking/{NewRankingName}.csv')               
                st.success(f"Successfully saved ranking to ../../data/rankings/{NewRankingName} ")
                        

        st.markdown("---")

        st.markdown(f"#### Name of active ranking: {current_ranking_name}")
        
        if st.button("Save current ranking"):
            st.write("Temporary Text")
            sorted_names = [entry.split(" | ")[0] for entry in sorted_items]
            sorted_df = pd.DataFrame(sorted_names, columns=['Player'])

            saveable_data = sorted_df.merge(
                rankingmodel,
                how='left',
                left_on='Player',
                right_on='Player'
            )

            saveable_data = saveable_data[['Player','PlayerID','Predicted','S_GamesPlayed','TotalGamesSeason','S_FantasyPoints','S_AvgPoints','S_AvgAssists','S_AvgRebounds','S_AvgSteals','S_AvgBlocks','S_AvgTurnovers','S_Avg3P']]
            saveable_data.to_csv(f'../../data/rankings/{current_ranking_name}.csv')
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            saveable_data.to_csv(f'../../data/current_ranking/{current_ranking_name}.csv')  
            st.success(f"Successfully saved ranking to ../../data/rankings/{current_ranking_name} ")

        st.markdown("---")

        ranking_preset = st.selectbox("🔁 Load Existing Rankings", options=["None"] + available_rankings)

        if ranking_preset != "None" and st.button("📥 Load Ranking Preset"):
            preset_ranking_df = pd.read_csv(os.path.join(rankings_folder, ranking_preset))
            folder_path = '../../data/current_ranking'
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            preset_ranking_df.to_csv(f'../../data/current_ranking/{ranking_preset}.csv')
            st.success(f"Ranking is current ranking.") 
            st.rerun()


        st.markdown("---")

        if st.button("Get Updated Player Teams and Positions"):

            current_time = pd.Timestamp.now()

            try:
                with open("../../data/sleeperapidata/timestamp.txt", "r") as f:
                    ts_str = f.read()
                    last_update_time = pd.Timestamp(ts_str)
            except Exception:
                # If file doesn't exist or can't parse, set last_update_time far in the past
                last_update_time = current_time - timedelta(days=2)

            duration = current_time - last_update_time

            if duration > pd.Timedelta(days=1):
                response = requests.get('https://api.sleeper.app/v1/players/nba')
                base_data = response.json()

                player_dataframe = pd.DataFrame(base_data).T
                player_dataframe = player_dataframe[['full_name', 'fantasy_positions', 'team']]
                player_dataframe = player_dataframe.drop_duplicates(subset='full_name', keep='first')
                player_dataframe.to_csv('../../data/sleeperapidata/updatedsleeperapidata1.csv', index=False)
                st.success("Successfully got updated player information from sleeper!")

                with open("../../data/sleeperapidata/timestamp.txt", "w") as f:
                    f.write(current_time.isoformat())
                
                st.success("Player data updated successfully!")
            else:
                wait_time = pd.Timedelta(days=1) - duration
                st.warning(f"Can't send Sleeper API request: please wait {wait_time} more.")


with tab4:
    
    weights_folder = "../../data/latestweights"
    available_weights = [f for f in os.listdir(weights_folder) if f.endswith(".csv")]


    defaults = {
        "Points": st.session_state.get("Points", 0.5),
        "Assists": st.session_state.get("Assists", 1.0),
        "Rebounds": st.session_state.get("Rebounds", 1.0),
        "Steals": st.session_state.get("Steals", 2.0),
        "Blocks": st.session_state.get("Blocks", 2.0),
        "Turnovers": st.session_state.get("Turnovers", -1.0),
        "ThreePointers": st.session_state.get("ThreePointers", 0.5),
        "GamesMadeWeight": st.session_state.get("GamesMadeWeight", 0.3),
    }
    

    points_val = st.number_input("Points Value", value=defaults["Points"], min_value=-10.0, max_value=10.0, step=0.25)
    assists_val = st.number_input("Assists Value", value=defaults["Assists"], min_value=-10.0, max_value=10.0, step=0.25)
    rebounds_val = st.number_input("Rebound Value", value=defaults["Rebounds"], min_value=-10.0, max_value=10.0, step=0.25)
    steals_val = st.number_input("Steal Value", value=defaults["Steals"], min_value=-10.0, max_value=10.0, step=0.25)
    blocks_val = st.number_input("Block Value", value=defaults["Blocks"], min_value=-10.0, max_value=10.0, step=0.25)
    turnovers_val = st.number_input("Turnover Value", value=defaults["Turnovers"], min_value=-10.0, max_value=10.0, step=0.25)
    three_point_val = st.number_input("3 Point Value", value=defaults["ThreePointers"], min_value=-10.0, max_value=10.0, step=0.25)

    weight = st.slider("Games Made Weight", min_value=0, max_value=100, value=int(defaults["GamesMadeWeight"]), format="%d%%")
    st.caption(f"Weight: {'No Game Weight' if weight == 0 else 'All Games Weight' if weight == 100 else str(weight) + '%'}")

    preset = st.selectbox("🔁 Load Existing Weights", options=["None"] + available_weights)


    if preset != "None" and st.button("📥 Load Preset"):
        preset_df = pd.read_csv(os.path.join(weights_folder, preset))
        preset_df.to_csv('../../data/currentweight/currentpointvalues.csv')
        st.success(f"Preset is now app wide values.") 
        if not preset_df.empty:
            for key in defaults:
                st.session_state[key] = preset_df.iloc[0][key]
            st.rerun() 
            


    if st.button("Confirm Current Preset"):
        weights = {
        "Points": points_val,
        "Assists": assists_val,
        "Rebounds": rebounds_val,
        "Steals": steals_val,
        "Blocks": blocks_val,
        "Turnovers": turnovers_val,
        "ThreePointers": three_point_val,
        "GamesMadeWeight": weight
        }

        weights_df = pd.DataFrame([weights])
        weights_df.to_csv('../../data/currentweight/currentpointvalues.csv')
        st.success(f"Weight Configuration has been confirmed across the app.")

    st.subheader("Model Changing (Coming Soon)")






    weights = {
        "Points": points_val,
        "Assists": assists_val,
        "Rebounds": rebounds_val,
        "Steals": steals_val,
        "Blocks": blocks_val,
        "Turnovers": turnovers_val,
        "ThreePointers": three_point_val,
        "GamesMadeWeight": weight
    }
    weights_df = pd.DataFrame([weights])


    st.write("### Current Settings")
    st.dataframe(weights_df)


    weight_name = st.text_input('Name the weight')
    if st.button("💾 Save Weights to CSV"):
        save_path = os.path.join(weights_folder, f"weight_{weight_name}.csv")
        weights_df.to_csv(save_path, index=False)
        st.success(f"Weights saved to `{save_path}`")

    
    