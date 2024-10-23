import requests
from datetime import datetime, timedelta


# An api key is emailed to you when you sign up to a plan
# Get a free API key at https://api.the-odds-api.com/
API_KEY = '204b8940e5d4c9be1a3ab2e8192a286f'
SPORT = 'icehockey_nhl' # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports
REGIONS = 'us' # uk | us | eu | au. Multiple can be specified if comma delimited
MARKETS = 'h2h,spreads' # h2h | spreads | totals. Multiple can be specified if comma delimited
ODDS_FORMAT = 'decimal' # decimal | american
DATE_FORMAT = 'iso' # iso | unix

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# First get a list of in-season sports
#   The sport 'key' from the response can be used to get odds in the next request
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# Calculate tomorrow's date in ISO format
tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()

# Get a list of live & upcoming games for the sport you want, along with odds for different bookmakers
odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
    params={
        'api_key': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,  # Moneyline odds
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
    }
)

try:
    odds_data = odds_response.json()
except ValueError:
    print('Error: Response is not in JSON format')
    odds_data = []

print(odds_data)

# Filter for the Carolina vs Tampa Bay game
carolina_tampa_game = next((game for game in odds_data if 'Carolina' in game['home_team'] and 'Tampa Bay' in game['away_team']), None)

if not carolina_tampa_game:
    print('No Carolina vs Tampa Bay game found.')
else:
    for bookmaker in carolina_tampa_game['bookmakers']:
        print(f"Bookmaker: {bookmaker['title']}")
        for market in bookmaker['markets']:
            print(f"  Market: {market['key']}")
            for outcome in market['outcomes']:
                print(f"    Outcome: {outcome['name']}, Price: {outcome['price']}")
 

    # Check the usage quota
    print('Remaining requests', odds_response.headers['x-requests-remaining'])
    print('Used requests', odds_response.headers['x-requests-used'])