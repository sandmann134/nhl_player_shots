Most of these files are extraneous or test/analysis scripts (and results).  The core files and flow follow
setup_database.py
main.py
odds_api_main.py
player_api.py
update_ledger.py (only for evaluating results)
weight_test.py
opposition_test.py

setup_database.py or similar should be used to initialize the .db file

Main daily run structure is as follows:
- main.py is run, which then calls
- odds_api_main.py which gathers player shot odds for the day if not done already, storing them in table in db
- player_api.py is then run with automatically fetches player data from nhl api and models the relevant players
  with the original, default weighting.  These modelled likelihoods/recommended bets are written to a .csv
- daily_factor_update() is then run which updates factors used to compensate for how many shots a given team
  allows, relative to the league average.  This is used later in models which include opposition weighting.
- update_ledger() is run which updates a ledger for the past days, to check results and see if the suggested
  bets won or lost money, and then store this in the various ledgers - one for each model weighting.
- weight_test.py and opposition_test.py are then run, which repeat all of this but with 1) different weightings
  for recency (last 10 games, this season, last season, 22/23 season) and 2) including a factor to account for
  who the opposing team is on a given night (whether they give up more or less than league average).

Bets are typically made based on the output 'modelled_likelihoods_weight4_tenthOppositionFactor.csv' which has 
a weighting of x_10=4, x_2024=3, x_2023=2, x_2022=1 (meaning last 10 games counted 4 times each, other games 
from this season 3 times each, games last season two times each, 22/23 season 1 time each.  All these games 
are taken to construct a poisson distribution for the likelihood modelling.  The 1/10th opposition factor means
that the opposing team's average shots against is compared to the average, and an individual player's mean SOG is
scaled by 1/10th of that difference [ player mean SOG*(opposing team avg.-league average)/league average ] 
