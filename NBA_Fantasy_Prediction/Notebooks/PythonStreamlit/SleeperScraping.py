from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidArgumentException
import time
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
import xlwings as xw
import math 
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService

# The new players on teams and breaks before I pick the players don't update


def scrape_draft_board_names(url):
    try:
        driver.refresh()
        drafted_players = driver.find_elements(By.CSS_SELECTOR, '.player-name')
        drafted_player_names = [player.text for player in drafted_players]
        
        return drafted_player_names
    except InvalidArgumentException as e:
        print("Invalid argument:", e)


url = 'https://sleeper.com/draft/nba/1223814632272052225'

options = webdriver.EdgeOptions()
options.add_argument('--headless=new')
#options.add_argument('disable-gpu')
#options.add_argument('--no-sandbox')
#options.add_argument('--disable-dev-shm-usage')

# Initialize Edge WebDriver
edge_service = EdgeService(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=edge_service)
# Load the webpage
driver.get(url)

pastLength = 0


newTeamPlayers = 0

oldNumPersPlayers = 0

lastlist = []
iterations = 0

while True:
    
    time.sleep(5)
    print(scrape_draft_board_names(url))




# Example usage



driver.quit()






