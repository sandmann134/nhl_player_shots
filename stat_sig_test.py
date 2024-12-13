import os
import subprocess
import sqlite3
import pandas as pd # type: ignore
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial
from scipy.stats import poisson, nbinom
from datetime import datetime, timedelta
from player_api import fetch_and_store_player_data, get_player_id, get_shots_per_game
from update_ledger import update_ledger, print_ledger
from setup_database import create_ledger, create_player_models
from config import DATABASE
from scipy.stats import poisson


# IN PROGRESS:
# IDEA IS TO TRY WEIGHTING DEPENDING ON HOW 'DIFFERENT' this season is

def print_table_preview(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    if len(df) >= 4:
        print(f"First 3 rows of {table_name}:")
        print(df.head(3))
        print(f"Last 3 rows of {table_name}:")
        print(df.tail(3))
    else:
        print(f"Entire {table_name} table:")
        print(df)

def delete_table_fr_db(table):
    db_path = 'nhl_player_shots.db'  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()

def write_table_to_csv(table_name):
    db_path = 'nhl_player_shots.db'  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    df.to_csv(f"{table_name}.csv", index=False)
    conn.close()

def main():

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    today_date = datetime.today().strftime('%Y-%m-%d')

    p1 = 'Quinn Hughes'
    p2 = 'Conor Garland'
    p3 = 'Evan Rodrigues'
    p4 = 'Anton Lundell'
    p5 = 'Pius Suter'
    p6 = ''
    p7 = 'Owen Tippett'
    p8 = 'Lucas Raymond'
    p9 = 'Patrick Kane'
    p10 = 'Alex DeBrincat'
    p11 = 'Vladimir Tarasenko'
    p12 = 'Dylan Holloway'
    p13 = 'Jordan Kyrou'
    p14 = 'Jake Walman' 
    p15 = 'Tyler Toffoli'
    p16 = 'Justin Faulk'
    p17 = 'Nathan MacKinnon'
    p18 = 'Mikhail Sergachev'


    players = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18]
    teams = ['Washington Capitals', 'Columbus Blue Jackets',
             'Washington Capitals', 'Columbus Blue Jackets', 
             'Washington Capitals', 'Winnipeg Jets', 
             'Philadelphia Flyers', 'Detroit Red Wings',
             'Detroit Red Wings', 'Detroit Red Wings',
             'Detroit Red Wings', 'St. Louis Blues',
             'St. Louis Blues', 'San Jose Sharks',
             'San Jose Sharks', 'St. Louis Blues',
             'Colorado Avalanche', 'Utah Hockey Club']

    for player in players:
        player_id = get_player_id(teams[players.index(player)], teams[0], player)[0]
        current_season_shots = get_shots_per_game(player_id, '20242025', today_date)
        last_season_shots = get_shots_per_game(player_id, '20232024', today_date)
        twothree_season_shots = get_shots_per_game(player_id, '20222023', today_date)

        #combine previous seasons into one:
        pre_thisseason = last_season_shots + twothree_season_shots
        all_shots = pre_thisseason + current_season_shots
        
        #output the mean and variance of pre_thisseason and this season:
        print(f"Player: {player}")
        cur_mean = sum(current_season_shots) / len(current_season_shots)
        cur_var = sum([(x - sum(current_season_shots) / len(current_season_shots))**2 for x in current_season_shots]) / len(current_season_shots)
        print(f"Mean shots and variance this season: {cur_mean:.3f}, {cur_var:.3f}, ({cur_var/cur_mean:.2f})")
        past_mean = sum(pre_thisseason) / len(pre_thisseason)
        past_var = sum([(x - sum(pre_thisseason) / len(pre_thisseason))**2 for x in pre_thisseason]) / len(pre_thisseason)
        print(f"Mean shots and variance previous seasons: {past_mean:.3f}, {past_var:.3f}, ({past_var/past_mean:.2f})")

        # Perform a statistical test to compare current season shots with previous seasons' shots
        # Null hypothesis: The two samples come from the same distribution
        # Alternative hypothesis: The two samples come from different distributions

        # Calculate the lambda (rate) for the Poisson distributions
        lambda_current = cur_mean
        lambda_pre_thisseason = past_mean

        # Perform a two-sample Poisson test

        # Calculate the p-value
        p_value = poisson.cdf(sum(current_season_shots), lambda_pre_thisseason * len(current_season_shots))

        # Determine if the p-value is less than the significance level (e.g., 0.05)
        significance_level = 0.05
        if p_value < significance_level:
            print("The current season shots are statistically significantly different from previous seasons' shots (reject H0).")
        else:
            print("The current season shots are not statistically significantly different from previous seasons' shots (fail to reject H0).")
        
        poisson_model = sm.GLM(all_shots, sm.add_constant(range(len(all_shots))), family=sm.families.Poisson()).fit()
        print(poisson_model.summary())

        X = sm.add_constant(range(len(all_shots)))


        # Fit Negative Binomial model (with automatic alpha estimation)
        #negbin_model = NegativeBinomial(all_shots, X).fit()
        #print(negbin_model.summary())

        # make histogram of 1) this years shots and 2) all other shots (last season and 2/3 season)
        fig, ax = plt.subplots()
        bins = range(11)  # Bins from 0 to 10 (10 bins for values 0 to 9)
        ax.hist(current_season_shots, bins=bins, alpha=0.5, label='2024/2025', align='left')
        ax.hist(last_season_shots, bins=bins, alpha=0.5, label='2023/2024', align='left')
        ax.hist(twothree_season_shots, bins=bins, alpha=0.5, label='2022/2023', align='left')
        ax.set_xticks(range(10))  # Ensure x-axis has ticks from 0 to 9
        ax.set_xlabel('Shots per game')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{player} shots per game')
        ax.legend()
        fig.savefig(f"player_shots_histograms/{player.replace(' ', '_')}_{today_date}.png")
        plt.show()


if __name__ == "__main__":
    main()
    #delete_table_fr_db("daily_ledger_scaled")