import sqlite3
from config import DATABASE

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create tables
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

# Create the table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS modelled_likelihoods (
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


# Create the daily_ledger_best_book table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_ledger_best_book (
    id INTEGER PRIMARY KEY,
    date TEXT,
    number_of_bets_suggested INTEGER,
    dollar_value_of_bets_suggested REAL,
    initial_dollar_value REAL,
    final_dollar_value REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_ledger_scaled (
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