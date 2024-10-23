import os
import requests # type: ignore
import sqlite3
from datetime import datetime, timedelta
from config import API_KEY, SPORT, REGIONS, MARKETS, ODDS_FORMAT, DATE_FORMAT, DATABASE

# Set this variable to 'y' if you want to print to console
print_to_console = 'y'

# Calculate today's date in ISO format
today = datetime.now().date().isoformat()

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Connect to the database
conn = sqlite3.connect(os.path.join(script_dir, DATABASE))
cursor = conn.cursor()

# Check if there are already any odds in the database for today
cursor.execute('SELECT COUNT(*) FROM player_shots_odds WHERE date = ?', (today,))
odds_count = cursor.fetchone()[0]

if odds_count > 0:
    print('Odds for today are already in the database.')
else:
    # Step 1: Get a list of upcoming NHL events
    events_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/events',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'dateFormat': DATE_FORMAT,
        }
    )

    try:
        events_data = events_response.json()
    except ValueError:
        print('Error: Response is not in JSON format')
        events_data = []

    # Check for error messages in the response
    if isinstance(events_data, dict) and 'error_code' in events_data:
        if print_to_console == 'y':
            print(f"Error: {events_data['message']}")
            print(f"Error Code: {events_data['error_code']}")
            print(f"Details: {events_data['details_url']}")
        events_data = []

    # Step 2: Extract the event ID for the next game
    if events_data:
        date = datetime.now().date().isoformat()

        for event in events_data:
            event_id = event['id']
            home_team = event['home_team']
            away_team = event['away_team']
            print(f"Processing {away_team} at {home_team}, ID: {event_id}")

            # Step 3: Use the event ID to query the odds for the player shots on goal props
            event_odds_response = requests.get(
                f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
                params={
                    'api_key': API_KEY,
                    'regions': REGIONS,
                    'markets': 'player_shots_on_goal',
                    'oddsFormat': ODDS_FORMAT,
                    'dateFormat': DATE_FORMAT,
                }
            )

            try:
                event_odds_data = event_odds_response.json()
            except ValueError:
                print('Error: Response is not in JSON format')
                event_odds_data = []

            # Check for error messages in the response
            if isinstance(event_odds_data, dict) and 'error_code' in event_odds_data:
                print(f"Error: {event_odds_data['message']}")
                print(f"Error Code: {event_odds_data['error_code']}")
                print(f"Details: {event_odds_data['details_url']}")
                event_odds_data = []

            # Collect player shots on goal props
            player_props = {}
            for bookmaker in event_odds_data.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'player_shots_on_goal':
                        for outcome in market['outcomes']:
                            player_name = outcome['description']
                            if player_name not in player_props:
                                player_props[player_name] = []
                            player_props[player_name].append({
                                'bookmaker': bookmaker['title'],
                                'over_under': outcome['name'],
                                'price': outcome['price'],
                                'points': outcome['point'],
                                'home_team': home_team,
                                'away_team': away_team
                            })

            # Store player shots on goal props in the database
            for player, props in player_props.items():
                for prop in props:
                    cursor.execute('''
                    INSERT INTO player_shots_odds (event_id, home_team, away_team, player_name, bookmaker, over_under, price, points, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (event_id, prop['home_team'], prop['away_team'], player, prop['bookmaker'], prop['over_under'], prop['price'], prop['points'], date))
        
        conn.commit()

        # Print the player shots on goal props organized by player
        if print_to_console == 'y':
            for player, props in player_props.items():
                print(f"Player: {player}")
                for prop in props:
                    print(f"  Bookmaker: {prop['bookmaker']}, Over/Under: {prop['over_under']}, Price: {prop['price']}, Points: {prop['points']}, Home Team: {prop['home_team']}, Away Team: {prop['away_team']}")
    else:
        print('No upcoming NHL events found.')

    # Print used and remaining requests
    print('Used requests:', event_odds_response.headers['x-requests-used'])
    print('Remaining requests:', event_odds_response.headers['x-requests-remaining'])

conn.close()