import streamlit as st
import subprocess
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import pytz

# Ensure that beautifulsoup4 is installed
try:
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4"])
    from bs4 import BeautifulSoup

# Function to safely convert scores
def convert_score(score):
    if score == 'E':
        return 0
    try:
        return int(score)
    except ValueError:
        return float('inf')  # Use a high value to push invalid scores to the end

# Function to scrape the leaderboard data
@st.cache_data(ttl=10)
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
                'Player Score': player_score,
                'Highlight': ''  # Initialize the Highlight field
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

# Function to highlight score changes
def highlight_changes(players, previous_scores):
    for player in players:
        current_score = player['Player Score']
        prev_score = previous_scores.get(player['Player Name'])

        if prev_score is not None:
            if current_score < prev_score:
                player['Highlight'] = 'green'  # Highlight green
            elif current_score > prev_score:
                player['Highlight'] = 'red'  # Highlight red
            else:
                player['Highlight'] = ''  # No highlight
        else:
            player['Highlight'] = ''  # No highlight

        previous_scores[player['Player Name']] = current_score

    return players, previous_scores

# Function to apply styles based on the highlight
def apply_styles(df):
    def highlight_cell(row):
        if row['Highlight'] == 'green':
            return ['background-color: lightgreen'] * len(row)
        elif row['Highlight'] == 'red':
            return ['background-color: lightcoral'] * len(row)
        else:
            return [''] * len(row)
    return df.style.apply(highlight_cell, axis=1)

# Function to find new teams in the top 10
def find_new_top_10_teams(current_teams, previous_teams):
    current_team_names = {team['Team Name'] for team in current_teams}
    previous_team_names = {team['Team Name'] for team in previous_teams}
    new_teams = current_team_names - previous_team_names
    return new_teams

# Main app
st.title('Golf Leaderboard Notifier')

# Get the current time in CST
cst = pytz.timezone('America/Chicago')
now = datetime.now(cst)

# Only run the script if it is between 6am and 3pm CST
if 6 <= now.hour < 15:
    # Initialize session state for previous top 10 teams and scores
    if 'previous_top_10_teams' not in st.session_state:
        st.session_state.previous_top_10_teams = []
    if 'previous_scores' not in st.session_state:
        st.session_state.previous_scores = {}

    # Scrape the leaderboard data with a custom spinner message
    with st.spinner('Updating leaderboard...'):
        current_teams = scrape_leaderboard()

    # Find new teams in the top 10
    new_teams = find_new_top_10_teams(current_teams, st.session_state.previous_top_10_teams)

    # Display notification if there are new teams in the top 10
    if new_teams:
        st.write("### <span style='color:green;'>New teams entered the top 10:</span>", unsafe_allow_html=True)
        for team in new_teams:
            st.write(f"**<span style='color:green;'>{team}</span>** has entered the top 10!", unsafe_allow_html=True)

    # Update the previous top 10 teams in the session state
    st.session_state.previous_top_10_teams = current_teams

    # Display each team's information and highlight changes
    should_update = False
    for i, team in enumerate(current_teams):
        st.subheader(f"Team {i + 1}: {team['Team Name']} - Score: {team['Team Score']}")
        players, st.session_state.previous_scores = highlight_changes(team['Players'], st.session_state.previous_scores)
        players_df = pd.DataFrame(players)
        
        # Apply styles based on score changes
        styled_df = apply_styles(players_df)
        
        # Check if there are any changes in the scores
        for player in players:
            if player['Highlight']:
                should_update = True
        
        st.dataframe(styled_df)

    # Auto refresh the page every 10 seconds
    st.experimental_set_query_params(refresh=time.time())
    time.sleep(10)
    st.experimental_rerun()
else:
    st.write("The leaderboard updates are only available between 6am and 3pm CST.")

    # Scrape the leaderboard data with a custom spinner message
    with st.spinner('Updating leaderboard...'):
        current_teams = scrape_leaderboard()

    # Display each team's information without highlighting changes
    for i, team in enumerate(current_teams):
        st.subheader(f"Team {i + 1}: {team['Team Name']} - Score: {team['Team Score']}")
        players_df = pd.DataFrame(team['Players'])
        
        # Apply styles based on score changes
        styled_df = apply_styles(players_df)
        
        st.dataframe(styled_df)

