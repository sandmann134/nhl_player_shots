import os
import subprocess
import sqlite3
import pandas as pd # type: ignore
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from player_api import fetch_and_store_player_data
from update_ledger import update_ledger, print_ledger
from setup_database import create_ledger, create_player_models
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
    
    #create storage for the daily dollar amounts from different ledgers, so that they can all be plotted together after the loop
    daily_dollar_amounts = []

    for i in range(3, 6):
        # Create new table for ledger with different weights
        ledger_name = f'daily_ledger_scaled_weight{i}'
        model_table = f'modelled_likelihoods_weight{i}'
        if i == 5:
            model_table = 'modelled_likelihoods'
            ledger_name = 'daily_ledger_scaled'

        # CREATE
        create_ledger(ledger_name)
        create_player_models(model_table)

        # model players with current weights
        fetch_and_store_player_data(i, 3, 2, 1)

        # update correct ledger with actual results
        update_ledger(ledger_name, model_table)

        # store the daily dollar amount for each ledger
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        query = f"SELECT final_dollar_value FROM {ledger_name}"
        print_table_preview(conn, ledger_name)
        df = pd.read_sql_query(query, conn)
        daily_dollar_amounts.append(df)
        conn.close()
        print(f"Daily dollar amounts for {ledger_name}:")
        print(df)

        # if weight = 4 (which seems to be best model), write today's odds to csv
        if i == 4:
            today_date = datetime.today().strftime('%Y-%m-%d')
            db_path = os.path.join(script_dir, DATABASE)  # Update with your actual database path
            conn = sqlite3.connect(db_path)
            query = f"SELECT * FROM {model_table} WHERE date = '{today_date}'"
            df = pd.read_sql_query(query, conn)
            df.to_csv(os.path.join(script_dir,f"daily_odds/{model_table}_{today_date}.csv"), index=False)
            conn.close()

            print_path = os.path.join(script_dir,f"daily_odds/{model_table}_{today_date}.csv")
            print(f"CSV file {model_table}_{today_date}.csv created at {print_path}.")

    # plot the daily dollar amounts for each ledger
    for i in range(len(daily_dollar_amounts)):
        plt.plot(daily_dollar_amounts[i], label=f'Weight {i+4}')

    plt.xlabel('Day')
    plt.ylabel('Dollar Amount')
    plt.title('Daily Dollar Amounts for Different Weights')
    plt.legend(['x_10 = 3', 'x_10 = 4', 'x_10 = 5'])
    plt.savefig(os.path.join(script_dir, 'plots/weight_test.png'))
    #plt.show()
    

if __name__ == "__main__":
    main()
    #delete_table_fr_db("daily_ledger_scaled")