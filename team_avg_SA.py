from datetime import datetime
import sqlite3
import requests
import numpy as np
from config import DATABASE
import csv

# Function to get team stats from NHL API
def get_team_stats():
    team_shots_url = "https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId=20242025%20and%20gameTypeId=2"
    response = requests.get(team_shots_url)
    team_stats = {}
    data = response.json().get('data', [])
    for team in data:
        team_stats[team['teamFullName']] = {
            'teamId': team['teamId'],
            'shotsAgainstPerGame': team['shotsAgainstPerGame']
        }
    return team_stats

def get_opposition_factor_frtable(opposing_team, team_stats):

    average_shots_against = np.mean([stats['shotsAgainstPerGame'] for stats in team_stats.values()])
    factor = team_stats[opposing_team]['shotsAgainstPerGame'] / average_shots_against
    return factor

def create_table(conn, team_names):
    cursor = conn.cursor()
    sorted_team_names = sorted(team_names)
    columns = ', '.join([f'"{team}" REAL' for team in sorted_team_names])
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS opposing_team_factors (
            date TEXT PRIMARY KEY,
            {columns}
        )
    ''')
    conn.commit()

def insert_factors(conn, team_stats):
    cursor = conn.cursor()
    today_date = datetime.today().strftime('%Y-%m-%d')
    sorted_team_names = sorted(team_stats.keys())
    factors = {team: get_opposition_factor_frtable(team, team_stats) for team in sorted_team_names}
    columns = ', '.join([f'"{team}"' for team in sorted_team_names])
    placeholders = ', '.join(['?' for _ in sorted_team_names])
    values = [today_date] + [factors[team] for team in sorted_team_names]
    cursor.execute(f'''
        INSERT OR REPLACE INTO opposing_team_factors (date, {columns})
        VALUES (?, {placeholders})
    ''', values)
    conn.commit()

def print_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opposing_team_factors")
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    print(headers)
    for row in rows:
        formatted_row = [f"{item:.3f}" if isinstance(item, float) else item for item in row]
        print(formatted_row)

def delete_factors_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS opposing_team_factors")
    conn.commit()
    conn.close()

def daily_factor_update():
    conn = sqlite3.connect(DATABASE)
    team_stats = get_team_stats()
    team_names = list(team_stats.keys())
    create_table(conn, team_names)
    insert_factors(conn, team_stats)
    conn.close()

def get_opposition_factor(date, opposing_team, opposition_adjust):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM opposing_team_factors WHERE date = ?", (date,))
    row = cursor.fetchone()
    if row:
        headers = [description[0] for description in cursor.description]
        if opposing_team == 'St Louis Blues':
            opposing_team = 'St. Louis Blues'
        elif opposing_team not in headers:
            print(f"Opposing team {opposing_team} not found in the database.")
            factor = 1
            return factor
        factor = row[headers.index(opposing_team)]
        conn.close()
        return factor


    with open('team_shots_gamelogs.csv', mode='r') as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames
        team_games = [row for row in reader if row['Team'] == opposing_team and row['Game Date'] < date]

    if not team_games:
        conn.close()
        factor = 1
        return factor

    team_sa_gp = np.mean([float(game['SA/GP']) for game in team_games])
    team_gp = len(team_games)
    ramp = 1
    if team_gp < 10:
        ramp = team_gp / 10    
    all_sa_gp = []

    with open('team_shots_gamelogs.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Game Date'] < date:
                all_sa_gp.append(float(row['SA/GP']))

    league_avg_sa_gp = np.mean(all_sa_gp)
    factor = 1 + ((team_sa_gp / league_avg_sa_gp) - 1) * ramp * opposition_adjust
    conn.close()
    return factor

# Main function
def main():
    daily_factor_update

if __name__ == "__main__":
    main()
    #delete_factors_table()
    