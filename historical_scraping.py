import requests
from datetime import datetime

def bettingpros():
    # Define the base URL
    base_url = 'https://api.bettingpros.com/v3/pbcs'

    # Define the parameters
    params = {
        'sport': 'NHL',
        'event_date': '2024-10-27',
        'market_id': '151:152:156:157:160:162',
        'book_id': '10:12:13:14:15:18:19:20:21:22:24:25:26:27:28:29:30:31',
        'location': 'ALL'
    }

    # Construct the URL with parameters
    url = f"{base_url}?sport={params['sport']}"

    # Make the request
    response = requests.get(url)

    # Check the status code of the response
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(response.text)  # Print the raw response text
        return

    # Parse the JSON response
    data = response.json()

    # Extract event IDs for the given date
    event_ids = [event['event_id'] for event in data.get('markets', []) if event.get('event_date') == params['event_date']]

    # Print the event IDs
    print("Event IDs for the given date:", event_ids)

# Main function
def main():
    bettingpros()

if __name__ == "__main__":
    main()