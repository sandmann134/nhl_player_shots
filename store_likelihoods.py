import sqlite3
from datetime import datetime
from config import DATABASE

# Example function to store modelled likelihoods
def store_modelled_likelihoods(event_id, player_name, likelihood):
    date = datetime.now().date().isoformat()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO modelled_likelihoods (event_id, player_name, likelihood, date)
    VALUES (?, ?, ?, ?)
    ''', (event_id, player_name, likelihood, date))
    conn.commit()
    conn.close()