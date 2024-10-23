import os
import sqlite3
import sys
print(f"Python interpreter: {sys.executable}")
import requests # type: ignore
import datetime
from player_api import get_player_id
from config import DATABASE


# Constants
INITIAL_BANKROLL = 100
BASE_URL = "https://api-web.nhle.com/v1"
SEASON = "20242025"

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

def teams_from_date_and_player(date, player_name, cursor):
    # find the teams from the date and player_name in the player_shots_odds table
    cursor.execute("SELECT DISTINCT home_team, away_team FROM player_shots_odds WHERE date = ? AND player_name = ?", (date, player_name))
    result = cursor.fetchone()
    if result:
        return result[0], result[1]
    else:
        return None, None

# Function to get the actual shots from the NHL API
def get_actual_shots(player_id, date):
    season_url = f"{BASE_URL}/player/{player_id}/game-log/{SEASON}/2"
    response = requests.get(season_url)
    if response.status_code == 200:
        try:
            data = response.json()
            if data and 'gameLog' in data:
                for game in data['gameLog']:
                    game_date = datetime.datetime.strptime(game['gameDate'], '%Y-%m-%d').date()
                    if game_date == datetime.datetime.strptime(date, '%Y-%m-%d').date():
                        return game['shots']
                print(f"No game found for player {player_id} on date {date}")
                return -1
            else:
                print("No valid game log data available.")
                return 0
        except requests.exceptions.JSONDecodeError:
            print(f"Error decoding JSON from {season_url}")
            return []
    else:
        print(f"Request to {season_url} failed with status code {response.status_code}")
        return []


# Function to update the ledger
def update_ledger():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # open the database
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()

    # Get the days that have not been updated
    cursor.execute("SELECT DISTINCT date FROM modelled_likelihoods WHERE date <= ? AND date NOT IN (SELECT DISTINCT date FROM daily_ledger_scaled)", (yesterday,))
    dates_to_update = cursor.fetchall()

    for date in dates_to_update:
        date = date[0]

        # Initialize bankroll
        # Get the most recent bankroll from the ledger table
        cursor.execute("SELECT final_dollar_value FROM daily_ledger_scaled ORDER BY date DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            bankroll_bestbook_0 = result[0]
        else:
            bankroll_bestbook_0 = INITIAL_BANKROLL

        cursor.execute('''
            SELECT player_name, date, implied_likelihood, points, over_under, poisson_kelly
            FROM modelled_likelihoods
            WHERE date = ? AND poisson_kelly > 0.01
        ''', (date,))
        best_bets = cursor.fetchall()

        # process the earnings/losses for the best bets only
        daily_earnings_bb = 0
        num_bets_bb = 0
        wager_sum_bb = 0
        scaling_factor = 1
        two_percent_min = 0
        # Calculate the sum of poisson_kelly for all entries in best_bets
        # Checking sum of all suggested bets to see if total suggested volume is greater than bankroll
        # if so, option A is only use bets > 2% of bankroll, if that's not significant enough, option B is to scale all bets down
        if sum(bet[5] for bet in best_bets) > 1:
            print(f"WARNING: Sum of suggested bets for date {date} is greater than bankroll.")
            if sum(bet[5] for bet in best_bets if bet[5] > 0.02) < 1:
                print(f"WARNING: Only using {date} suggested bets > 2% of bankroll to reduce bet volume below 100%.")
                two_percent_min = 1
            else:
                scaling_factor = 1 / sum(bet[5] for bet in best_bets)
                print(f"WARNING: Scaling all suggested bets for date {date} by {scaling_factor:.2f} to reduce bet volume below 100%.")
        
        for bet in best_bets:
            player_name, date, implied_likelihood, points, over_under, poisson_kelly = bet

            if two_percent_min == 1:
                min_pc_bet = 0.02
            else:
                min_pc_bet = 0.01
            if poisson_kelly*scaling_factor > min_pc_bet:
                # Get actual shots
                teams = teams_from_date_and_player(date, player_name, cursor)
                player_id = get_player_id(teams[0], teams[1], player_name)
                actual_shots = get_actual_shots(player_id, date)

                # Calculate bet amount
                bet_amount = bankroll_bestbook_0 * poisson_kelly * scaling_factor
                
                # Update the number of bets and total wagered
                num_bets_bb += 1
                wager_sum_bb += bet_amount

                # Determine win or loss based on actual shots and over_under
                if (over_under == 'Over' and actual_shots > points) or (over_under == 'Under' and actual_shots < points):
                    price = 1 / implied_likelihood
                    return_amount = (price - 1) * bet_amount
                    daily_earnings_bb += return_amount
                elif actual_shots != -1:
                    daily_earnings_bb -= bet_amount
                #print(f"Player: {player_name}, Date: {date}, Actual Shots: {actual_shots}, o/u: {over_under} {points}, Bet Amount: {bet_amount:.2f}")
        bankroll_bestbook_f = bankroll_bestbook_0 + daily_earnings_bb

        # Update the daily_ledger_best_book table
        cursor.execute('''
        INSERT INTO daily_ledger_scaled (date, number_of_bets_suggested, dollar_value_of_bets_suggested, initial_dollar_value, final_dollar_value)
        VALUES (?, ?, ?, ?, ?)
        ''', (date, num_bets_bb, wager_sum_bb, bankroll_bestbook_0, bankroll_bestbook_f))
        conn.commit()

    # Close the connection
    conn.close()

def print_ledger(ledger):
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {ledger}")
    print("Updated Ledger:")
    rows = cursor.fetchall()
    for row in rows:
        formatted_row = [f"{x:.2f}" if isinstance(x, float) else x for x in row]
        print(formatted_row)
    conn.close()

if __name__ == "__main__":
    update_ledger()
    # print both ledgers:
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_ledger_scaled")
    print("Scaled Ledger:")
    rows = cursor.fetchall()
    for row in rows:
        formatted_row = [f"{x:.2f}" if isinstance(x, float) else x for x in row]
        print(formatted_row)
    conn.close()