import sqlite3
from config import DATABASE

def create_ledger(table_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY,
        date TEXT,
        number_of_bets_suggested INTEGER,
        dollar_value_of_bets_suggested REAL,
        initial_dollar_value REAL,
        final_dollar_value REAL
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Created table {table_name}")

def create_player_models(table_name = 'modelled_likelihoods'):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY,
        player_name TEXT,
        date TEXT,
        over_under TEXT,
        points REAL,
        implied_likelihood REAL,
        normal_likelihood REAL,
        poisson_likelihood REAL,
        raw_data_likelihood REAL,
        weighted_likelihood REAL,
        poisson_kelly REAL
    )
    ''')
    conn.commit()
    conn.close()
    print(f"Created table {table_name}")

def create_player_shots_odds():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_shots_odds (
        id INTEGER PRIMARY KEY,
        event_id TEXT,
        home_team TEXT,
        away_team TEXT,
        player_name TEXT,
        bookmaker TEXT,
        over_under TEXT,
        price REAL,
        points REAL,
        date TEXT
    )
    ''')
    conn.commit()
    conn.close()



if __name__ == "__main__":
    # Create the daily_ledger_best_book table if it doesn't exist
    create_ledger('daily_ledger_best_book')

    # Create player models if they don't exist
    create_player_models('modelled_likelihoods')

    # Create player shots odds table if it doesn't exist
    create_player_shots_odds()
