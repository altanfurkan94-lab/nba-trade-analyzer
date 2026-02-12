from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, playerdashboardbygeneralsplits
import pandas as pd
import time

def get_all_nba_teams():
    return teams.get_teams()

def get_team_roster(team_id):
    from nba_api.stats.endpoints import commonteamroster
    roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    return roster['PLAYER'].tolist()

def get_player_stats(player_name, mode='LAST30'):
    try:
        search = players.find_players_by_full_name(player_name)
        if not search: return None
        p_id = search[0]['id']
        
        if mode == 'SEASON':
            stats = playercareerstats.PlayerCareerStats(player_id=p_id).get_data_frames()[0]
            latest = stats.iloc[-1]
            gp = float(latest['GP'])
            return {
                'id': p_id,
                'name': player_name,
                'games': int(gp),
                'stats': {
                    'FG%': float(latest['FG_PCT']),
                    'FGM': float(latest['FGM']) / gp,
                    'FGA': float(latest['FGA']) / gp,
                    'FT%': float(latest['FT_PCT']),
                    'FTM': float(latest['FTM']) / gp,
                    'FTA': float(latest['FTA']) / gp,
                    '3PTM': float(latest['FG3M']) / gp,
                    'PTS': float(latest['PTS']) / gp,
                    'REB': float(latest['REB']) / gp,
                    'AST': float(latest['AST']) / gp,
                    'STL': float(latest['STL']) / gp,
                    'BLK': float(latest['BLK']) / gp,
                    'TOV': float(latest['TOV']) / gp
                }
            }
        else:
            dash = playerdashboardbygeneralsplits.PlayerDashboardByGeneralSplits(
                player_id=p_id, last_n_days=30, per_mode_detailed='PerGame'
            ).get_data_frames()[0]
            if dash.empty: return None
            latest = dash.iloc[0]
            return {
                'id': p_id,
                'name': player_name,
                'games': int(latest['GP']),
                'stats': {
                    'FG%': float(latest['FG_PCT']),
                    'FGM': float(latest['FGM']),
                    'FGA': float(latest['FGA']),
                    'FT%': float(latest['FT_PCT']),
                    'FTM': float(latest['FTM']),
                    'FTA': float(latest['FTA']),
                    '3PTM': float(latest['FG3M']),
                    'PTS': float(latest['PTS']),
                    'REB': float(latest['REB']),
                    'AST': float(latest['AST']),
                    'STL': float(latest['STL']),
                    'BLK': float(latest['BLK']),
                    'TOV': float(latest['TOV'])
                }
            }
    except:
        return None

def get_combined_stats(player_names, mode='LAST30'):
    all_stats = []
    missing = []
    for name in player_names:
        s = get_player_stats(name, mode)
        if s: all_stats.append(s)
        else: missing.append(name)
        time.sleep(0.6) # NBA sunucularını yormayalım
    
    if not all_stats: return {}, 0, [], missing
    
    cats = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    combined = {cat: 0 for cat in cats}
    for p in all_stats:
        for cat in cats:
            combined[cat] += p['stats'][cat]
    
    # Yüzdeleri isabet/deneme üzerinden tekrar hesaplıyoruz (daha doğru sonuç verir)
    combined['FG%'] = combined['FGM'] / combined['FGA'] if combined['FGA'] > 0 else 0
    combined['FT%'] = combined['FTM'] / combined['FTA'] if combined['FTA'] > 0 else 0
    
    score = (combined['PTS'] * 1.0 + combined['REB'] * 1.2 + combined['AST'] * 1.5 + 
             combined['STL'] * 3 + combined['BLK'] * 3 - combined['TOV'] * 2)
    
    return combined, score, all_stats, missing
