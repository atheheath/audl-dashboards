"""
Created by: Joseph Wylie
Name: GetAUDLStats
Description: Pull urls that store game data for AUDL games and store them in database for furture use
Date Created: 6/29/2021
"""

from concurrent import futures
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import datetime
import time

currentDate = datetime.now()

urls = []
teams = []

""" 
2021 AUDL Teams:
hustle
sol
glory
union
roughnecks
breeze
mechanix
alleycats
aviators
radicals
windchill
royal
empire
outlaws
phoenix
thunderbirds
flyers
growlers
spiders
cascades
cannons
rush
"""

#AUDL teams url
teamsURL = 'https://theaudl.com/league/teams'

#Base url used to create full link to stats
statspage = 'https://audl-stat-server.herokuapp.com/stats-pages/'


def getTeams():
    #Request the AUDL schedule site to get the rest of the URL information needed for the full stats page
    teamsite = requests.get(teamsURL)

    #Create a soup object
    soup = BeautifulSoup(teamsite.content, 'html.parser')

    #Find the table of teams
    table = soup.find('table',class_='league-team-table-pg')

    #Find each teams table entry and store in list
    teamscard = table.find_all('div',style='text-align:center')

    #For each team in the league find the teams identifier and store in list
    for team in teamscard:
        teamname = team.find(href=True)['href'][1:]
        teams.append(teamname)

    return teams

def getStats(teams):
    #AUDL schedule url
    AUDLSchedule = f'https://theaudl.com/{teams}/schedule'

    #Request the AUDL schedule site to get the rest of the URL information needed for the full stats page
    site = requests.get(AUDLSchedule)

    #Create a soup object
    soup = BeautifulSoup(site.content, 'html.parser')

    #Find the div used to house the game data for every game on schedule
    schedule = soup.find('div',class_='view-content')

    #Find game data for each game and store in list
    games = schedule.find_all('div', attrs={'class': re.compile('^views-row views-row.*')})

    #For each game on the schedule find the unique identifier for each specific games full stats page
    for game in games:
        #Find the span where the unique identifier is located
        link_desc = game.find('span',class_='audl-schedule-gc-link')

        #Find the name of the href
        hreftag = link_desc.find(href=True)['href']

        #Parse the name and store the unique identifier
        hrefsplit = hreftag.split('/')

        #Reformat the data of the game into a usable formate
        datesplit = hrefsplit[3].split('-')[0:3]
        date = datesplit[0]+'/'+datesplit[1]+'/'+datesplit[2]

        #Store the game date in a usable formate
        gameDate = datetime.strptime(date,'%Y/%m/%d')

        #Compate the game date with today's date and ignore if the game has not happened yet
        if gameDate<currentDate:
            #Finalize the format for unique identifier
            directory = hrefsplit[2]+'/'+hrefsplit[3]

            #Concatenate the unique identifier to the end of the base url and append to a list
            urls.append(statspage+directory)

    return urls


def get_audl_stat_urls():
    #Find all current AUDL teams
    AUDLteams = getTeams()

    #Find the stats for every game that each AUDL team has played
    start_time = time.time()

    # final_url_list = set()
    # for team in AUDLteams:
    #     url_list = getStats(team)
    #     for url in url_list:
    #         final_url_list.add(url)

    result_futures = []
    with futures.ThreadPoolExecutor(8) as ex:
        for team in AUDLteams:
            result_futures.append(ex.submit(getStats, team))

        final_url_list = set()
        for url_list_future in futures.as_completed(result_futures):
            url_list = url_list_future.result()
            for url in url_list:
                final_url_list.add(url)

    end_time = time.time()
    print(f"total time taken: {end_time - start_time}")
    return final_url_list


def main():
    game_urls = get_audl_stat_urls()
    
    df = pd.DataFrame({'Team Stat urls': game_urls})

    # Write the urls to a csv file
    df.to_csv('GameStats.csv', index=False)


if __name__ == "__main__":
    main()
