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
# IDEA IS TO COMPARE ADJUSTING FOR OPPOSITION VS NOT 

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
    
    #create storage for the daily dollar amounts from different ledgers, so that they can all be plotted together after the loop
    daily_dollar_amounts = []

    #ledger_name = 'daily_ledger_scaled_weight4_wQuarterOppositionFactor'
    #model_table = 'modelled_likelihoods_weight4_wQuarterOppositionFactor'

    ledger_name3 = 'daily_ledger_scaled_weight4_wHalfOppositionFactor'
    model_table3 = 'modelled_likelihoods_weight4_wHalfOppositionFactor'

    #ledger_name2 = 'daily_ledger_scaled_weight4_wOppositionFactor'
    #model_table2 = 'modelled_likelihoods_weight4_wOppositionFactor'

    ledger_name4 = 'daily_ledger_scaled_weight4_tenthOppositionFactor'
    model_table4 = 'modelled_likelihoods_weight4_tenthOppositionFactor'

    ledger_name5 = 'daily_ledger_scaled_weight4_twentiethOppositionFactor'
    model_table5 = 'modelled_likelihoods_weight4_twentiethOppositionFactor'

    create_ledger(ledger_name5)
    create_player_models(model_table5)

    # model players with opposing team adjustments
    #fetch_and_store_player_data(4, 3, 2, 1, 0.25)
    fetch_and_store_player_data(4, 3, 2, 1, 0.5)
    #fetch_and_store_player_data(4, 3, 2, 1, 1)
    fetch_and_store_player_data(4, 3, 2, 1, 0.1)
    fetch_and_store_player_data(4, 3, 2, 1, 0.05)

    #update_ledger(ledger_name, model_table)
    update_ledger(ledger_name3, model_table3)
    #update_ledger(ledger_name2, model_table2)
    update_ledger(ledger_name4, model_table4)
    update_ledger(ledger_name5, model_table5)

    # Get daily final dollar amounts for A) the original, 'daily_legder_scaled' and B) the new, 'daily_ledger_scaled_wOppositionFactor'
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()

    cursor.execute(f"SELECT final_dollar_value FROM {ledger_name5}")
    daily_dollar_amounts.append(cursor.fetchall())

    cursor.execute(f"SELECT final_dollar_value FROM {ledger_name4}")
    daily_dollar_amounts.append(cursor.fetchall())

    #cursor.execute(f"SELECT final_dollar_value FROM {ledger_name}")
    #daily_dollar_amounts.append(cursor.fetchall())

    cursor.execute(f"SELECT final_dollar_value FROM {ledger_name3}")
    daily_dollar_amounts.append(cursor.fetchall())

    #cursor.execute(f"SELECT final_dollar_value FROM {ledger_name2}")
    #daily_dollar_amounts.append(cursor.fetchall())

    cursor.execute("SELECT final_dollar_value FROM daily_ledger_scaled_weight4")
    daily_dollar_amounts.append(cursor.fetchall())

    conn.close()

    # write todays odds from 1/10th scaling (which seems to be best model) to csv
    today_date = datetime.today().strftime('%Y-%m-%d')
    db_path = os.path.join(script_dir, DATABASE)  # Update with your actual database path
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {model_table4} WHERE date = '{today_date}'"
    df = pd.read_sql_query(query, conn)
    df.to_csv(os.path.join(script_dir,f"daily_odds/{model_table4}_{today_date}.csv"), index=False)
    conn.close()

    print_path = os.path.join(script_dir,f"daily_odds/{model_table4}_{today_date}.csv")
    print(f"CSV file {model_table4}_{today_date}.csv created at {print_path}.")    


    for i in range(4):
        plt.plot(daily_dollar_amounts[i], label=f'Ledger {i+1}')

    plt.xlabel('Day')
    plt.ylabel('Dollar Amount')
    plt.title('Daily Dollar Amounts for Different Weights')
    plt.legend(['x_10=4, 1/20 Opp.Scaling', 'x_10=4, 1/10 Opp.Scaling', 'x_10=4, 1/2 Opp.Scaling', 'x_10=4, no Opp.Scaling'])
    #plt.show()
    plt.savefig(os.path.join(script_dir, 'plots/opposition_test.png'))


if __name__ == "__main__":
    main()
    #delete_table_fr_db("daily_ledger_scaled")