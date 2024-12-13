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


# Define the player ID for Mitch Marner
# player_id = 8478483
# team = 'TOR'
# player = 'Mitch Marner'

# Define the weights for the seasons


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
    mean_weighted_shots = float(opposition_factor) * sum(weighted_shots) / float(len(weighted_shots))
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

def fetch_and_store_player_data(x_10 = 5, x_2024 = 3, x_2023 = 2, x_2022 = 1, opposition_adjust = 0, sig_diff_adjust = 0):
    print(f"Fetching and storing player data with weights: x_10 = {x_10}, x_2024 = {x_2024}, x_2023 = {x_2023}, x_2022 = {x_2022}")

    if x_2024 == 3 and x_2023 == 2 and x_2022 == 1:
        if opposition_adjust != 0 and sig_diff_adjust == 0:
            if x_10 == 5:
                ledger = 'daily_ledger_scaled_wOppositionFactor'
                model_table = 'modelled_likelihoods_wOppositionFactor'
            elif opposition_adjust == 1:
                ledger = 'daily_ledger_scaled_weight' + str(x_10) + '_wOppositionFactor'
                model_table = 'modelled_likelihoods_weight' + str(x_10) + '_wOppositionFactor'
            elif opposition_adjust == 0.5:
                ledger = 'daily_ledger_scaled_weight' + str(x_10) + '_wHalfOppositionFactor'
                model_table = 'modelled_likelihoods_weight' + str(x_10) + '_wHalfOppositionFactor'
            elif opposition_adjust == 0.25:
                ledger = 'daily_ledger_scaled_weight' + str(x_10) + '_wQuarterOppositionFactor'
                model_table = 'modelled_likelihoods_weight' + str(x_10) + '_wQuarterOppositionFactor'
            elif opposition_adjust == 0.1:
                ledger = 'daily_ledger_scaled_weight' + str(x_10) + '_tenthOppositionFactor'
                model_table = 'modelled_likelihoods_weight' + str(x_10) + '_tenthOppositionFactor'
            elif opposition_adjust == 0.05:
                ledger = 'daily_ledger_scaled_weight' + str(x_10) + '_twentiethOppositionFactor'
                model_table = 'modelled_likelihoods_weight' + str(x_10) + '_twentiethOppositionFactor'
        elif x_10 == 5 and sig_diff_adjust == 0:
            ledger = 'daily_ledger_scaled'
            model_table = 'modelled_likelihoods'
        elif sig_diff_adjust == 0:
            ledger = 'daily_ledger_scaled_weight' + str(x_10)
            model_table = 'modelled_likelihoods_weight' + str(x_10)
        elif opposition_adjust== 0.1 and sig_diff_adjust == 1:
            ledger = 'daily_ledger_scaled_weight' + str(x_10) + 'tenthOppositionFactor' + '_sigDiff2'   #sigDiff for +2
            model_table = 'modelled_likelihoods_weight' + str(x_10) + 'tenthOppositionFactor' + '_sigDiff2'  #sigDiff for +2
    elif x_2024 == 1 and x_2023 == 1:
        if x_10 == 1 and x_2022 == 0:
            ledger = 'daily_ledger_scaled_2324flat'
            model_table = 'modelled_likelihoods_2324flat'
        elif x_10 == 3 and x_2022 == 0:
            ledger = 'daily_ledger_scaled_2324flat_x10_3'
            model_table = 'modelled_likelihoods_2324flat_x10_3'
        elif x_10 == 3 and x_2022 == 1:
            ledger = 'daily_ledger_scaled_222324flat_x10_3'
            model_table = 'modelled_likelihoods_222324flat_x10_3' 

    else:
        if x_10 == 4 and x_2024 != 3:
            ledger = f'daily_ledger_scaled_weight4_x24_{str(x_2024)}'
            model_table = f'modelled_likelihoods_weight4_x24_{str(x_2024)}'
        else:
            print("Invalid weights for model table - write more options .")
            return
    
    print(f"Using ledger: {ledger}, model table: {model_table}")

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
        player_info = get_player_id(home_team, away_team, player_name)
        if player_info is None:
            continue
        player_id = player_info[0]
        opposing_team = player_info[2]
        opposing_team = get_player_id(home_team, away_team, player_name)[2]
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

            # if sig_diff_adjust == 1, compare to see if this season is significantly different past
            adjusted = 0    # boolean for if coefficients need resetting
            x_10_inc = 2    # increment for x_10 if sig_diff_adjust == 1
            x_2024_inc = 1  # increment for x_2024 if sig_diff_adjust == 1
            if sig_diff_adjust == 1 and len(current_season_shots) > 9:
                pre_thisseason = last_season_shots + twothree_season_shots

                # Calculate the mean of the two samples
                mean_current = sum(current_season_shots) / len(current_season_shots)
                mean_pre_thisseason = sum(pre_thisseason) / len(pre_thisseason)

                # Calculate the lambda (rate) for the Poisson distributions
                lambda_current = mean_current
                lambda_pre_thisseason = mean_pre_thisseason
                combined_rate = (sum(current_season_shots) + sum(pre_thisseason)) / (len(current_season_shots) + len(pre_thisseason))

                # Perform a two-sample Poisson test
                # Calculate the p-value
                #p_value = poisson.cdf(sum(current_season_shots), lambda_pre_thisseason * len(current_season_shots))
                z_stat = (mean_current - mean_pre_thisseason) / (combined_rate * (1 / len(current_season_shots) + 1 / len(pre_thisseason))) ** 0.5
                p_value = (1 - norm.cdf(z_stat))

                # Determine if the p-value is less than the significance level (e.g., 0.05)
                significance_level = 0.05
                if p_value < significance_level:
                    x_10 = x_10 + x_10_inc
                    x_2024 = x_2024 + x_2024_inc
                    adjusted = 1
                    print(f"Player: {player_name} has significantly different shots this season (this year mean: {mean_current:.3f}, gp: {len(current_season_shots)} vs. mean pre: {mean_pre_thisseason:.3f}, gp: {len(pre_thisseason)}). Adjusting weights to x_10 = {x_10}, x_2024 = {x_2024}.")

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

            # if adjusted, reset coefficients:
            if adjusted == 1:
                x_10 -= x_10_inc
                x_2024 -= x_2024_inc

            cursor.execute("""
            SELECT date, over_under, points, MAX(price) as price 
            FROM player_shots_odds 
            WHERE player_name = ? 
            GROUP BY date, over_under, points
            """, (player_name,))
            odds_data = cursor.fetchall()

            print_bool = 0      # if 1, print suggested bets to console
            for date_b, over_under, points, price in odds_data:
                # Check if the modelled likelihoods for this date and player_name already exist
                cursor.execute(f"SELECT 1 FROM {model_table} WHERE date = ? AND player_name = ? AND over_under = ? AND points = ?", (date_b, player_name, over_under, points))
                if cursor.fetchone() is None and date_b == date:
                    if opposition_adjust != 0:
                        opposition_factor = get_opposition_factor(date, opposing_team, opposition_adjust)
                    else:
                        opposition_factor = 1
                    normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood = calculate_likelihoods(shots, weighted_shots, over_under, points, opposition_factor)
                    implied_likelihood = 1/price
                    poisson_kelly = kelly_criterion(poisson_likelihood, price) / 4

                    if poisson_kelly > 0.01:        #output histogram and statistical comparison of this season to previous ones
                        print(f"Player: {player_name}, date: {date}, {over_under} {points}, Price: {price}, Kelly Bet: {poisson_kelly*100:.2f}%")
                        pre_thisseason = last_season_shots + twothree_season_shots
                        # Calculate the mean & variance of the two samples
                        cur_mean = sum(current_season_shots) / len(current_season_shots)
                        cur_var = sum([(x - sum(current_season_shots) / len(current_season_shots))**2 for x in current_season_shots]) / len(current_season_shots)
                        past_mean = sum(pre_thisseason) / len(pre_thisseason)
                        past_lambda = past_mean
                        past_var = sum([(x - sum(pre_thisseason) / len(pre_thisseason))**2 for x in pre_thisseason]) / len(pre_thisseason)
                        combined_rate = (sum(current_season_shots) + sum(pre_thisseason)) / (len(current_season_shots) + len(pre_thisseason))

                        # Perform a rate-comparison test
                        z_stat = abs((cur_mean - past_mean)) / (combined_rate * (1 / len(current_season_shots) + 1 / len(pre_thisseason))) ** 0.5
                        p_value = (1 - norm.cdf(z_stat))*2

                        # Calculate the p-value
                        #p_value = poisson.cdf(sum(current_season_shots), past_lambda * len(current_season_shots))

                        # Determine if the p-value is less than the significance level (e.g., 0.05)
                        significance_level = 0.05
                        if p_value < significance_level:
                            diff_text = f'24/25 sig. diff. from prev. szns (p={p_value:.3f})'
                        else:
                            diff_text = f'24/25 not sig. diff. from prev. szns p={p_value:.3f}'
                        
                        # make histogram of 1) this years shots and 2) all other shots (last season and 2/3 season)
                        # Check if the figure already exists
                        fig_path = f"player_shots_histograms/{player_name.replace(' ', '_')}_{date}.png"
                        if not os.path.exists(fig_path):
                            fig, ax = plt.subplots()
                            bins = range(11)  # Bins from 0 to 10 (10 bins for values 0 to 9)
                            ax.hist(current_season_shots, bins=bins, alpha=0.5, label='2024/2025', align='left')
                            ax.hist(last_season_shots, bins=bins, alpha=0.5, label='2023/2024', align='left')
                            ax.hist(twothree_season_shots, bins=bins, alpha=0.5, label='2022/2023', align='left')
                            ax.set_xticks(range(10))  # Ensure x-axis has ticks from 0 to 9
                            ax.set_xlabel('Shots per game')
                            ax.set_ylabel('Frequency')
                            ax.set_title(f'{player_name} shots per game\n24/25:({cur_mean:.2f}, {cur_var:.2f}), prev:({past_mean:.2f}, {past_var:.2f})\n{diff_text}')
                            ax.legend()
                            fig.savefig(fig_path)
                            #plt.show()
                            plt.close(fig)



                    cursor.execute(f"SELECT 1 FROM {model_table} WHERE player_name = ? AND date = ? AND over_under = ? AND points = ?", (player_name, date, over_under, points))
                    if cursor.fetchone() is None:
                        cursor.execute(f'''
                        INSERT INTO {model_table} (player_name, date, over_under, points, implied_likelihood, normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood, poisson_kelly)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (player_name, date, over_under, points, implied_likelihood, normal_likelihood, poisson_likelihood, raw_data_likelihood, weighted_likelihood, poisson_kelly))
                        if poisson_kelly > 0 and print_bool:
                            print(f"Player: {player_name}, date: {date}, {over_under} {points}, Price: {price}, Kelly Bet: {poisson_kelly*100:.2f}%")


    conn.commit()
    conn.close()

if __name__ == "__main__":
    #print(get_shots_per_game(8478483, '20242025', '2024-10-13'))
    fetch_and_store_player_data()