This repository holds the core code for a statistical NHL-player shot-on-goal model based on past player performances. 

Most of these files are extraneous or test/analysis scripts (and results).  The core files and flow follow:
setup_database.py
main.py
odds_api_main.py
player_api.py
update_ledger.py (only for evaluating results)
weight_test.py
opposition_test.py

setup_database.py or similar should be used to initialize the .db file

These scripts in their current form are inefficient as they were built additively with several different models, 
and some testing/graphing output built in.  But they run easily and quickly enough to be useful daily.

Main daily run structure is as follows:
- main.py is run, which then calls
- odds_api_main.py which gathers player shot odds for the day if not done already, storing them in table in db
- player_api.py is then run with automatically fetches player data from nhl api and models the relevant players
  with the original, default weighting of different time periods.  Once this is constructed, several different
  statistical models output the expected likelihood of that player having over/under the shot total, and this is
  compared to the implied betting odds to produce a suggested bet size as a fraction of the Kelly bet (if there
  is an expected edge).  These modelled likelihoods/recommended bets are written to a .csv
- daily_factor_update() is then run which updates factors used to compensate for how many shots a given team
  allows, relative to the league average.  This is used later in models which include opposition weighting.
- update_ledger() is run which updates a ledger for the past days, to check results and see if the suggested
  bets would have won or lost money, and then store this in the various ledgers - one for each model weighting.
- weight_test.py and opposition_test.py are then run, which repeat all of this but with 1) different weightings
  for recency (last 10 games, this season, last season, 22/23 season) and 2) including a factor to account for
  who the opposing team is on a given night (whether they give up more or less than league average).  These
  scripts also update/produce plots showing the bankrolls over time for the various different models.

To keep the details of the statistically modelling private, those details have been removed from this public
repository.  This repository is posted to show script structure and execution workflow.  If you would like to
discuss the details of the modelling, please contact me directly.

The performance of several models can be found in 'tested_models_plot.png'.  This fig. shows the relative 
performance of a number of statistical models with different recency weightings which were developed as part of 
the testing process.  Tests of several other factors also exist, with each model adding or combining different: 
1) statistical model type,
2) different weightings towards recency,
3) different adjustments based on the opponents' average shots against (relative to league average),among other smaller factors.
The included plot shows daily bankroll if one were to start with $100 on day one of the 2024/25 NHL season, and
place bets based on each model's output and using a fraction of a Kelly criteria for bet size.  The plot is updated
until start of the NHL break for 4-Nations.
