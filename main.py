import os
import subprocess
import sqlite3
import pandas as pd # type: ignore
from datetime import datetime, timedelta
from player_api import fetch_and_store_player_data
from update_ledger import update_ledger, print_ledger
from config import DATABASE
from team_avg_SA import daily_factor_update

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

def fetch_and_print_odds():
    db_path = 'nhl_player_shots.db'  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    tables = ['player_shots_odds', 'modelled_likelihoods', 'daily_ledger_best_book', 'daily_ledger_draftkings']  # Update with your actual table names
    for table in tables:
        print_table_preview(conn, table)
    conn.close()

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

    # Run the script to fetch and store odds
    subprocess.run(['python3', os.path.join(script_dir, 'odds_api_main.py')])

    # Run the script to calculate modelled likelihoods for today's bets
    subprocess.run(['python3', os.path.join(script_dir, 'player_api.py')])

    daily_factor_update()

    # Run the script to update the ledger for actual results in days prior to the current
    #subprocess.run(['python3', 'update_ledger.py'])
    fetch_and_store_player_data()

    # Optionally, print the odds table for verification
    #fetch_and_print_odds()

    #delete_table_fr_db("daily_ledger_draftkings")
    
    # Get today's date in the format YYYY-MM-DD
    today_date = datetime.today().strftime('%Y-%m-%d')

    # Write only the entries in modelled_likelihoods which have today's date to a csv file
    db_path = os.path.join(script_dir, DATABASE)  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM modelled_likelihoods WHERE date = '{today_date}'"
    df = pd.read_sql_query(query, conn)
    df.to_csv(os.path.join(script_dir,f"daily_odds/modelled_likelihoods_{today_date}.csv"), index=False)
    conn.close()

    print_path = os.path.join(script_dir,f"daily_odds/modelled_likelihoods_{today_date}.csv")
    print(f"CSV file modelled_likelihoods_{today_date}.csv created at {print_path}.")

    # Update Best Book Ledger, print updated ledger:
    update_ledger()
    
    # Run weight_test.py to update the ledger with different weights
    subprocess.run(['python3', os.path.join(script_dir, 'weight_test.py')])
    # Run opposition_test.py to update the ledger with different opposition factors
    subprocess.run(['python3', os.path.join(script_dir, 'opposition_test.py')])
    # Run weight_test3_avg.py to update the ledger with different weights
    #subprocess.run(['python3', os.path.join(script_dir, 'weight_test3_avg.py')])

    # Print the updated base ledger
    print_ledger("daily_ledger_scaled_weight4")
    print_ledger("daily_ledger_scaled_weight4_tenthOppositionFactor")


if __name__ == "__main__":
    main()
    #delete_table_fr_db("modelled_likelihoods_2324flat")
    #delete_table_fr_db("daily_ledger_scaled_2324flat")
    #print_ledger("daily_ledger_scaled_weight4")
    #print_ledger("daily_ledger_scaled_weight4_tenthOppositionFactor")

    # Get yesterdays's date in the format YYYY-MM-DD
    #yesterday_date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

    # Get the directory of the current script
    #script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Write only the entries in modelled_likelihoods which have today's date to a csv file
    #db_path = os.path.join(script_dir, DATABASE)  # Update with your actual database path
    #conn = sqlite3.connect(db_path)
    #query = f"SELECT * FROM modelled_likelihoods_weight4_wOppositionFactor WHERE date = '{yesterday_date}'"
    #df = pd.read_sql_query(query, conn)
    #df.to_csv(os.path.join(script_dir,f"daily_odds/modelled_likelihoods_w4_wOppFactor_{yesterday_date}.csv"), index=False)
    #conn.close()
