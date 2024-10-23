import os
import subprocess
import sqlite3
import pandas as pd # type: ignore
from datetime import datetime
from player_api import fetch_and_store_player_data
from update_ledger import update_ledger, print_ledger
from config import DATABASE

# IN PROGRESS:
# IDEA IS TO LOOP THROUGH DIFFERENT WEIGHTS, PLOT RESULTS AGAINST EACH OTHER
# thus need to run through player API each time, as it currently stands

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

    fetch_and_store_player_data()
    
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
    print_ledger("daily_ledger_best_book")

if __name__ == "__main__":
    #main()
    delete_table_fr_db("daily_ledger_scaled")