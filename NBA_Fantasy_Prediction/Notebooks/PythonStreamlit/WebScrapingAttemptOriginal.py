from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidArgumentException
import time
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service as EdgeService
import xlwings as xw
import math 
# The new players on teams and breaks before I pick the players don't update


wb = xw.Book('NBA Fantasy Spreadsheet.xlsx')

sheet = wb.sheets['Template Possibility']

def generatePicksForPosition(position,numDrafted):
    round = math.ceil(numDrafted/8)
    picks = []
    for i in range(round-1):
        if i % 2 == 0:  #if in an odd round
            picks.append(((i+1)*8)-(8-position))
        if i % 2 != 0:  #if in an even round
            picks.append(((i+1)*8)-(position-1))
    if round % 2 != 0:  #if last round is odd
        if ((round*8)-(8-position)) <= numDrafted:
            picks.append((round*8)-(8-position))
    if round % 2 ==0:   #if last round is even
        if ((round*8)-(position-1)) <=  numDrafted:
            picks.append((round*8)-(position-1))
    
    return picks

def getListUpdatedPositions(numDrafted):

    round = math.ceil(numDrafted/8)
    #print(round)
    finallist = []
    for i in range(8):
        addition = generatePicksForPosition(i+1,numDrafted)
        for j in addition:
            finallist.append(j)
    
    return finallist


def scrape_draft_board_names(url):
    try:
        driver.refresh()
        drafted_players = driver.find_elements(By.CSS_SELECTOR, '.player-name')
        drafted_player_names = [player.text for player in drafted_players]
        
        return drafted_player_names
    except InvalidArgumentException as e:
        print("Invalid argument:", e)


def scrape_draft_board_teams(url):
    try:
        

        drafted_teams = driver.find_elements(By.CSS_SELECTOR, '.position')
        drafted_player_teams = [player.text for player in drafted_teams]
        
        return drafted_player_teams
    except InvalidArgumentException as e:
        print("Invalid argument:", e)

url = 'https://sleeper.com/draft/nba/1124180725475045377'

options = webdriver.EdgeOptions()
#options.add_argument('headless')
#options.add_argument('disable-gpu')
#options.add_argument('--no-sandbox')
#options.add_argument('--disable-dev-shm-usage')

# Initialize Edge WebDriver
driver_path = 'C:\\Users\\teska\\Downloads\\edgedriver_win64\\msedgedriver.exe'
edge_service = webdriver.edge.service.Service(executable_path=driver_path)
driver = webdriver.Edge(service=edge_service)
# Load the webpage
driver.get(url)

pastLength = 0


newTeamPlayers = 0

oldNumPersPlayers = 0

lastlist = []
iterations = 0

while True:
    
    starttime= time.time()
    list1 = scrape_draft_board_names(url)
    names = scrape_draft_board_teams(url)

    numofplayers = len(list1)
    ranks = getListUpdatedPositions(numofplayers)

    listoflists = []
    for i in range(len(list1)):
        newlist = []
        newlist.append(ranks[i])

        newlist.append(list1[i])
        newlist.append(names[i])
        listoflists.append(newlist)
    
    sortedList = sorted(listoflists, key=lambda x:x[0])

    fullnames = []
    #gotta change this next
    if len(list1) == len(names) == len(ranks):
        try:
            for i in range(len(sortedList)):
                fullnames.append(sortedList[i][1] + " -" + sortedList[i][2].split("-")[1])
        except:
            fullnames = fullnames

        numofplayers = len(fullnames)

        

        
        if numofplayers != pastLength:

            newtotplayers = numofplayers - pastLength
            pastLength = numofplayers
            indicies = generatePicksForPosition(2,numofplayers)
            personalTeam = []
            for i in indicies:
                personalTeam.append(fullnames[i-1])
            
            numTeamPlayers = len(personalTeam)
            newTeamPlayers = numTeamPlayers - oldNumPersPlayers
            oldNumPersPlayers = numTeamPlayers
            print("NEW NUMBER OF PLAYERS:", newtotplayers)
            print("-----------------")
            print("NEW PLAYERS ON MY TEAM:", newTeamPlayers)
            print("=-----------")
            
            for j in range(newtotplayers):
                cell = "CI" + str((numofplayers - newtotplayers)+j+1)
                sheet.range(cell).value = fullnames[(numofplayers - newtotplayers)+ j]
                print("Normal:",j, "--- Cell:",cell," ---Names",fullnames[(numofplayers - newtotplayers) + j])

            for i in range(newTeamPlayers):
                cell = "CJ" + str((numTeamPlayers - newTeamPlayers) + i + 1)
                sheet.range(cell).value = personalTeam[(numTeamPlayers - newTeamPlayers) + i]
                print("Personal:",i, "--- Cell:",cell," ---Names",personalTeam[(numTeamPlayers - newTeamPlayers) + i])

            print("TotalList:",fullnames)
            print("PersonalList:",personalTeam)
                
            print("TimePassed:",time.time() - starttime)
    lastlist = fullnames
    if (time.time() - starttime) < 1.5:
        time.sleep(1.5 - (time.time() - starttime))



# Example usage



driver.quit()






