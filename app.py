import streamlit as st
import os

# --- KESİN ÇÖZÜM KURULUM BLOĞU ---
try:
    import nba_api
except ImportError:
    os.system("pip install nba_api pandas plotly")
    st.rerun()

import pandas as pd
import analyzer
import config
import plotly.graph_objects as go

st.set_page_config(page_title="NBA Trade Analyzer", layout="wide")

st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    .stDataFrame {font-size: 1.1rem;}
    .player-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-bottom: 10px;
        border: 1px solid #444;
    }
    .player-name {font-weight: bold; font-size: 14px; margin-top: 5px; color: white;}
    .game-badge {font-size: 11px; color: #aaa; margin-bottom: 5px;}
    .badge-container {display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; margin-top: 5px;}
    .badge {font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: white;}
    .badge-scorer {background-color: #d63031;} 
    .badge-shooter {background-color: #0984e3;}
    .badge-wall {background-color: #6c5ce7;}
    .badge-thief {background-color: #e17055;}
    .badge-dimer {background-color: #00b894;}
    .badge-glass {background-color: #fdcb6e; color: black;}
    .intro-box {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 25px;
        font-style: italic;
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏀 NBA Fantasy Trade Analyzer")

st.markdown("""
<div class="intro-box">
    "Bu sayfa değerli ligimizin değerli komisyonerlerinin takaslardaki farkları daha net şekilde görebilmesi ve daha az efor sarf etmeleri için oluşturulmuştur. Umarım ki yardımı dokunur."
</div>
""", unsafe_allow_html=True)

if 'team_a_package' not in st.session_state: st.session_state.team_a_package = []
if 'team_b_package' not in st.session_state: st.session_state.team_b_package = []

@st.cache_data
def load_nba_teams():
    teams = analyzer.get_all_nba_teams()
    return {t['full_name']: t['id'] for t in teams}

nba_teams_dict = load_nba_teams()
team_names = sorted(list(nba_teams_dict.keys()))

st.sidebar.header("🛠️ Ayarlar")
analysis_mode = st.sidebar.radio("Analiz Aralığı:", ("Sezon Geneli", "Son 30 Gün"), index=1)
mode_code = 'LAST30' if analysis_mode == "Son 30 Gün" else 'SEASON'

st.sidebar.divider()
st.sidebar.markdown("### 🟢 Takım A (Gidenler)")
team_a_select = st.sidebar.selectbox("Takım Seç (A)", options=team_names, key="sel_a")
roster_a = analyzer.get_team_roster(nba_teams_dict[team_a_select])
player_to_add_a = st.sidebar.selectbox("Oyuncu Seç:", options=roster_a, key="player_a")

if st.sidebar.button("➕ Listeye Ekle (A)", key="btn_add_a"):
    if player_to_add_a not in st.session_state.team_a_package:
        st.session_state.team_a_package.append(player_to_add_a)
        st.rerun()

st.sidebar.markdown("**📦 Paket A İçeriği:**")
if st.session_state.team_a_package:
    for p in st.session_state.team_a_package: st.sidebar.markdown(f"- {p}")
    remove_player_a = st.sidebar.selectbox("Çıkarılacak:", options=["Seçiniz..."]+st.session_state.team_a_package, key="rem_sel_a")
    if st.sidebar.button("🗑️ Çıkar (A)"):
        if remove_player_a != "Seçiniz...":
            st.session_state.team_a_package.remove(remove_player_a)
            st.rerun()
    if st.sidebar.button("❌ Hepsini Sil (A)"):
        st.session_state.team_a_package = []
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔵 Takım B (Gelenler)")
team_b_select = st.sidebar.selectbox("Takım Seç (B)", options=team_names, index=1, key="sel_b")
roster_b = analyzer.get_team_roster(nba_teams_dict[team_b_select])
player_to_add_b = st.sidebar.selectbox("Oyuncu Seç:", options=roster_b, key="player_b")

if st.sidebar.button("➕ Listeye Ekle (B)", key="btn_add_b"):
    if player_to_add_b not in st.session_state.team_b_package:
        st.session_state.team_b_package.append(player_to_add_b)
        st.rerun()

st.sidebar.markdown("**📦 Paket B İçeriği:**")
if st.session_state.team_b_package:
    for p in st.session_state.team_b_package: st.sidebar.markdown(f"- {p}")
    remove_player_b = st.sidebar.selectbox("Çıkarılacak:", options=["Seçiniz..."]+st.session_state.team_b_package, key="rem_sel_b")
    if st.sidebar.button("🗑️ Çıkar (B)"):
        if remove_player_b != "Seçiniz...":
            st.session_state.team_b_package.remove(remove_player_b)
            st.rerun()

with st.sidebar.expander("🚫 Punt Stratejisi"):
    punt_cats = []
    cats_list = ['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    for c in cats_list:
        if st.checkbox(f"Punt {c}"): punt_cats.append(c)

def get_badges_html(stats):
    badges = []
    if stats['PTS'] >= 24.0: badges.append(f"<span class='badge badge-scorer'>🔥 {stats['PTS']:.0f} PTS</span>")
    if stats['3PTM'] >= 3.5: badges.append(f"<span class='badge badge-shooter'>🎯 {stats['3PTM']:.1f} 3P</span>")
    if stats['BLK'] >= 1.8: badges.append(f"<span class='badge badge-wall'>🛡️ {stats['BLK']:.1f} BLK</span>")
    if stats['AST'] >= 8.0: badges.append(f"<span class='badge badge-dimer'>🎩 {stats['AST']:.1f} AST</span>")
    if stats['REB'] >= 10.0: badges.append(f"<span class='badge badge-glass'>🦍 {stats['REB']:.0f} REB</span>")
    return "".join(badges)

if st.sidebar.button("ANALİZ ET", type="primary"):
    if not st.session_state.team_a_package or not st.session_state.team_b_package:
        st.error("Her iki tarafa da oyuncu ekle kral!")
    else:
        with st.spinner('NBA Verileri Çekiliyor...'):
            stats_a, score_a, players_a, missing_a = analyzer.get_combined_stats(st.session_state.team_a_package, mode_code)
            stats_b, score_b, players_b, missing_b = analyzer.get_combined_stats(st.session_state.team_b_package, mode_code)

            c1, c2 = st.columns(2)
            for idx, (p_list, title, color) in enumerate([(players_a, "GIDENLER", "#1f77b4"), (players_b, "GELENLER", "#ff7f0e")]):
                with [c1, c2][idx]:
                    st.markdown(f"<h3 style='text-align:center; color:{color}'>{title}</h3>", unsafe_allow_html=True)
                    cols = st.columns(min(len(p_list), 4))
                    for i, p in enumerate(p_list):
                        with cols[i % 4]:
                            st.markdown(f'<div class="player-card"><img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{p["id"]}.png" style="width:100%"><div class="player-name">{p["name"]}</div><div class="badge-container">{get_badges_html(p["stats"])}</div></div>', unsafe_allow_html=True)

            st.divider()
            st.subheader("📊 Karşılaştırmalı Tablo")
            data = []
            for cat in cats_list:
                val_a, val_b = stats_a.get(cat, 0), stats_b.get(cat, 0)
                if cat == 'FG%':
                    str_a = f"%{val_a*100:.1f} ({stats_a['FGM']:.1f}/{stats_a['FGA']:.1f})"
                    str_b = f"%{val_b*100:.1f} ({stats_b['FGM']:.1f}/{stats_b['FGA']:.1f})"
                elif cat == 'FT%':
                    str_a = f"%{val_a*100:.1f} ({stats_a['FTM']:.1f}/{stats_a['FTA']:.1f})"
                    str_b = f"%{val_b*100:.1f} ({stats_b['FTM']:.1f}/{stats_b['FTA']:.1f})"
                else:
                    str_a, str_b = f"{val_a:.1f}", f"{val_b:.1f}"
                
                win = "Takım A" if (val_a > val_b if cat != 'TOV' else val_a < val_b) else "Takım B"
                if cat in punt_cats: win = "🚫 PUNT"
                data.append({'Kategori': cat, 'Takım A': str_a, 'Takım B': str_b, 'Kazanan': win})
            
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            st.info(f"💡 Takas Dengesi: Takım A ({score_a:.1f} Puan) vs Takım B ({score_b:.1f} Puan)")
