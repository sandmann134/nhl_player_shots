import os
import requests # type: ignore
import matplotlib.pyplot as plt # type: ignore
from scipy.stats import norm, poisson # type: ignore
import sqlite3
from datetime import datetime
from config import DATABASE

# Define the base URL for the NHL API
base_url = "https://api-web.nhle.com/v1"
url2 = "https://statsapi.web.nhl.com/api/v1"

# Define the player ID for Mitch Marner
# player_id = 8478483
# team = 'TOR'
# player = 'Mitch Marner'

# Define the weights for the seasons
x_10 = 5
x_2024 = 3
x_2023 = 2
x_2022 = 1

def plot_shots_histogram(shots, title, ylabel):
    plt.hist(shots, bins=range(min(shots), max(shots) + 2), edgecolor='black', align='left')
    plt.title(title)
    plt.xlabel('Shots per Game')
    plt.ylabel(ylabel)
    plt.show()

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
        return player_id

    # If not found, try to find the player in team2
    player_id = search_player_in_team(team2_id)
    if player_id:
        return player_id

    print(f"Player {player} not found in either team {team1} ({team1_id}) or team {team2} ({team2_id}) roster.")
    return None  
    
# Function to get player statistics from the NHL API
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

def calculate_likelihoods(shots, weighted_shots, over_under, shots_threshold):
    mean_weighted_shots = sum(weighted_shots) / len(weighted_shots)
    std_dev_weighted_shots = (sum((shots - mean_weighted_shots) ** 2 for shots in weighted_shots) / len(weighted_shots)) ** 0.5
    z = (shots_threshold - mean_weighted_shots) / std_dev_weighted_shots
    if over_under == 'Over' or over_under == 'over':
        normal_likelihood = (1 - norm.cdf(z))
        poisson_likelihood = (1 - poisson.cdf(shots_threshold, mean_weighted_shots))
        raw_data_likelihood = (sum(1 for shots in shots if shots > shots_threshold) / len(shots))
        weighted_likelihood = (sum(1 for shots in weighted_shots if shots > shots_threshold) / len(weighted_shots))
    elif over_under == 'under' or over_under == 'Under':
        normal_likelihood = norm.cdf(z)
        poisson_likelihood = poisson.cdf(shots_threshold, mean_weighted_shots)
        raw_data_likelihood = (sum(1 for shots in shots if shots < shots_threshold) / len(shots))
        weighted_likelihood = (sum(1 for shots in weighted_shots if shots < shots_threshold) / len(weighted_shots))
    else:
        raise ValueError("Invalid value for over_under. Expected 'Over' or 'Under'.")
    
    return normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood

def kelly_criterion(probability, odds):
    return probability - (1 - probability) / (odds - 1)

def fetch_and_store_player_data():
    # Connect to the SQLite database

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT pso.player_name, pso.over_under, pso.home_team, pso.away_team, pso.date 
    FROM player_shots_odds pso
    LEFT JOIN modelled_likelihoods ml
    ON pso.player_name = ml.player_name AND pso.over_under = ml.over_under AND pso.date = ml.date AND pso.points = ml.points
    WHERE ml.player_name IS NULL
    """)
    players = cursor.fetchall()

    for player_name, over_under, home_team, away_team, date in players:
        player_id = get_player_id(home_team, away_team, player_name)
        if player_id:
            shots = []
            weighted_shots = []

            # Get season shots
            current_season_shots = get_shots_per_game(player_id, '20242025', date)
            last_season_shots = get_shots_per_game(player_id, '20232024', date)
            twothree_season_shots = get_shots_per_game(player_id, '20222023', date)

            # Add shots to the shots log
            shots.extend(current_season_shots)
            shots.extend(last_season_shots)
            shots.extend(twothree_season_shots)

            # Check if the player has played more than 60 games
            total_games = len(current_season_shots) + len(last_season_shots) + len(twothree_season_shots)
            if total_games < 60:
                print(f"{player_name} has less than 60 GP.")
                continue

            # Add weighted shots for the most recent 10 games
            if len(current_season_shots) > 10:
                weighted_shots.extend(current_season_shots[:10] * x_10)
                weighted_shots.extend(current_season_shots[10:] * x_2024)
            else:
                weighted_shots.extend(current_season_shots * x_10)
                if len(current_season_shots) + len(last_season_shots) > 10:
                    weighted_shots.extend(last_season_shots[:10 - len(current_season_shots)] * x_10)
                    weighted_shots.extend(last_season_shots[10 - len(current_season_shots):] * x_2024)
                else:
                    weighted_shots.extend(last_season_shots * x_2024)

            # Add weighted shots for the previous seasons
            weighted_shots.extend(last_season_shots * x_2023)
            weighted_shots.extend(twothree_season_shots * x_2022)

            cursor.execute("""
            SELECT date, over_under, points, MAX(price) as price 
            FROM player_shots_odds 
            WHERE player_name = ? 
            GROUP BY date, over_under, points
            """, (player_name,))
            odds_data = cursor.fetchall()

            for date_b, over_under, points, price in odds_data:
                # Check if the modelled likelihoods for this date and player_name already exist
                cursor.execute("SELECT 1 FROM modelled_likelihoods WHERE date = ? AND player_name = ? AND over_under = ?", (date_b, player_name, over_under))
                if cursor.fetchone() is None and date_b == date:
                    normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood = calculate_likelihoods(shots, weighted_shots, over_under, points)
                    implied_likelihood = 1/price
                    poisson_kelly = kelly_criterion(poisson_likelihood, price) / 3

                    cursor.execute('''
                    INSERT INTO modelled_likelihoods (player_name, date, over_under, points, implied_likelihood, normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood, poisson_kelly)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (player_name, date, over_under, points, implied_likelihood, normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood, poisson_kelly))
                    if poisson_kelly > 0:
                        print(f"Player: {player_name}, date: {date}, {over_under} {points}, Price: {price}, Kelly Bet: {poisson_kelly*100:.2f}%")


    conn.commit()
    conn.close()

if __name__ == "__main__":
    #print(get_shots_per_game(8478483, '20242025', '2024-10-13'))
    fetch_and_store_player_data()