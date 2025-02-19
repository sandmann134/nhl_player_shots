import os
import requests # type: ignore
import matplotlib.pyplot as plt # type: ignore
from scipy.stats import norm, poisson # type: ignore
import sqlite3
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
from team_avg_SA import get_opposition_factor
from config import DATABASE

# Define the base URL for the NHL API
base_url = "https://api-web.nhle.com/v1"
url2 = "https://statsapi.web.nhl.com/api/v1"
team_shots_url = "https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId=20242025%20and%20gameTypeId=2"


def plot_shots_histogram(shots, title, ylabel):
    plt.hist(shots, bins=range(min(shots), max(shots) + 2), edgecolor='black', align='left')
    plt.title(title)
    plt.xlabel('Shots per Game')
    plt.ylabel(ylabel)
    plt.show()

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=15))
def get_shots_per_game(player_id, season, cutoff_date):
    # Define the endpoint for player game logs for the current season
    season_url = f"{base_url}/player/{player_id}/game-log/{season}/2"

    response = requests.get(season_url)
    if response.status_code == 200:
        try:
            data = response.json()
            if data and 'gameLog' in data:
                cutoff_datetime = datetime.strptime(cutoff_date, '%Y-%m-%d')
                return [game['shots'] for game in data['gameLog'] if datetime.strptime(game['gameDate'], '%Y-%m-%d') < cutoff_datetime]
            else:
                print(f"No valid game log data available for player ID: {player_id} before date {cutoff_date} for season {season}.")
                return []
        except requests.exceptions.JSONDecodeError:
            print(f"Error decoding JSON from {season_url}")
            return []
    else:
        print(f"Request to {season_url} failed with status code {response.status_code}")
        return []

# Find player ID for player through team roster
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=15))
def get_player_id(team1, team2, player):
    team1_id = get_NHL_abbreviations(team1)
    team2_id = get_NHL_abbreviations(team2)
    
    # Function to search for player in a given team
    def search_player_in_team(team_id):
        response = requests.get(f"{base_url}/roster/{team_id}/current")
        if response.status_code == 200:
            try:
                data = response.json()
                for player_data in data.get('forwards', []):
                    full_name = f"{player_data.get('firstName', {}).get('default', '')} {player_data.get('lastName', {}).get('default', '')}"
                    if full_name.lower() == player.lower():
                        return player_data.get('id')
                for player_data in data.get('defensemen', []):
                    full_name = f"{player_data.get('firstName', {}).get('default', '')} {player_data.get('lastName', {}).get('default', '')}"
                    if full_name.lower() == player.lower():
                        return player_data.get('id')
                return None
            except requests.exceptions.JSONDecodeError:
                print(f"Error decoding JSON from {base_url}")
                return None
        else:
            print(f"Request to {base_url} failed with status code {response.status_code}")
            return None

    # Try to find the player in team1
    player_id = search_player_in_team(team1_id)
    if player_id:
        player_team = team1
        opposing_team = team2
        return player_id, player_team, opposing_team

    # If not found, try to find the player in team2
    player_id = search_player_in_team(team2_id)
    if player_id:
        player_team = team2
        opposing_team = team1
        return player_id, player_team, opposing_team
    
    # If player first name Nicholas, try Nick + last name instead (paul)
    if player.split()[0].lower() == 'nicholas':
        player = 'Nick ' + player.split()[1]
        player_id = search_player_in_team(team1_id)
        if player_id:
            player_team = team1
            opposing_team = team2
            return player_id, player_team, opposing_team
        player_id = search_player_in_team(team2_id)
        if player_id:
            player_team = team2
            opposing_team = team1
            return player_id, player_team, opposing_team
    
    # If player first name Alex (and not found already), try Alexander + last name instead (wennberg)
    if player.split()[0].lower() == 'alex':
        player = 'Alexander ' + player.split()[1]
        player_id = search_player_in_team(team1_id)
        if player_id:
            player_team = team1
            opposing_team = team2
            return player_id, player_team, opposing_team
        player_id = search_player_in_team(team2_id)
        if player_id:
            player_team = team2
            opposing_team = team1
            return player_id, player_team, opposing_team


    print(f"Player {player} not found in either team {team1} ({team1_id}) or team {team2} ({team2_id}) roster.")
    return None  
    
# Function to get player statistics from the NHL API
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=15))
def get_player_stats(url):
    response = requests.get(url)
    if response.status_code == 200:
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Error decoding JSON from {url}")
            return None
    else:
        print(f"Request to {url} failed with status code {response.status_code}")
        return None

# Function to calculate total games and shots
def calculate_totals(data):
    if data and 'gameLog' in data:
        game_logs = data['gameLog']
        total_games = len(game_logs)
        total_shots = sum(game['shots'] for game in game_logs)
        return total_games, total_shots
    else:
        print("No valid game log data available.")
        return 0, 0
    
# Function to extract career totals
def extract_career_totals(data):
    if data and 'careerTotals' in data and 'regularSeason' in data['careerTotals']:
        career_stats = data['careerTotals']['regularSeason']
        total_games = career_stats['gamesPlayed']
        total_shots = career_stats['shots']
        return total_games, total_shots
    else:
        print("No valid career statistics data available.")
        return 0, 0

# Extract the last 10 regular season games spanning multiple seasons
def get_last_10_games(data):
    if 'gameLog' in data:
        game_logs = data['gameLog']
        return game_logs[:10]
    return []

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=15))
def get_NHL_abbreviations(team_name):
    if team_name == 'St Louis Blues':
        team_name = 'St. Louis Blues'
    response = requests.get(f"{base_url}/standings/now")
    if response.status_code == 200:
        try:
            data = response.json()
            for team in data['standings']:
                if team['teamName']['default'] == team_name:
                    return team['teamAbbrev']['default']
            print(f"Team {team_name} not found in NHL teams.")
            return None
        except requests.exceptions.JSONDecodeError:
            print(f"Error decoding JSON from {base_url}/standings/now")
            return None
    else:
        print(f"Request to {base_url}/standings/now failed with status code {response.status_code}")
        return None

def calculate_likelihoods(shots, weighted_shots, over_under, shots_threshold, opposition_factor=1):
    # MODELLED LIKELIHOODS CALCULATED HERE FOR SPECIFIC WEIGHTINGS, WITH SEVERAL STATISTICAL MODELS
    # - (POISSON MOST VALID, OTHERS CALCULATED FOR REFERENCE)
    
    return normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood

def kelly_criterion(probability, odds):
    return probability - (1 - probability) / (odds - 1)

def fetch_and_store_player_data(x_10 = 5, x_2024 = 3, x_2023 = 2, x_2022 = 1, opposition_adjust = 0, sig_diff_adjust = 0):
    # WEIGHTING INFORMATION REDACTED FROM HERE

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Connect to the SQLite database
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()

    cursor.execute(f"""
    SELECT DISTINCT pso.player_name, pso.over_under, pso.home_team, pso.away_team, pso.date 
    FROM player_shots_odds pso
    LEFT JOIN {model_table} ml
    ON pso.player_name = ml.player_name AND pso.over_under = ml.over_under AND pso.date = ml.date AND pso.points = ml.points
    WHERE ml.player_name IS NULL 
    AND pso.date > (SELECT COALESCE(MAX(date), '1900-01-01') FROM {ledger})
    """)
    players = cursor.fetchall()
    print(f"Found {len(players)} players to model.")

    for player_name, over_under, home_team, away_team, date in players:
        # STATISTICAL modelling done here from past SOG data & chosen model structure - details kept private
        # - from here, the modelled likelihood for each over/under is calculated, 
        # - modelling likelihood is then compared to the betting odds
        # - bets with a expected edge are printed to output file, with suggested bet size based on bankroll and size of expected edge


    conn.commit()
    conn.close()

if __name__ == "__main__":
    #print(get_shots_per_game(8478483, '20242025', '2024-10-13'))
    fetch_and_store_player_data()
