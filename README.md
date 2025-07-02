# NBAFantasyDraftBoard

<<<<<<< HEAD
Hello Testing
=======
This application is a hub where you can create player rankings, and practice drafting with many tools to assist you!
It is ran in a virtual enviroment, and there is a requirements file that should have all of the libraries needed to run. 

These are the 4 tabs in the app, and this will go through what each one does.

### Tab 1 - Real Draftboard
This tab is where you can connect an actual NBA fantasy draft from the fantasy website "Sleeper", and see live updates from the draft on your application.
You can keep track of what players have been drafted, who is on your team, and search through players by their position. It lets you be able to control what you know about the draft, and be able to keep track of everything going on. 
 - When you put in an working draft link, it will get most of the data from the draft and update it in the app to get the number of draft participants and rounds.
 - You can put in if you have any picks traded away or gained.
 - Selenium is doing the webscraping, and it will open up a seperate tab with the draft in it. You can update from the live draft by clicking "Scrape Now"

Important things to note
  - The official ranking will sometimes not updated if it has been updated in another tab, and might require a refresh for everything to load officially.

### Tab 2 - Mock Draftboard
This is where you can practice drafting easily if you do not want to connect to sleeper. It is the same idea and functionality as the real draftboard, but it "simulates" the draft by taking players off of your personal ranking you are using, so you can really practice the worse case scenarios.
  - On the side tab, you put in all of the draft specifications for what it will look like and what position you will be drafting at, in a similar way to the Real Draftboard.

Important things to note:
  - The buttons to select your pick/keep the draft moving could be optimized a little better for clarity. For instance, if you have the first overall pick, you would have to click start draft first and then select your pick.
  - There is currently no way to load a draft preset into the mock draftboard, it would have to be made each time.
  - There is currently no way to save a draft and the team that you have.
  - To update what ranking is in this page, you might need to refresh.

### Tab 3 - PlayerRankings
Here is where you can create and edit your own player rankings. You can save and load multiple rankings and make them be used across the entire app. You have the ability to pull up a ranking on the side to compare your current one to, and also a toggable section where you can compare player statistics. You can also update the sleeper fantasy statistics here in this tab, to make sure everything is up to date. (There is a 24 hour cooldown on this, because sleeper asks that this API call is not done too much.)

Important things to note:
  - When saving rankings, if you want to see them in another drop down or as an option - currently you have to refresh to see it pop up.

### Tab 4 - Model Changing
This is where you can put in the specific weights that each statistic holds when calculating fantasy values. With doing this, you can save them and load them up for different situations. When you load them, they will be implemented into all facets of the app whenever they are set as the current weights (This is when calculating previous fantasy values.) With these weights, you can also create a model which will predict which players will do the best in the upcoming year. You can save this as a ranking, and make changes off of it and use it to create your own personalized ranking.

Important things to note:
  - With the weights being saved AND the models, for them to show up as options in other tabs in dropdowns, the app will have to be refreshed.
  - In sleeper, calculating fantasy points takes a few extra statistics that are not listed in the model weights. There is a chance that you might not be able to exactly get the right weights for your league with that being the case.
  - The model R^2 value can change a decent amount depending on what the weights look like.
    
>>>>>>> ba8aac55954ccf4f1d9a5159b47c69cfbec904d9
