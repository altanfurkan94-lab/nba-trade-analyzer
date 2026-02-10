from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playergamelog, commonteamroster
import unicodedata
import config
import time
from datetime import datetime, timedelta
import pandas as pd

# Önbellekler
player_cache = {}
roster_cache = {}

def normalize_text(text):
    text = text.lower()
    normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return normalized

def get_all_nba_teams():
    return teams.get_teams()

def get_team_roster(team_id):
    if team_id in roster_cache: return roster_cache[team_id]
    try:
        roster = commonteamroster.CommonTeamRoster(team_id=team_id, season=config.CURRENT_SEASON_ID)
        df = roster.get_data_frames()[0]
        player_list = df['PLAYER'].tolist()
        roster_cache[team_id] = player_list
        return player_list
    except Exception as e:
        return []

def get_player_id(name_input):
    if name_input in player_cache: return player_cache[name_input]
    active_players = players.get_active_players()
    search_key = normalize_text(name_input)
    best_match = None
    for p in active_players:
        db_name_clean = normalize_text(p['full_name'])
        if db_name_clean == search_key:
            player_cache[name_input] = p['id']
            return p['id']
        if search_key in db_name_clean:
            if best_match is None: best_match = p['id']
    if best_match:
        player_cache[name_input] = best_match
        return best_match
    return None

def get_combined_stats(player_names_list, mode='SEASON'):
    total_stats = {
        'PTS': 0, 'REB': 0, 'AST': 0, 'STL': 0, 'BLK': 0, 
        '3PTM': 0, 'TOV': 0, 'FGA': 0, 'FGM': 0, 'FTA': 0, 'FTM': 0
    }
    
    valid_players = [] 
    missing_players = [] 
    
    today = datetime.now()
    cutoff_date = today - timedelta(days=30)

    for name in player_names_list:
        if not name.strip(): continue 
        pid = get_player_id(name)
        if not pid:
            missing_players.append(f"{name} (Bulunamadı)")
            continue
            
        try:
            time.sleep(0.3) 
            gamelog = playergamelog.PlayerGameLog(player_id=pid, season=config.CURRENT_SEASON_ID)
            df = gamelog.get_data_frames()[0]
            
            if df.empty:
                missing_players.append(f"{name} (Veri Yok)")
                continue
            
            working_df = df
            if mode == 'LAST30':
                df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
                df_filtered = df[df['GAME_DATE'] >= cutoff_date]
                if df_filtered.empty:
                    missing_players.append(f"{name} (Son 30 gün boş)")
                    continue
                working_df = df_filtered

            # ORTALAMALAR
            games = len(working_df)
            p_pts = working_df['PTS'].sum() / games
            p_reb = working_df['REB'].sum() / games
            p_ast = working_df['AST'].sum() / games
            p_stl = working_df['STL'].sum() / games
            p_blk = working_df['BLK'].sum() / games
            p_3pt = working_df['FG3M'].sum() / games
            p_tov = working_df['TOV'].sum() / games
            
            # Toplamlara Ekle
            total_stats['PTS'] += p_pts
            total_stats['REB'] += p_reb
            total_stats['AST'] += p_ast
            total_stats['STL'] += p_stl
            total_stats['BLK'] += p_blk
            total_stats['3PTM'] += p_3pt
            total_stats['TOV'] += p_tov
            
            total_stats['FGA'] += working_df['FGA'].sum() / games
            total_stats['FGM'] += working_df['FGM'].sum() / games
            total_stats['FTA'] += working_df['FTA'].sum() / games
            total_stats['FTM'] += working_df['FTM'].sum() / games
            
            real_name = players.find_player_by_id(pid)['full_name']
            
            # --- YENİLİK: Bireysel İstatistikleri Kaydet ---
            # Bu verileri rozet (badge) sistemi için kullanacağız
            player_stats_summary = {
                'PTS': p_pts, 'REB': p_reb, 'AST': p_ast,
                'STL': p_stl, 'BLK': p_blk, '3PTM': p_3pt, 'TOV': p_tov
            }
            
            valid_players.append({
                'name': real_name, 
                'id': pid, 
                'games': games,
                'stats': player_stats_summary
            })
            
        except Exception as e:
            print(f"Hata ({name}): {e}")
            missing_players.append(f"{name} (Hata)")

    if total_stats['FGA'] > 0: total_stats['FG%'] = total_stats['FGM'] / total_stats['FGA']
    else: total_stats['FG%'] = 0.0
        
    if total_stats['FTA'] > 0: total_stats['FT%'] = total_stats['FTM'] / total_stats['FTA']
    else: total_stats['FT%'] = 0.0

    score = 0
    score += total_stats['PTS'] * config.WEIGHTS['PTS']
    score += total_stats['REB'] * config.WEIGHTS['REB']
    score += total_stats['AST'] * config.WEIGHTS['AST']
    score += total_stats['STL'] * config.WEIGHTS['STL']
    score += total_stats['BLK'] * config.WEIGHTS['BLK']
    score += total_stats['3PTM'] * config.WEIGHTS['FG3M']
    score += total_stats['TOV'] * config.WEIGHTS['TOV']
    
    fg_impact = (total_stats['FG%'] - config.LEAGUE_BASE['FG_PCT']) * total_stats['FGA'] * config.PERCENTAGE_WEIGHT
    ft_impact = (total_stats['FT%'] - config.LEAGUE_BASE['FT_PCT']) * total_stats['FTA'] * config.PERCENTAGE_WEIGHT
    score += fg_impact + ft_impact

    return total_stats, round(score, 2), valid_players, missing_players