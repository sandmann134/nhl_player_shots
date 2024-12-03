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
# IDEA IS TO COMPARE SCALING ALL BETS (WHEN RECOMMENDED > BANKROLL) VS. TRUNCATING (LARGEST FIRST)

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

    ledger_name = 'daily_ledger_scaled_weight4_tenthOppositionFactor_TruncBets'
    
    ref_ledger_name = 'daily_ledger_scaled_weight4_tenthOppositionFactor'
    model_table = 'modelled_likelihoods_weight4_tenthOppositionFactor'


    create_ledger(ledger_name)

    #fetch_and_store_player_data(4, 3, 2, 1, 0.1)

    #update_ledger(ref_ledger_name, model_table)
    
    update_ledger(ledger_name, model_table, 1)

    # Get daily final dollar amounts for A) 'daily_ledger_scaled_weight4_tenthOppositionFactor' and B) 'daily_ledger_scaled_weight4_tenthOppositionFactor_TruncBets'
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()

    cursor.execute(f"SELECT final_dollar_value FROM {ref_ledger_name}")
    daily_dollar_amounts.append(cursor.fetchall())

    cursor.execute(f"SELECT final_dollar_value FROM {ledger_name}")
    daily_dollar_amounts.append(cursor.fetchall())

    conn.close()  


    for i in range(2):
        plt.plot(daily_dollar_amounts[i], label=f'Ledger {i+1}')

    plt.xlabel('Day')
    plt.ylabel('Dollar Amount')
    plt.title('Daily Dollar Amounts for Different Weights')
    plt.legend(['x_10=4, 1/10 Opp.Scaling', 'x_10=4, 1/10 Opp.Scaling, Truncated (not scaled) bets'])
    plt.savefig(os.path.join(script_dir, 'plots/scale_test.png'))
    plt.show()


if __name__ == "__main__":
    main()
    #delete_table_fr_db("daily_ledger_scaled")