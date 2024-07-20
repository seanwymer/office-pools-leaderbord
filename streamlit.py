import streamlit as st
import subprocess
import sys
import time

# Check if the BeautifulSoup4 package is installed
try:
    from bs4 import BeautifulSoup
except ImportError:
    # Install the package if not present
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

import requests
import pandas as pd
import time

# Function to safely convert scores
def convert_score(score):
    if score == 'E':
        return 0
    try:
        return int(score)
    except ValueError:
        return float('inf')  # Use a high value to push invalid scores to the end

# Function to scrape the leaderboard data
def scrape_leaderboard():
    url = 'https://www.easyofficepools.com/leaderboard/?p=349290&scoring=To%20Par'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize lists to store data
    teams = []

    # Find all team containers
    team_containers = soup.find_all('tbody', class_='searchable')

    for team in team_containers:
        # Extract team name
        team_name_tag = team.find('td', class_='teamName').find('span')
        team_name = team_name_tag.get('ng-click').split("'")[1]

        # Extract team score
        team_score_tag = team.find('td', class_='teamName').find_next_sibling('td')
        team_score = team_score_tag.text.strip()
        team_score = convert_score(team_score)

        # Extract player details
        players = []
        player_rows = team.find_all('tr', class_='details')
        for player in player_rows:
            player_data = player.find_all('td')
            player_name = player_data[2].text.strip()
            player_score = player_data[3].text.strip()
            player_score = convert_score(player_score)
            players.append({
                'Player Name': player_name,
                'Player Score': player_score
            })

        # Append to the teams list
        teams.append({
            'Team Name': team_name,
            'Team Score': team_score,
            'Players': players
        })

    # Sort by team_score and get top 10
    teams = sorted(teams, key=lambda x: x['Team Score'])[:10]
    return teams

# Main app
st.title('Golf Leaderboard Notifier')

# Function to refresh the page every 10 seconds
def refresh():
    with st.spinner('Wait for it...'):
        time.sleep(10)
        st.title('Test app')
        st.write('1')
        st.write('2')
        st.success('Done!')

teams = scrape_leaderboard()

# Display each team's information
for i, team in enumerate(teams):
    st.subheader(f"Team {i + 1}: {team['Team Name']} - Score: {team['Team Score']}")
    players_df = pd.DataFrame(team['Players'])
    st.dataframe(players_df)
