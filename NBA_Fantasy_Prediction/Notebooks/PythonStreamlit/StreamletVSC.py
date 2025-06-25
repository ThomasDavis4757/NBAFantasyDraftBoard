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
from pandas.api.types import is_numeric_dtype
from sklearn.impute import SimpleImputer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor

#print(streamlit_sortables.__version__)

test_front_page = False

model_columns = [
    'Unnamed: 0.2', 'Unnamed: 0.1', 'Unnamed: 0', 'Player', 'Ht', 'Wt', 'Birth Date', 'Colleges', 'PlayerID',
    'RecuitRank', 'TeamDrafted', 'PickDrafted', 'Starters', 'S_TotalWins', 'S_GamesPlayed', 'S_AvgPoints',
    'S_AvgAssists', 'S_AvgRebounds', 'S_AvgSteals', 'S_AvgBlocks', 'S_AvgTurnovers', 'S_AvgFG', 'S_AvgFGA',
    'S_Avg3P', 'S_Avg3PA', 'S_AvgFT', 'S_AvgFTA', 'S_FantasyPoints', 'S_MinutesPlayed', 'S_GamePointDiff',
    'S_StartingCount', 'S_Top7Team', 'Season', 'TotalGamesSeason', 'HS_TotalWins', 'HS_GamesPlayed',
    'HS_AvgPoints', 'HS_AvgAssists', 'HS_AvgRebounds', 'HS_AvgSteals', 'HS_AvgBlocks', 'HS_AvgTurnovers',
    'HS_AvgFG', 'HS_AvgFGA', 'HS_Avg3P', 'HS_Avg3PA', 'HS_AvgFT', 'HS_AvgFTA', 'HS_FantasyPoints',
    'HS_MinutesPlayed', 'HS_GamePointDiff', 'HS_StartingCount', 'HS_Top7Team', 'Age', 'PrimaryPosition',
    'Team', 'NewPos1', 'NewPos2', 'NewPos3', 'FirstSeason', 'FirstSeasonYear', 'YearsExperience',
    'PickDraftedNumber', 'S_TotalWins_prevyear', 'S_GamesPlayed_prevyear', 'S_AvgPoints_prevyear',
    'S_AvgAssists_prevyear', 'S_AvgRebounds_prevyear', 'S_AvgSteals_prevyear', 'S_AvgBlocks_prevyear',
    'S_AvgTurnovers_prevyear', 'S_AvgFG_prevyear', 'S_AvgFGA_prevyear', 'S_Avg3P_prevyear', 'S_Avg3PA_prevyear',
    'S_AvgFT_prevyear', 'S_AvgFTA_prevyear', 'S_FantasyPoints_prevyear', 'S_MinutesPlayed_prevyear',
    'S_GamePointDiff_prevyear', 'S_StartingCount_prevyear', 'S_Top7Team_prevyear', 'TotalGamesSeason_prevyear',
    'S_TotalWins_prev5years', 'S_GamesPlayed_prev5years', 'S_AvgPoints_prev5years', 'S_AvgAssists_prev5years',
    'S_AvgRebounds_prev5years', 'S_AvgSteals_prev5years', 'S_AvgBlocks_prev5years', 'S_AvgTurnovers_prev5years',
    'S_AvgFG_prev5years', 'S_AvgFGA_prev5years', 'S_Avg3P_prev5years', 'S_Avg3PA_prev5years', 'S_AvgFT_prev5years',
    'S_AvgFTA_prev5years', 'S_FantasyPoints_prev5years', 'S_MinutesPlayed_prev5years',
    'S_GamePointDiff_prev5years', 'S_StartingCount_prev5years', 'S_Top7Team_prev5years',
    'TotalGamesSeason_prev5years', 'S_TotalWins_futureyear', 'S_GamesPlayed_futureyear',
    'S_AvgPoints_futureyear', 'S_AvgAssists_futureyear', 'S_AvgRebounds_futureyear', 'S_AvgSteals_futureyear',
    'S_AvgBlocks_futureyear', 'S_AvgTurnovers_futureyear', 'S_AvgFG_futureyear', 'S_AvgFGA_futureyear',
    'S_Avg3P_futureyear', 'S_Avg3PA_futureyear', 'S_AvgFT_futureyear', 'S_AvgFTA_futureyear',
    'S_FantasyPoints_futureyear', 'S_MinutesPlayed_futureyear', 'S_GamePointDiff_futureyear',
    'S_StartingCount_futureyear', 'S_Top7Team_futureyear', 'TotalGamesSeason_futureyear', 'TargetVariable'
]




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
            list_of_positions.append(str(i+1) + "." + str(int(picking_pos)))
        else:
            list_of_positions.append(str(i+1) + "." + str(int(draft_participants) - (int(picking_pos) - 1)))
    
    try:
        list_not_owned = not_owned_dps.split(',')
    except:
        list_not_owned = []
    try:
        list_newly_owned = newly_owned_dps.split(',')
    except:
        list_newly_owned = []
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

########################################################################################################################################################

def list_of_all_draft_picks(rounds,num_participants):
    total_picks = rounds * num_participants
    list_of_dps = []
    for i in range(int(rounds)):
        for j in range(int(num_participants)):
            list_of_dps.append(str(i+1) + '.' + str(j+1))
    return list_of_dps

########################################################################################################################################################

def style_stats_df(stats_df, ranks_list):
    """Apply color styling to the 'Value' column based on provided rank list."""
    def color_row(val, rank):
        color = RANK_COLORS.get(rank, "white")
        return f'<span style="color:{color}">{val}</span>'

    styled_rows = []
    for i, row in stats_df.iterrows():
        stat = row['Stat']
        value = row['Value']
        rank = ranks_list[i]
        styled_val = color_row(value, rank)
        styled_rows.append((stat, styled_val))

    styled_df = pd.DataFrame(styled_rows, columns=["Stat", "Value"])
    return styled_df.to_html(index=False, escape=False)

########################################################################################################################################################

def get_player_ranks_for_index(player_index: int, stat_ranks: dict) -> list:
    # These must be in the same order as the 'Stat' column in your stats_df
    stat_order = ["Age", "Team", "Years of Experience", "PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"]
    ranks = []
    for stat in stat_order:
        if stat == "Team":  # Non-numeric, no rank
            ranks.append(None)
        elif stat == "PercGamesMade":
            ranks.append(stat_ranks["PercGamesMade"][player_index])
        elif stat == "Years of Experience":
            ranks.append(stat_ranks["YearsExperience"][player_index])
        else:
            ranks.append(stat_ranks[stat][player_index])
    return ranks

########################################################################################################################################################

def add_prediction_value(df, games_made_weight = 0.0, stat_weights = [0.5,1,1,-1,2,2,0.5]):
    df = df.copy()
    
#     Stat weight List
#     first_number - points
#     second_number - Assists
#     third number - Rebounds
#     fourth number - Turnovers
#     fifth number - steals
#     sixth number - blocks
#     seventh number - 3pointers

    
    
    df['TargetVariable'] = df['S_FantasyPoints_futureyear'] - (
        (df['S_AvgPoints_futureyear'] * 0.5) +
        (df['S_AvgAssists_futureyear'] * 1) +
        (df['S_AvgRebounds_futureyear'] * 1) +
        (df['S_AvgTurnovers_futureyear'] * -1) +
        (df['S_AvgSteals_futureyear'] * 2) +
        (df['S_AvgBlocks_futureyear'] * 2) +
        (df['S_Avg3P_futureyear'] * 0.5) 
    )
    
    df['TargetVariable'] = df['TargetVariable'] + (
        (df['S_AvgPoints_futureyear'] * stat_weights[0]) +
        (df['S_AvgAssists_futureyear'] * stat_weights[1]) +
        (df['S_AvgRebounds_futureyear'] * stat_weights[2]) +
        (df['S_AvgTurnovers_futureyear'] * stat_weights[5]) +
        (df['S_AvgSteals_futureyear'] * stat_weights[3]) +
        (df['S_AvgBlocks_futureyear'] * stat_weights[4]) +
        (df['S_Avg3P_futureyear'] * stat_weights[6]) 
    )
    
    df['TargetVariable'] = (
    (df['TargetVariable'] * (1 - (games_made_weight / 100))) +
    (df['TargetVariable'] * (games_made_weight / 100) * (df['S_GamesPlayed_futureyear'] / df['TotalGamesSeason_futureyear']))
    )
    
#     df['S_PercGamesMade'] = df['S_GamesPlayed'] / df['TotalGamesSeason']
#     df['S_PercGamesMade_prevyear'] = df['S_GamesPlayed_prevyear'] / df['TotalGamesSeason_prevyear']
#     df['S_PercGamesMade_prev5years'] = df['S_GamesPlayed_prev5years'] / df['TotalGamesSeason_prev5years']
    
    
    return df
   

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
    st.title("🏀 Live Draft Board (Sleeper)")

    # Create two columns: a thin "sidebar" and a wide main section
    col_sidebar, col_main = st.columns([1, 4], border = True)

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
                    st.write(names)
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
    st.title("Mock Draftboard")


    # Create two columns: a thin "sidebar" and a wide main section
    col_sidebar, col_main = st.columns([1, 4], border = True)

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
    if 'num_participants' not in st.session_state:
        st.session_state.num_participants = 8
    if 'draft_pos' not in st.session_state:
        st.session_state.draft_pos = 1
    if 'rounds' not in st.session_state:
        st.session_state.rounds = 16
    if 'lost_picks' not in st.session_state:
        st.session_state.lost_picks = ""
    if 'added_picks' not in st.session_state:
        st.session_state.added_picks = ""




    num_drafting_participants = 0
    num_drafting_rounds = 0

    with col_sidebar:
        st.markdown("### 🛠️ Controls")

        num_participants_mock = st.number_input("Number of Draft Participants:", min_value = 1, max_value = 32,value = int(st.session_state.num_participants))
        draft_pos_mock = st.number_input("Draft Position", min_value = 1, max_value = int(st.session_state.num_participants), value = int(st.session_state.draft_pos))
        rounds_mock = st.number_input("Number of rounds", min_value = 1, max_value = 20, value = int(st.session_state.rounds))
        lost_picks_mock = st.text_input("Enter picks you do NOT have anymore (traded away) ",value= st.session_state.lost_picks)
        added_picks_mock = st.text_input("Enter picks you have aquired (gotten from trading) ", value= st.session_state.added_picks)
        st.text("Must be in 'x.x' format, or 'x.x, x.x', or empty.") 

        if st.button("Update Draft Settings:"): 
            st.session_state.draft_picks = get_draft_picks_list(st.session_state.num_participants, st.session_state.rounds, st.session_state.draft_pos, st.session_state.lost_picks, st.session_state.added_picks)

            st.session_state.current_pick = "1.1"
            st.session_state.picked_players_mock = pd.DataFrame()
            st.session_state.team_players_with_positions_mock = pd.DataFrame()
            
            st.session_state.draft_board = displayed_df_2.copy()
            st.session_state.draft_board['Rank'] = st.session_state.draft_board.index + 1
            st.session_state.players_turn = False

            st.session_state.num_participants = num_participants_mock
            st.session_state.draft_pos = draft_pos_mock
            st.session_state.rounds = rounds_mock
            st.session_state.lost_picks = lost_picks_mock
            st.session_state.added_picks = added_picks_mock
            st.success("Updated Draft settings for current mock draft")
            st.rerun()

        st.markdown("---")

        with st.popover("Save Current Draft Settings"):
            draft_setting_name_mock = st.text_input("Enter file name to save as. ")

            st.markdown(f"Number of Participants: {num_participants_mock}")
            st.markdown(f"Your Pick Location: {draft_pos_mock}")
            st.markdown(f"Rounds: {rounds_mock}")
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
                    "num_drafting_participants": num_participants_mock,
                    "draft_picking_position": draft_pos_mock,
                    "num_drafting_rounds": rounds_mock,
                    "lost_picks": lost_picks_mock,
                    "added_picks": added_picks_mock
                }

                df_mock = pd.DataFrame([settings])  
                df_mock.to_csv(f"../../data/draft_settings/{draft_setting_name_mock}.csv")
                st.success("Successfully saved to file!")

        st.markdown("---")
        draftsettings_folder = "../../data/draft_settings"
        available_draftsettings = [f for f in os.listdir(draftsettings_folder) if f.endswith(".csv")]
        draftsettings_preset = st.selectbox("🔁 Load Existing Draft Settings", options=["None"] + available_draftsettings)
        
        if draftsettings_preset != "None" and st.button("📥 Load Ranking Preset"):
            draft_settings_df = pd.read_csv(os.path.join(draftsettings_folder, draftsettings_preset))
            st.session_state.num_participants = draft_settings_df.iloc[0]['num_drafting_participants']
            st.session_state.draft_pos = draft_settings_df.iloc[0]['draft_picking_position']
            st.session_state.rounds = draft_settings_df.iloc[0]['num_drafting_rounds']
            st.session_state.lost_picks = draft_settings_df.iloc[0]['lost_picks']
            st.session_state.added_picks= draft_settings_df.iloc[0]['added_picks']
            st.session_state.draft_picks = get_draft_picks_list(st.session_state.num_participants, st.session_state.rounds, st.session_state.draft_pos, st.session_state.lost_picks, st.session_state.added_picks)
            st.session_state.current_pick = "1.1"
            st.session_state.picked_players_mock = pd.DataFrame()
            st.session_state.team_players_with_positions_mock = pd.DataFrame()
            
            st.session_state.draft_board = displayed_df_2.copy()
            st.session_state.draft_board['Rank'] = st.session_state.draft_board.index + 1
            st.session_state.players_turn = False
            st.success("Updated Draft settings for current mock draft")
            st.success(f"Draft Settings have been updated.") 
            st.rerun()




          


    with col_main:
        
        displaying_draft_settings_df = pd.DataFrame([
            {
                "Participants": int(st.session_state.num_participants),
                "Rounds": int(st.session_state.rounds),
                "Your Draft Position": int(st.session_state.draft_pos),
                "Lost Picks": st.session_state.lost_picks,
                "Gained Picks": st.session_state.added_picks
            }
        ])
        st.text("Mock Draft Current Settings")
        st.table(displaying_draft_settings_df)
        st.markdown("---")

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
                        # try:
                            all_draft_picks = list_of_all_draft_picks(st.session_state.rounds, st.session_state.num_participants)
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
                        # except Exception as e:
                        #     st.warning(f"Error during simulation: {e}")
                    else:
                        st.warning(f"It is pick {st.session_state.current_pick}, and it is your turn to draft.")
                else:
                    st.success("You are finished with the draft!")
                    st.session_state.players_turn = False
            if st.button("Reset Mock Draft"):
                st.session_state.draft_picks = get_draft_picks_list(st.session_state.num_participants, st.session_state.rounds, st.session_state.draft_pos, st.session_state.lost_picks, st.session_state.added_picks)
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

                    all_picks = list_of_all_draft_picks(rounds_mock, num_participants_mock)
                    current_pick_index = all_picks.index(st.session_state.current_pick)
                    if current_pick_index + 1 < len(all_picks):
                        st.session_state.current_pick = all_picks[current_pick_index + 1]
                else:
                    st.warning(f"It is not your turn - please click 'Continue Draft Picking' to continue simulating.")

        # if True:
        #     st.write(f'These are the players draft picks: {st.session_state.draft_picks}')
        #     st.dataframe(st.session_state.picked_players_mock)
        #     st.dataframe(st.session_state.team_players_with_positions_mock)

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
    st.title("Player Rankings")


    col_sidebartab3, col_maintab3 = st.columns([2, 5])

    def define_player_list_sortable():
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

        def get_best_match(name, reference_list, threshold=15):
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
        
        return player_list
    player_list = define_player_list_sortable()

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
    if 'player_list' not in st.session_state:
        st.session_state.player_list = player_list
    


    all_player_data = pd.read_csv("../../data/seasonfullstatsreal/playerbasedatatotal.csv")
    only2025 = all_player_data[all_player_data['Season'] == 2025]
    player_names_2025 = only2025['Player'].unique().tolist()
    


    with col_maintab3:
        st.session_state.show_player_comp = st.toggle("Player Comparison", value = False)
        if st.session_state.show_player_comp:
            selected_year = st.number_input('Years', min_value = 2003, max_value = 2025, value = 2025)
            selected_data = all_player_data[all_player_data['Season'] == selected_year]


            col1, col2, col3, col4 = st.columns([1,1,1,1], border = True)
            all_players_found = True
            with col1:
                
                st.session_state.player1 = st.selectbox("Player 1", player_names_2025, index=player_names_2025.index(st.session_state.player1) if st.session_state.player1 in player_names_2025 else 0)
                player1 = st.session_state.player1
                playerid1 = only2025[only2025['Player'] == player1].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid1}.jpg")
                try:
                    p1Row = selected_data[selected_data['Player'] == player1].iloc[0]
                except IndexError:
                    all_players_found = False
                           
            with col2:

                st.session_state.player2 = st.selectbox("Player 2", player_names_2025, index=player_names_2025.index(st.session_state.player2) if st.session_state.player2 in player_names_2025 else 0)
                player2 = st.session_state.player2               
                playerid2 = only2025[only2025['Player'] == player2].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid2}.jpg")
                try:
                    p2Row = selected_data[selected_data['Player'] == player2].iloc[0]

                except IndexError:
                    all_players_found = False
                 
            with col3:
                st.session_state.player3 = st.selectbox("Player 3", player_names_2025, index=player_names_2025.index(st.session_state.player3) if st.session_state.player3 in player_names_2025 else 0)
                player3 = st.session_state.player3
                playerid3 = only2025[only2025['Player'] == player3].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid3}.jpg")   
                try:
                    p3Row = selected_data[selected_data['Player'] == player3].iloc[0]
                except IndexError:
                    all_players_found = False
                 
            with col4:
                
                st.session_state.player4 = st.selectbox("Player 4", player_names_2025, index=player_names_2025.index(st.session_state.player4) if st.session_state.player4 in player_names_2025 else 0)
                player4 = st.session_state.player4
                playerid4 = only2025[only2025['Player'] == player4].iloc[0]['PlayerID']
                st.image(f"https://www.basketball-reference.com/req/202106291/images/headshots/{playerid4}.jpg")
                try:
                    p4Row = selected_data[selected_data['Player'] == player4].iloc[0]
                except IndexError:
                    all_players_found = False
                 
            if all_players_found:
                players_stats_df = pd.DataFrame([p1Row, p2Row, p3Row, p4Row], index=["Player 1", "Player 2", "Player 3", "Player 4"])
                stat_ranks = {
                    "Age": players_stats_df["Age"].rank(ascending=True, method="min").astype(int).tolist(),
                    "YearsExperience": players_stats_df["YearsExperience"].rank(ascending=False, method="min").astype(int).tolist(),
                    "PercGamesMade": (players_stats_df["S_GamesPlayed"] / players_stats_df["TotalGamesSeason"]).rank(ascending=False, method="min").astype(int).tolist(),
                    "Fantasy Points": players_stats_df["S_FantasyPoints"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Points": players_stats_df["S_AvgPoints"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Assists": players_stats_df["S_AvgAssists"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Rebounds": players_stats_df["S_AvgRebounds"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Steals": players_stats_df["S_AvgSteals"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Blocks": players_stats_df["S_AvgBlocks"].rank(ascending=False, method="min").astype(int).tolist(),
                    "Turnovers": players_stats_df["S_AvgTurnovers"].rank(ascending=True, method="min").astype(int).tolist(),
                    "3PM": players_stats_df["S_Avg3P"].rank(ascending=False, method="min").astype(int).tolist()
                }
                
                RANK_COLORS = {
                    1: "#00FF00",   
                    2: "#FFFF00",   
                    3: "#FFA500",   
                    4: "#FF0000"    
                }
                with col1:
                    stats_df1 = pd.DataFrame({
                        "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                        "Value": [int(p1Row["Age"]), p1Row["Team"], p1Row["YearsExperience"], round(p1Row['S_GamesPlayed'] / p1Row['TotalGamesSeason'],2) * 100,  round(p1Row["S_FantasyPoints"], 2), round(p1Row["S_AvgPoints"], 2), round(p1Row["S_AvgAssists"], 2), round(p1Row["S_AvgRebounds"], 2), round(p1Row["S_AvgSteals"], 2), round(p1Row["S_AvgBlocks"], 2), round(p1Row["S_AvgTurnovers"], 2), round(p1Row["S_Avg3P"], 2)]
                    })
                    # st.markdown(stats_df1.to_html(index=False), unsafe_allow_html=True)
                    player1_ranks = get_player_ranks_for_index(0, stat_ranks)
                    st.markdown(style_stats_df(stats_df1, player1_ranks), unsafe_allow_html=True)
                with col2:
                    stats_df2 = pd.DataFrame({
                        "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                        "Value": [int(p2Row["Age"]), p2Row["Team"], p2Row["YearsExperience"], round(p2Row['S_GamesPlayed'] / p2Row['TotalGamesSeason'],2) * 100, round(p2Row["S_FantasyPoints"], 2), round(p2Row["S_AvgPoints"], 2), round(p2Row["S_AvgAssists"], 2), round(p2Row["S_AvgRebounds"], 2), round(p2Row["S_AvgSteals"], 2), round(p2Row["S_AvgBlocks"], 2), round(p2Row["S_AvgTurnovers"], 2), round(p2Row["S_Avg3P"], 2)]
                    })
                    # st.markdown(stats_df2.to_html(index=False), unsafe_allow_html=True)
                    player2_ranks = get_player_ranks_for_index(1, stat_ranks)
                    st.markdown(style_stats_df(stats_df2, player2_ranks), unsafe_allow_html=True)
                with col3:
                    stats_df3 = pd.DataFrame({
                        "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                        "Value": [int(p3Row["Age"]), p3Row["Team"], p3Row["YearsExperience"], round(p3Row['S_GamesPlayed'] / p3Row['TotalGamesSeason'],2) * 100, round(p3Row["S_FantasyPoints"], 2), round(p3Row["S_AvgPoints"], 2), round(p3Row["S_AvgAssists"], 2), round(p3Row["S_AvgRebounds"], 2), round(p3Row["S_AvgSteals"], 2), round(p3Row["S_AvgBlocks"], 2), round(p3Row["S_AvgTurnovers"], 2), round(p3Row["S_Avg3P"], 2)]
                    }) 
                    # st.markdown(stats_df3.to_html(index=False), unsafe_allow_html=True)  
                    player3_ranks = get_player_ranks_for_index(2, stat_ranks)
                    st.markdown(style_stats_df(stats_df3, player3_ranks), unsafe_allow_html=True)
                with col4:
                    stats_df4 = pd.DataFrame({
                        "Stat": ["Age", "Team", "Years of Experience","PercGamesMade", "Fantasy Points", "Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "3PM"],
                        "Value": [int(p4Row["Age"]), p4Row["Team"], p4Row["YearsExperience"], round(p4Row['S_GamesPlayed'] / p4Row['TotalGamesSeason'],2) * 100, round(p4Row["S_FantasyPoints"], 2), round(p4Row["S_AvgPoints"], 2), round(p4Row["S_AvgAssists"], 2), round(p4Row["S_AvgRebounds"], 2), round(p4Row["S_AvgSteals"], 2), round(p4Row["S_AvgBlocks"], 2), round(p4Row["S_AvgTurnovers"], 2), round(p4Row["S_Avg3P"], 2)]
                    }) 
                    # st.markdown(stats_df4.to_html(index=False), unsafe_allow_html=True)
                    player4_ranks = get_player_ranks_for_index(3, stat_ranks)
                    st.markdown(style_stats_df(stats_df4, player4_ranks), unsafe_allow_html=True)
            else:
                st.warning("Not All players played in this year.")




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

            sorted_items = sort_items(st.session_state["player_list"], multi_containers=False, custom_style=custom_style, direction="vertical")
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
            saveable_data.to_csv(f'../../data/rankings/{current_ranking_name}')
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            saveable_data.to_csv(f'../../data/current_ranking/{current_ranking_name}')  
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
            st.session_state.player_list = define_player_list_sortable()
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
    st.title("Predictive Model/Weight Configuration")
    weights_folder = "../../data/latestweights"
    available_weights = [f for f in os.listdir(weights_folder) if f.endswith(".csv")]



    cola, colb = st.columns([2,5.5], border = True)

    with colb:
        preset = st.selectbox("🔁 Load Existing Weights", options=["None"] + available_weights)

        # If preset is selected and button is clicked, apply it before anything else
        if preset != "None" and st.button("📥 Load Preset"):
            preset_df = pd.read_csv(os.path.join(weights_folder, preset))
            preset_df.to_csv('../../data/currentweight/currentpointvalues.csv')
            st.success(f"Preset is now app wide values.") 
            if not preset_df.empty:
                for key in ["Points", "Assists", "Rebounds", "Steals", "Blocks", "Turnovers", "ThreePointers", "GamesMadeWeight"]:
                    st.session_state[key] = preset_df.iloc[0][key]
                st.rerun()

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
    


    with cola:
        points_val = st.number_input("Points Value", min_value=-10.0, max_value=10.0, step=0.25, key = 'Points')
        assists_val = st.number_input("Assists Value",  min_value=-10.0, max_value=10.0, step=0.25, key = 'Assists')
        rebounds_val = st.number_input("Rebound Value",  min_value=-10.0, max_value=10.0, step=0.25, key = 'Rebounds')
        steals_val = st.number_input("Steal Value",  min_value=-10.0, max_value=10.0, step=0.25, key = 'Steals')
        blocks_val = st.number_input("Block Value",  min_value=-10.0, max_value=10.0, step=0.25, key ='Blocks')
        turnovers_val = st.number_input("Turnover Value",  min_value=-10.0, max_value=10.0, step=0.25, key = 'Turnovers')
        three_point_val = st.number_input("3 Point Value",  min_value=-10.0, max_value=10.0, step=0.25, key = 'ThreePointers')

        weight = st.slider("Games Made Weight", min_value=0, max_value=100,  format="%d%%", key = 'GamesMadeWeight')
        st.caption(f"Weight: {'No Game Weight' if weight == 0 else 'All Games Weight' if weight == 100 else str(weight) + '%'}")

    with colb:
        
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

        if 'current_model' not in st.session_state:
            st.session_state.current_model = pd.DataFrame()

        st.write("### Current Settings")
        st.dataframe(weights_df)



        if st.button("Create New Model from weights:"):
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
            weights_list = list(weights.values())

            weights_list_official = weights_list[:-1]
            games_weight_value = weights_list[-1]


            weights_df.to_csv('../../data/currentweight/currentpointvalues.csv')

            train_base_data = pd.read_csv(f"../../data/seasonfullstatsreal/playerbasedatatotaltrain.csv")
            test_base_data = pd.read_csv(f"../../data/seasonfullstatsreal/playerbasedatatotaltest.csv")

            train_base_data = train_base_data.dropna(subset=["S_GamesPlayed_futureyear"])
            train_base_data = train_base_data.dropna(subset=['YearsExperience'])
            train_base_data = train_base_data.dropna(subset=['FirstSeasonYear'])
            train_base_data = train_base_data.dropna(subset=['Team'])
            train_base_data = train_base_data.dropna(subset=['PrimaryPosition'])
            train_base_data = train_base_data.dropna(subset=['Age'])

            test_base_data = test_base_data.dropna(subset=['YearsExperience'])
            test_base_data = test_base_data.dropna(subset=['FirstSeasonYear'])
            test_base_data = test_base_data.dropna(subset=['Team'])
            test_base_data = test_base_data.dropna(subset=['PrimaryPosition'])
            test_base_data = test_base_data.dropna(subset=['Age'])

            st.write(f"Games Weight: {games_weight_value}. weight list: {weights_list_official}")
            test = add_prediction_value(train_base_data, games_weight_value, weights_list_official)

            X = test[['Ht', 'Wt','S_TotalWins', 'S_GamesPlayed', 'S_AvgPoints',
                'S_AvgAssists', 'S_AvgRebounds', 'S_AvgSteals', 'S_AvgBlocks', 'S_AvgTurnovers', 'S_AvgFG', 'S_AvgFGA',
                'S_Avg3P', 'S_Avg3PA', 'S_AvgFT', 'S_AvgFTA', 'S_FantasyPoints', 'S_MinutesPlayed', 'S_GamePointDiff',
                'S_StartingCount', 'S_Top7Team', 'HS_TotalWins', 'HS_GamesPlayed',
                'HS_AvgPoints', 'HS_AvgAssists', 'HS_AvgRebounds', 'HS_AvgSteals', 'HS_AvgBlocks', 'HS_AvgTurnovers',
                'HS_AvgFG', 'HS_AvgFGA', 'HS_Avg3P', 'HS_Avg3PA', 'HS_AvgFT', 'HS_AvgFTA', 'HS_FantasyPoints',
                'HS_MinutesPlayed', 'HS_GamePointDiff', 'HS_StartingCount', 'HS_Top7Team', 'Age', 'NewPos1', 'NewPos2', 'NewPos3',
                'YearsExperience', 'S_TotalWins_prevyear', 'S_GamesPlayed_prevyear', 'S_AvgPoints_prevyear',
                'S_AvgAssists_prevyear', 'S_AvgRebounds_prevyear', 'S_AvgSteals_prevyear', 'S_AvgBlocks_prevyear',
                'S_AvgTurnovers_prevyear', 'S_AvgFG_prevyear', 'S_AvgFGA_prevyear', 'S_Avg3P_prevyear', 'S_Avg3PA_prevyear',
                'S_AvgFT_prevyear', 'S_AvgFTA_prevyear', 'S_FantasyPoints_prevyear', 'S_MinutesPlayed_prevyear',
                'S_GamePointDiff_prevyear', 'S_StartingCount_prevyear', 'S_Top7Team_prevyear', 'S_TotalWins_prev5years', 'S_GamesPlayed_prev5years', 'S_AvgPoints_prev5years', 'S_AvgAssists_prev5years',
                'S_AvgRebounds_prev5years', 'S_AvgSteals_prev5years', 'S_AvgBlocks_prev5years', 'S_AvgTurnovers_prev5years',
                'S_AvgFG_prev5years', 'S_AvgFGA_prev5years', 'S_Avg3P_prev5years', 'S_Avg3PA_prev5years', 'S_AvgFT_prev5years',
                'S_AvgFTA_prev5years', 'S_FantasyPoints_prev5years', 'S_MinutesPlayed_prev5years',
                'S_GamePointDiff_prev5years', 'S_StartingCount_prev5years', 'S_Top7Team_prev5years']]


            y = test['TargetVariable'].values



            all_features = X.columns

            cat_cols = ['NewPos1', 'NewPos2', 'NewPos3']


            num_cols = [col for col in all_features if col not in cat_cols]

            num_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='mean'))#,
                #('scaler', StandardScaler())
            ])


            cat_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', num_transformer, num_cols),
                    ('cat', cat_transformer, cat_cols)
                ])

            model = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('regressor', LinearRegression())
            ])

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            st.write(f"r^2 value: {r2_score(y_test, y_pred)}")

            test_base_data_copy = test_base_data.copy()
            test_base_data_predict = test_base_data[X.columns]
            new_predictions = model.predict(test_base_data_predict)


            results_df = test_base_data_copy[['Player']].copy()
            results_df['Predicted'] = new_predictions


            results_df1 = results_df.sort_values(by=['Predicted'], ascending = False)






            subset_test_base = test_base_data[['Player','PlayerID','S_GamesPlayed','TotalGamesSeason','S_FantasyPoints','S_AvgPoints','S_AvgAssists','S_AvgRebounds','S_AvgSteals','S_AvgBlocks','S_AvgTurnovers','S_Avg3P']]

            # Then, perform the merge
            results_df1 = results_df1.merge(
                subset_test_base,
                how='left',
                left_on='Player',
                right_on='Player'
            )

            st.session_state.current_model = results_df1


        if len(st.session_state.current_model) != 0:
            model_name = st.text_input("Enter Model Name")

            if st.button("Save Model"):
                if len(model_name) != 0:
                    st.session_state.current_model.to_csv(f'../../data/rankings/model_{model_name}.csv')
                    st.success("Successfully saved model to rankings.")
                else:
                    st.warning("Please enter a name for your model.")

        st.dataframe(st.session_state.current_model)

    

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






        weight_name = st.text_input('Name the weight')
        if st.button("💾 Save Weights to CSV"):
            save_path = os.path.join(weights_folder, f"weight_{weight_name}.csv")
            weights_df.to_csv(save_path, index=False)
            st.success(f"Weights saved to `{save_path}`")

    
    