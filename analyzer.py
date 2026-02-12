from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, playergamelog
import pandas as pd
import time
from datetime import datetime, timedelta

def get_all_nba_teams():
    return teams.get_teams()

def get_team_roster(team_id):
    from nba_api.stats.endpoints import commonteamroster
    roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    return roster['PLAYER'].tolist()

def get_player_stats(player_name, mode='LAST30'):
    try:
        # Oyuncu ID bul
        search = players.find_players_by_full_name(player_name)
        if not search: return None
        p_id = search[0]['id']
        
        # SEZON GENELİ İSE
        if mode == 'SEASON':
            stats = playercareerstats.PlayerCareerStats(player_id=p_id).get_data_frames()[0]
            if stats.empty: return None
            latest = stats.iloc[-1]
            gp = float(latest['GP'])
            if gp == 0: return None
            
            return {
                'id': p_id, 'name': player_name, 'games': int(gp),
                'stats': {
                    'FG%': float(latest['FG_PCT']), 
                    'FGM': float(latest['FGM'])/gp, 'FGA': float(latest['FGA'])/gp,
                    'FT%': float(latest['FT_PCT']), 
                    'FTM': float(latest['FTM'])/gp, 'FTA': float(latest['FTA'])/gp,
                    '3PTM': float(latest['FG3M'])/gp, 'PTS': float(latest['PTS'])/gp, 
                    'REB': float(latest['REB'])/gp, 'AST': float(latest['AST'])/gp, 
                    'STL': float(latest['STL'])/gp, 'BLK': float(latest['BLK'])/gp, 
                    'TOV': float(latest['TOV'])/gp
                }
            }
            
        # SON 30 GÜN İSE (MANUEL HESAPLAMA - KESİN ÇÖZÜM)
        else:
            # Oyuncunun bu sezonki tüm maçlarını çek
            gamelog = playergamelog.PlayerGameLog(player_id=p_id, season='2024-25').get_data_frames()[0]
            
            if gamelog.empty: return None

            # Tarih formatını ayarla
            gamelog['GAME_DATE'] = pd.to_datetime(gamelog['GAME_DATE'], format='%b %d, %Y')
            
            # Bugünden 30 gün öncesini bul
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            # Sadece son 30 gündeki maçları filtrele
            recent_games = gamelog[gamelog['GAME_DATE'] >= thirty_days_ago]
            
            if recent_games.empty: return None
            
            # Ortalamaları al
            gp = len(recent_games)
            mean_stats = recent_games.mean(numeric_only=True)
            
            return {
                'id': p_id, 'name': player_name, 'games': gp,
                'stats': {
                    'FG%': float(mean_stats['FG_PCT']), 
                    'FGM': float(mean_stats['FGM']), 'FGA': float(mean_stats['FGA']),
                    'FT%': float(mean_stats['FT_PCT']), 
                    'FTM': float(mean_stats['FTM']), 'FTA': float(mean_stats['FTA']),
                    '3PTM': float(mean_stats['FG3M']), 'PTS': float(mean_stats['PTS']), 
                    'REB': float(mean_stats['REB']), 'AST': float(mean_stats['AST']), 
                    'STL': float(mean_stats['STL']), 'BLK': float(mean_stats['BLK']), 
                    'TOV': float(mean_stats['TOV'])
                }
            }

    except Exception as e:
        return None

def get_combined_stats(player_names, mode='LAST30'):
    all_stats = []
    missing = []
    
    for name in player_names:
        s = get_player_stats(name, mode)
        if s: all_stats.append(s)
        else: missing.append(name)
        time.sleep(0.3)
    
    if not all_stats: return {}, 0, [], missing
    
    cats = ['FGM', 'FGA', 'FTM', 'FTA', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    combined = {cat: 0 for cat in cats}
    
    for p in all_stats:
        for cat in cats:
            combined[cat] += p['stats'][cat]
    
    # Yüzdeleri isabet/deneme üzerinden tekrar hesapla
    combined['FG%'] = combined['FGM'] / combined['FGA'] if combined['FGA'] > 0 else 0
    combined['FT%'] = combined['FTM'] / combined['FTA'] if combined['FTA'] > 0 else 0
    
    score = (combined['PTS']*1.0 + combined['REB']*1.2 + combined['AST']*1.5 + 
             combined['STL']*3 + combined['BLK']*3 - combined['TOV']*2)
    
    return combined, score, all_stats, missing
