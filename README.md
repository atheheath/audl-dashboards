# AUDL Dashboards

AUDL statistics using dashboards created with [dash](https://dash.plotly.com) 

To start the server, make sure `./run_dashboard.sh` is executable
```
chmod u+x ./run_dashboard.sh
```

Then to start the server
```
./run_dashboard.sh
```

# Overview
* Entry point is app.py
* Main flow exists at index.py

Flow is
1. Pull all data (initializes from home.all_game_urls)
2. When game is clicked from dropdown, parse all data (from home.update_game_data)
3. When changing the slider, show next possession


## Glossary of events
Event Index
1: Offense lineup
2: Defense lineup
3: Pull
5: Block
8: Turnover
17: Stall
19: Drop
20: Throw
22: Goal
