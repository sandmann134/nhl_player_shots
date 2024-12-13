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

    #create storage for the daily dollar amounts from different ledgers, so that they can all be plotted together after the loop
    daily_dollar_amounts = []

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    today_date = datetime.today().strftime('%Y-%m-%d')

    x_10 = 3

    ledger_name = 'daily_ledger_scaled_weight' + str(x_10) + 'tenthOppositionFactor' + '_sigDiff2'  #sigDiff for +2
    model_table = 'modelled_likelihoods_weight' + str(x_10) + 'tenthOppositionFactor' + '_sigDiff2' #sigDiff for +2
    #delete_table_fr_db(ledger_name)
    #delete_table_fr_db(model_table)

    create_ledger(ledger_name)
    create_player_models(model_table)

    fetch_and_store_player_data(x_10, 3, 2, 1, 0.1, 1)
    update_ledger(ledger_name, model_table)

     # Get daily final dollar amounts for A) weight 4 opp 0.1 and B) the new same but with stat_sig_diff
    conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
    cursor = conn.cursor()
   
    cursor.execute(f"SELECT final_dollar_value FROM {ledger_name}")
    daily_dollar_amounts.append(cursor.fetchall())

    cursor.execute("SELECT final_dollar_value FROM daily_ledger_scaled_weight4_tenthOppositionFactor")
    daily_dollar_amounts.append(cursor.fetchall())

    conn.close()

    for i in range(2):
        plt.plot(daily_dollar_amounts[i], label=f'Ledger {i+1}')

    plt.xlabel('Day')
    plt.ylabel('Dollar Amount')
    plt.title('Daily Dollar Amounts for Different Weights (both 1/10 opp)')
    plt.legend(['x_10=3, wSigDiffAdjust (+2,+1)', 'x_10=4'])
    #plt.show()
    plt.savefig(os.path.join(script_dir, 'plots/sigDiffAdjust_w3_P2p1.png'))

    print_ledger("daily_ledger_scaled_weight3")
    print_ledger("daily_ledger_scaled_weight4")
    print_ledger("daily_ledger_scaled")
    print_ledger("daily_ledger_scaled_weight4_tenthOppositionFactor")
    print_ledger("daily_ledger_scaled_weight3tenthOppositionFactor_sigDiff2")

if __name__ == "__main__":
    main()
    #delete_table_fr_db("daily_ledger_scaled")