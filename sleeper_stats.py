import requests
import pandas as pd
import os
import json

# ----- Fetch Functions -----
def get_users(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/users"
    return requests.get(url).json()

def get_rosters(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    return requests.get(url).json()

def get_matchups(league_id, week):
    url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    return requests.get(url).json()

# ----- Player Data -----
PLAYER_CACHE_PATH = "stats_cache/player_cache.json"
STATS_CACHE_PATH = "stats_cache/{year}_{week}.json"

def get_player_map(force_refresh=False):
    if not force_refresh and os.path.exists(PLAYER_CACHE_PATH):
        with open(PLAYER_CACHE_PATH, 'r') as f:
            return json.load(f)
    
    url = "https://api.sleeper.app/v1/players/nfl"
    data = requests.get(url).json()
    with open(PLAYER_CACHE_PATH, 'w') as f:
        json.dump(data, f)
    return data


def get_weekly_player_stats(year, week, force_refresh=False):
    file_path = STATS_CACHE_PATH.format(year=year, week=week)
    if not force_refresh and os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
        
    url = f"https://api.sleeper.app/v1/stats/nfl/regular/{year}/{week}"
    data = requests.get(url).json()
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return data

# ----- Analysis -----
def build_team_lookup(league_id):
    users = get_users(league_id)
    rosters = get_rosters(league_id)
    user_id_to_name = {u['user_id']: u['display_name'] for u in users}
    team_map = {}
    for r in rosters:
        owner_id = r['owner_id']
        team_id = r['roster_id']
        team_map[team_id] = user_id_to_name.get(owner_id, f"Team {team_id}")
    return team_map

def get_all_team_matchups(league_id, team_map, player_map, weeks):
    matchups_by_team = {team: [{}] * weeks for team in team_map.values()}
    for week in range(1, weeks + 1):
        match_id_to_teams_involved = {}
        matchups = get_matchups(league_id, week)
        
        for team in matchups:
            team_id = team_map.get(team['roster_id'], f"T{team['roster_id']}")
            matchup_id = team.get('matchup_id')
            if matchup_id is not None:
                match_id_to_teams_involved.setdefault(matchup_id, []).append((team_id, team))

            
        for matchup in match_id_to_teams_involved.values():
            if len(matchup) == 2:
                (team_one_id, team_one), (team_two_id, team_two) = matchup
                team_one_points = team_one.get('points', 0)
                team_two_points = team_two.get('points', 0)
                team_one_max_points = calculate_max_points(team_one.get("players_points", {}), player_map)
                team_two_max_points = calculate_max_points(team_two.get("players_points", {}), player_map)
                matchups_by_team[team_one_id][week-1] = {
                    "opp": team_two_id,
                    "points_for": team_one_points,
                    "points_against": team_two_points,
                    "margin": team_one_points - team_two_points,
                    "result": 'W' if team_one_points > team_two_points else 'L' if team_one_points < team_two_points else 'D',
                    "max_points": team_one_max_points,
                    "opp_max_points": team_two_max_points
                }
                matchups_by_team[team_two_id][week-1] = {
                    "opp": team_one_id,
                    "points_for": team_two_points,
                    "points_against": team_one_points,
                    "margin": team_two_points - team_one_points,
                    "result": 'W' if team_two_points > team_one_points else 'L' if team_two_points < team_one_points else 'D',
                    "max_points": team_two_max_points,
                    "opp_max_points": team_one_max_points
                }
            else:
                for team, team_data in matchup:
                    matchups_by_team[team][week-1] = {
                        "opp": None,
                        "points_for": 0,
                        "points_against": 0,
                        "margin": 0,
                        "result": None,
                        "max_points": calculate_max_points(team_data.get("players_points", {}), player_map)
                    }
    return matchups_by_team

def calculate_max_points(players_points, player_map):
    lineup = {
        "QB": [],
        "RB": [],
        "WR": [],
        "TE": [],
        "WR/RB/TE": [],
        "WR/RB/TE/QB": []
    }
    limits = {
        "QB": 1,
        "RB": 2,
        "WR": 3,
        "TE": 1,
        "WR/RB/TE": 2,
        "WR/RB/TE/QB": 1
    }
    starter_limit = sum(limits.values())

    sorted_players = sorted(
        players_points.items(),
        key=lambda x: x[1], # sort by points
        reverse=True
    )

    total = 0.0
    starter_count = 0
    for player_id, points in sorted_players:
        position = player_map.get(player_id, {}).get("position")
        if not position:
            continue

        for slot in ["QB", "RB", "WR", "TE", "WR/RB/TE", "WR/RB/TE/QB"]:
            if position not in slot:
                continue
            if len(lineup[slot]) >= limits[slot]:
                continue
            lineup[slot].append(player_id)
            total += points
            starter_count += 1
            break

        if starter_count == starter_limit:
            break

    return round(total, 2)

def get_roster_stats(league_id, team_map, weeks, year):
    roster_stats_by_team = { 
        team: { 
            "players" : [],
            "starts" : {},
            "appearances" : {},
            "start_points": {},
            "total_points": {}
            } 
        for team in team_map.values() 
    }
    for week in range(1, weeks + 1):
        matchups = get_matchups(league_id, week)
        weekly_stats = get_weekly_player_stats(year, week)

        for team in matchups:
            team_id = team_map.get(team['roster_id'], f"T{team['roster_id']}")
            team_stats = roster_stats_by_team[team_id]

            starters = team.get('starters', [])
            players_points = team.get('players_points', {})

            for player_id, points in players_points.items():
                if player_id not in team_stats["players"]:
                    team_stats["players"].append(player_id)

                player_week_stats = weekly_stats.get(player_id, {})
                player_played = player_week_stats.get("gp", 0) > 0
                if player_played:
                    team_stats["appearances"][player_id] = team_stats["appearances"].get(player_id, 0) + 1
                    team_stats["total_points"][player_id] = team_stats["total_points"].get(player_id, 0) + points

                if player_id in starters:
                    team_stats["starts"][player_id] = team_stats["starts"].get(player_id, 0) + 1
                    team_stats["start_points"][player_id] = team_stats["start_points"].get(player_id, 0) + points
                
    
    return roster_stats_by_team

def enrich_starter_stats(starters_by_team, player_map):
    enriched = {}
    for team, stats in starters_by_team.items():
        players = []
        for player_id in stats["players"]:
            starts = stats["starts"].get(player_id, 0)
            appearances = stats["appearances"].get(player_id, 0)
            start_points = stats["start_points"].get(player_id, 0.0)
            total_points = stats["total_points"].get(player_id, 0.0)
            info = player_map.get(player_id, {})
            ppgs =  round(start_points / starts, 2) if starts > 0 else 0.0
            ppg = round(total_points / appearances, 2) if appearances > 0 else 0.0
            ppg_diff = round(ppgs - ppg , 2) if starts > 0 else 0.0
            players.append({
                "id": player_id,
                "name": info.get("full_name", f"Player {player_id}"),
                "position": info.get("position", "?"),
                "nfl_team": info.get("team", "?"),
                "age": info.get("age", "?"),
                "years_exp": info.get("years_exp", "?"),
                "starts": starts,
                "games_played": appearances,
                "start_points": round(start_points, 2),
                "ppgs": ppgs,
                "total_points": round(total_points, 2),
                "ppg": ppg,
                "ppg_diff": ppg_diff
            })
        
        # Sort by total points descending
        players.sort(key=lambda p: p["start_points"], reverse=True)
        enriched[team] = players
    
    return enriched

def get_season_stats_by_team(matchups_by_team):
    weeks = len(next(iter(matchups_by_team.values())))
    season_stats_by_team = {team: {
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "points_for": 0,
        "points_against": 0,
    } for team in matchups_by_team}
    for team in matchups_by_team:
        for week in matchups_by_team[team]:
            if week["result"] == 'W':
                season_stats_by_team[team]["wins"] += 1
            elif week["result"] == 'L':
                season_stats_by_team[team]["losses"] += 1
            elif week["result"] == 'D':
                season_stats_by_team[team]["draws"] += 1
            season_stats_by_team[team]["points_for"] += week["points_for"]
            season_stats_by_team[team]["points_against"] += week["points_against"]

    for team in season_stats_by_team:
        stats = season_stats_by_team[team]
        stats["win %"] = 100 * (stats["wins"] + 0.5 * stats["draws"]) / len(matchups_by_team[team])

    for team in matchups_by_team:
        opp_wins = 0
        opp_points = 0
        opp_opp_wins = 0
        opp_opp_points = 0
        for week in matchups_by_team[team]:
            opp_wins += season_stats_by_team[week["opp"]]["wins"]
            opp_wins += 0.5 * season_stats_by_team[week["opp"]]["draws"]
            opp_points += season_stats_by_team[week["opp"]]["points_for"]
            for opp_week in matchups_by_team[week["opp"]]:
                opp_opp_wins += season_stats_by_team[opp_week["opp"]]["wins"]
                opp_opp_wins += 0.5 * season_stats_by_team[opp_week["opp"]]["draws"]
                opp_opp_points += season_stats_by_team[opp_week["opp"]]["points_for"]
            opp_opp_wins = (
                opp_opp_wins
                - season_stats_by_team[week["opp"]]["losses"]
                - 0.5 * season_stats_by_team[week["opp"]]["draws"]
            )
            opp_opp_points = (
                opp_opp_points
                - season_stats_by_team[week["opp"]]["points_against"]
            )
        season_stats_by_team[team]["opp_wins"] = (
            opp_wins # all the wins opp had
            - season_stats_by_team[team]["losses"] # only count wins they had against other teams
            - 0.5 * season_stats_by_team[team]["draws"] # ignore draws against the team being analyzed as well
        )
        season_stats_by_team[team]["opp_points"] = (
            # ignore points against the team being analyzed when counting
            # points scored by other teams
            opp_points - season_stats_by_team[team]["points_against"]
        )
        season_stats_by_team[team]["opp_opp_wins"] = opp_opp_wins
        season_stats_by_team[team]["opp_opp_points"] = opp_opp_points

    league_total_points = sum(stats["points_for"] for stats in season_stats_by_team.values()) 
    league_average_points = league_total_points / len(season_stats_by_team)

    for team in season_stats_by_team:
        stats = season_stats_by_team[team]
        stats["points_for_normalized"] = 100 *  stats["points_for"] / league_average_points
        stats["points_against_normalized"] = 100 * stats["points_against"] / league_average_points
        stats["opp win %"] = 100 * stats["opp_wins"] / (weeks * (weeks - 1))
        stats["opp opp win %"] = 100 * stats["opp_opp_wins"] / (weeks * weeks * (weeks - 1))
        stats["win % sos"] = (2 * stats["opp win %"] + stats["opp opp win %"]) / 3
        stats["opp_points_normalized"] = 100 * stats["opp_points"] / (league_average_points * (weeks - 1))
        stats["opp_opp_points_normalized"] = 100 *  stats["opp_opp_points"] / (league_average_points * weeks * (weeks - 1))
        stats["luck_factor"] = stats["opp_points_normalized"] - stats["points_against_normalized"]

    return season_stats_by_team