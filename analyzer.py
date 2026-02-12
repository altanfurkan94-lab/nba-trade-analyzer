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
            return {
                'id': p_id,
                'name': player_name,
                'games': int(latest['GP']),
                'stats': {
                    'FG%': float(latest['FG_PCT']),
                    'FGA': float(latest['FGA']) / float(latest['GP']),
                    'FT%': float(latest['FT_PCT']),
                    'FTA': float(latest['FTA']) / float(latest['GP']),
                    '3PTM': float(latest['FG3M']) / float(latest['GP']),
                    'PTS': float(latest['PTS']) / float(latest['GP']),
                    'REB': float(latest['REB']) / float(latest['GP']),
                    'AST': float(latest['AST']) / float(latest['GP']),
                    'STL': float(latest['STL']) / float(latest['GP']),
                    'BLK': float(latest['BLK']) / float(latest['GP']),
                    'TOV': float(latest['TOV']) / float(latest['GP'])
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
                    'FGA': float(latest['FGA']),
                    'FT%': float(latest['FT_PCT']),
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
        time.sleep(0.5)
    
    if not all_stats: return {}, 0, [], missing
    
    combined = {cat: 0 for cat in ['FG%', 'FGA', 'FT%', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']}
    for p in all_stats:
        for cat in combined:
            combined[cat] += p['stats'][cat]
    
    # Ortalama yüzdeler (Ağırlıklı değil, basit toplam üzerinden)
    combined['FG%'] /= len(all_stats)
    combined['FT%'] /= len(all_stats)
    
    # Basit bir skor hesaplama
    score = (combined['PTS'] * 1.0 + combined['REB'] * 1.2 + combined['AST'] * 1.5 + 
             combined['STL'] * 3 + combined['BLK'] * 3 - combined['TOV'] * 2)
    
    return combined, score, all_stats, missing
