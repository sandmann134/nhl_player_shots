from datetime import datetime
import requests
import numpy as np
from scipy.stats import ttest_ind

# Function to get team stats from NHL API
def get_team_stats():
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    response = requests.get(url)
    teams = response.json()['teams']
    team_stats = {}
    
    for team in teams:
        team_id = team['id']
        team_name = team['name']
        team_stats[team_name] = get_shots_allowed_per_game(team_id)
    
    return team_stats

# Function to get shots allowed per game for a specific team
def get_shots_allowed_per_game(team_id):
    url = f"https://statsapi.web.nhl.com/api/v1/teams/{team_id}/stats"
    response = requests.get(url)
    stats = response.json()['stats'][0]['splits'][0]['stat']
    return stats['shotsAllowed']

# Function to perform statistical comparison
def compare_shots_allowed(team_stats):
    significant_teams = []
    
    for team, shots_allowed in team_stats.items():
        other_teams_shots = [shots for t, shots in team_stats.items() if t != team]
        t_stat, p_value = ttest_ind([shots_allowed], other_teams_shots)
        
        if p_value < 0.05:
            significant_teams.append((team, shots_allowed))
    
    return significant_teams


# Main function
def main():
    #team_stats = get_team_stats()
    #significant_teams = compare_shots_allowed(team_stats)
    
    #for team, shots_allowed in significant_teams:
    #    print(f"Team: {team}, Mean Shots Allowed: {shots_allowed}")
    base_url = "https://api-web.nhle.com/v1"
    url2 = "https://api.nhle.com/stats/rest"
    standings_url = f"{base_url}/standings/now"
    response = requests.get(standings_url)
    data = response.json()
    #print(data)

    # Extract team abbreviations
    team_abbreviations = [team['teamAbbrev']['default'] for team in data['standings']]

    #team_stats_url = f"{url2}/en/game?isAggregate=0&gameTypeId=2&season=20242025&gameDate<=2024-10-24&homeTeamId=19"
    team_homegames_url = "https://api.nhle.com/stats/rest/en/game?isAggregate=0&cayenneExp=season=20242025%20and%20gameType=2%20and%20homeTeamId=19"
    team_awaygames_url = "https://api.nhle.com/stats/rest/en/game?isAggregate=0&cayenneExp=season=20242025%20and%20gameType=2%20and%20visitingTeamId=19"

    home_response = requests.get(team_homegames_url)
    away_response = requests.get(team_awaygames_url)

    home_data = home_response.json()
    away_data = away_response.json()

    # Get today's date
    today_date = datetime.today().date()

    # Extract game numbers for games before today's date
    home_game_numbers = [
        game['gameNumber'] for game in home_data['data']
        if datetime.strptime(game['gameDate'], '%Y-%m-%d').date() < today_date
    ]
    away_game_numbers = [
        game['gameNumber'] for game in away_data['data']
        if datetime.strptime(game['gameDate'], '%Y-%m-%d').date() < today_date
    ]

    # print(f"home_game_numbers: {home_game_numbers}\naway_game_numbers: {away_game_numbers}")

    team_scoreboard_url = "https://api.nhle.com/stats/rest/en/game?isAggregate=0"
    response = requests.get(team_scoreboard_url)
    data = response.json()
    # Print the keys of the response to see the top-level structure
    print("Top-level keys:", data.keys())



# https://www.nhl.com/stats/teams?aggregate=0&reportType=game&dateFrom=2024-10-04&dateTo=2024-10-29&gameType=2&playerPlayedFor=franchise.32&sort=points,wins&page=0&pageSize=50
# https://www.nhl.com/stats/teams?aggregate=0&reportType=game&dateFrom=2024-10-04&dateTo=2024-10-29&gameType=2&playerPlayedFor=franchise.19&sort=points,wins&page=0&pageSize=50
# https://www.nhl.com/stats/teams?aggregate=0&reportType=game&seasonFrom=20242025&seasonTo=20242025&dateFromSeason&gameType=2&playerPlayedFor=franchise.19&sort=points,wins&page=0&pageSize=50

if __name__ == "__main__":
    main()