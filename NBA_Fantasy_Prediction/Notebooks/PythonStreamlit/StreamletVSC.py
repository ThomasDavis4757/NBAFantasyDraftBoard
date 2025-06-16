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

#print(streamlit_sortables.__version__)



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
if 'last_scraped_positions' not in st.session_state:
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




    uploaded_data = pd.read_csv('../../data/sleeperapidata/updatedsleeperapidata1.csv')
    multi_weights = pd.read_csv('../../data/currentweight/currentpointvalues.csv')

    reference_names = uploaded_data['full_name'].dropna().unique().tolist()
    folder_path = '../../data/current_ranking'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if csv_files:
        csv_path = os.path.join(folder_path, csv_files[0])
        rankingmodel = pd.read_csv(csv_path)
        def get_best_match(name, reference_list, threshold=25):
            match = process.extractOne(name, reference_list, scorer=fuzz.token_sort_ratio)
            if match and match[1] >= threshold:
                return match[0]
            return None 
        rankingmodel['Player'] = rankingmodel['Player'].apply(lambda name: get_best_match(name, reference_names))
        current_ranking_name = os.path.splitext(csv_files[0])[0]
        #print(f"Loaded: {csv_files[0]}")
    else:
        print("No CSV files found.")
        
        



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



    def get_draft_picks_list(draft_participants, rounds, picking_pos):
        list_of_positions = []
        for i in range(int(rounds)):
            if (i+1) % 2 != 0:
                list_of_positions.append(str(i+1) + "." + str(picking_pos))
            else:
                list_of_positions.append(str(i+1) + "." + str(draft_participants - (picking_pos - 1)))
        return list_of_positions



    num_drafting_participants = 0
    num_drafting_rounds = 0

    with col_sidebar:
        st.markdown("### 🛠️ Controls")

        draft_link = st.text_input("Enter Draft link:")

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

        if start_browser and num_drafting_participants == 0:
            num_drafting_participants = len(st.session_state.driver.find_elements(By.CSS_SELECTOR, '.team-column'))

        if start_browser and num_drafting_rounds == 0:
            num_drafting_rounds = len(st.session_state.driver.find_elements(By.CSS_SELECTOR, '.cell-container')) / num_drafting_participants


        if num_drafting_participants == 0:
            pass
        else:
            draft_picking_position = st.number_input("Draft Picking Position", min_value=1, max_value=int(num_drafting_participants), value=1, step=1)
            draft_picks = get_draft_picks_list(num_drafting_participants, num_drafting_rounds, draft_picking_position)



        if st.button("Scrape Now"):
            if st.session_state.driver_active and st.session_state.driver:
                try:
                    st.session_state.driver.refresh()

                    drafted_cells = st.session_state.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'cell') and contains(@class, 'drafted')]"
                    )
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

        st.write(num_drafting_participants)
        st.write(num_drafting_rounds)

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


    with col_main:

        def format_name(full_name):
            parts = full_name.split()
            if len(parts) >= 2:
                return f"{parts[0][0].upper()}. {parts[-1]}"
            else:
                return full_name  # fallback if name is malformed
            

        def highlight_row(row):
            formatted_name = format_name(row["Player"])
            player_team_key = f"{formatted_name} - {row['team']}"
            
            if player_team_key in highlighted_names:
                return ['background-color: lightgreen; font-weight: bold'] * len(row)
            return [''] * len(row)
        
        indicies = [i for i, val in enumerate(st.session_state.last_scraped_draft_locations) if val in draft_picks]
        st.write(indicies)

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

        highlighted_names = [
            f"{name} - {position.split(' - ')[1]}"
            for name, position in zip(st.session_state.last_scraped_data, st.session_state.last_scraped_positions)
        ]


        col_all_players, col_position_players = st.columns([3,2])
        #The column that will hold the total player ranking, and be filled out.
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
                
                
            specific_display = displayed_df.copy()
            specific_display.index = specific_display.index + 1
            specific_display['MeetPositionalRequirement'] = specific_display['fantasy_positions'].apply(ast.literal_eval).apply(lambda player_positions: mark_as_good(player_positions, positions_equation, positions)) 
            specific_display = specific_display[specific_display['MeetPositionalRequirement'] == True]
            specific_display = specific_display.drop('MeetPositionalRequirement', axis=1)


            styled_df = specific_display.style.apply(highlight_row, axis=1)

            st.dataframe(styled_df, use_container_width=True)

        st.write("🔍 Scraped Players:", st.session_state.last_scraped_data)
        st.write("🔍 Scraped Positions:", st.session_state.last_scraped_positions)
        st.write("Scraped Draft Numbers:", st.session_state.last_scraped_draft_locations)
        st.write("Highlighted Entries", highlighted_names)



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


    with col_maintab3:


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
        for i, player in enumerate(sorted_items, start=1):
            st.write(f"{i}. {player}")



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
            preset_ranking_df.to_csv(f'../../data/current_ranking/{ranking_preset}')
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

    
    