import streamlit as st
import os

# --- ARKA KAPI KURULUMU ---
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

# --- CSS STİL (Görsellik Geri Geldi) ---
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
    .badge-container {display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; margin-top: 5px;}
    .badge {font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: white;}
    .badge-scorer {background-color: #d63031;} 
    .badge-shooter {background-color: #0984e3;}
    .badge-wall {background-color: #6c5ce7;}
    .badge-dimer {background-color: #00b894;}
    .badge-glass {background-color: #fdcb6e; color: black;}
    .intro-box {
        background-color: #262730; padding: 15px; border-radius: 8px;
        border-left: 5px solid #ff4b4b; margin-bottom: 25px; font-style: italic; color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏀 NBA Fantasy Trade Analyzer")

st.markdown('<div class="intro-box">"Bu sayfa değerli ligimizin değerli komisyonerlerinin takaslardaki farkları daha net görebilmesi için oluşturulmuştur."</div>', unsafe_allow_html=True)

if 'team_a_package' not in st.session_state: st.session_state.team_a_package = []
if 'team_b_package' not in st.session_state: st.session_state.team_b_package = []

@st.cache_data
def load_nba_teams():
    return {t['full_name']: t['id'] for t in analyzer.get_all_nba_teams()}

nba_teams_dict = load_nba_teams()
team_names = sorted(list(nba_teams_dict.keys()))

# --- SIDEBAR ---
st.sidebar.header("🛠️ Ayarlar")
analysis_mode = st.sidebar.radio("Analiz Aralığı:", ("Sezon Geneli", "Son 30 Gün"), index=1)
mode_code = 'LAST30' if analysis_mode == "Son 30 Gün" else 'SEASON'

st.sidebar.divider()
for side, label, key in [('team_a_package', '🟢 Takım A (Gidenler)', 'a'), ('team_b_package', '🔵 Takım B (Gelenler)', 'b')]:
    st.sidebar.markdown(f"### {label}")
    team_sel = st.sidebar.selectbox(f"Takım Seç ({key.upper()})", options=team_names, key=f"sel_{key}")
    roster = analyzer.get_team_roster(nba_teams_dict[team_sel])
    player_add = st.sidebar.selectbox(f"Oyuncu Seç:", options=roster, key=f"p_{key}")
    if st.sidebar.button(f"➕ Ekle ({key.upper()})", key=f"btn_{key}"):
        if player_add not in st.session_state[side]:
            st.session_state[side].append(player_add)
            st.rerun()
    st.sidebar.write(f"Paket: {st.session_state[side]}")
    if st.sidebar.button(f"🗑️ Temizle ({key.upper()})", key=f"clr_{key}"):
        st.session_state[side] = []
        st.rerun()

with st.sidebar.expander("🚫 Punt Stratejisi"):
    punt_cats = []
    cats_list = ['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    for c in cats_list:
        if st.checkbox(f"Punt {c}"): punt_cats.append(c)

# --- GÖRSEL FONKSİYONLAR ---
def plot_radar_chart(stats_a, stats_b, categories):
    vals_a, vals_b = [], []
    valid_cats = [c for c in categories if c not in punt_cats]
    for cat in valid_cats:
        v_a, v_b = stats_a.get(cat, 0), stats_b.get(cat, 0)
        total = v_a + v_b
        if cat == 'TOV':
            res_a = 1-(v_a/total) if total > 0 else 0.5
            res_b = 1-(v_b/total) if total > 0 else 0.5
        else:
            res_a = v_a/total if total > 0 else 0
            res_b = v_b/total if total > 0 else 0
        vals_a.append(res_a); vals_b.append(res_b)
    if vals_a: 
        vals_a.append(vals_a[0]); vals_b.append(vals_b[0]); valid_cats.append(valid_cats[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_a, theta=valid_cats, fill='toself', name='Takım A', line_color='#1f77b4'))
    fig.add_trace(go.Scatterpolar(r=vals_b, theta=valid_cats, fill='toself', name='Takım B', line_color='#ff7f0e'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False)), height=350, margin=dict(l=40,r=40,t=40,b=40), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

def plot_gauge_chart(score_a, score_b):
    diff = score_a - score_b
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = diff,
        delta = {'reference': 0},
        gauge = {'axis': {'range': [-30, 30]}, 'steps': [{'range': [-30, -5], 'color': '#ff7f0e'}, {'range': [5, 30], 'color': '#1f77b4'}], 'bar': {'color': 'white'}}
    ))
    fig.update_layout(height=250, margin=dict(l=20,r=20,t=50,b=20), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

# --- ANA ANALİZ ---
if st.sidebar.button("ANALİZ ET", type="primary"):
    if not st.session_state.team_a_package or not st.session_state.team_b_package:
        st.error("Oyuncuları seç kral!")
    else:
        with st.spinner('NBA Sunucusundan Veriler Çekiliyor...'):
            stats_a, score_a, players_a, _ = analyzer.get_combined_stats(st.session_state.team_a_package, mode_code)
            stats_b, score_b, players_b, _ = analyzer.get_combined_stats(st.session_state.team_b_package, mode_code)

            # Oyuncu Kartları
            c1, c2 = st.columns(2)
            for idx, (p_list, title, color) in enumerate([(players_a, "GIDENLER (A)", "#1f77b4"), (players_b, "GELENLER (B)", "#ff7f0e")]):
                with [c1, c2][idx]:
                    st.markdown(f"<h3 style='text-align:center; color:{color}'>{title}</h3>", unsafe_allow_html=True)
                    cols = st.columns(min(len(p_list), 4))
                    for i, p in enumerate(p_list):
                        with cols[i % 4]:
                            st.markdown(f'<div class="player-card"><img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{p["id"]}.png" style="width:100%"><div class="player-name">{p["name"]}</div></div>', unsafe_allow_html=True)

            st.divider()
            
            # Grafikler
            g1, g2 = st.columns([1, 1.2])
            with g1: st.plotly_chart(plot_gauge_chart(score_a, score_b), use_container_width=True)
            with g2: st.plotly_chart(plot_radar_chart(stats_a, stats_b, cats_list), use_container_width=True)

            # Renkli Tablo (Yeni Formatla)
            st.subheader("📊 İstatistik Detayları")
            data = []
            wins_a, wins_b = 0, 0
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
                
                is_punted = cat in punt_cats
                if not is_punted:
                    if cat == 'TOV': winner = "Takım A" if val_a < val_b else "Takım B"
                    else: winner = "Takım A" if val_a > val_b else "Takım B"
                    if winner == "Takım A": wins_a += 1
                    else: wins_b += 1
                else: winner = "🚫 PUNT"
                data.append({'Kategori': cat, 'Takım A': str_a, 'Takım B': str_b, 'Kazanan': winner})

            def color_rows(row):
                if row['Kazanan'] == 'Takım A': return ['background-color: #1f77b4; color: white']*4
                elif row['Kazanan'] == 'Takım B': return ['background-color: #d63031; color: white']*4
                return ['color: gray; text-decoration: line-through']*4
            
            st.dataframe(pd.DataFrame(data).style.apply(color_rows, axis=1), use_container_width=True, hide_index=True)

            # Sonuç Mesajı
            if wins_a > wins_b: st.success(f"🏆 TAKIM A KAZANIR ({wins_a} - {wins_b})")
            elif wins_b > wins_a: st.error(f"🏆 TAKIM B KAZANIR ({wins_b} - {wins_a})")
            else: st.warning(f"⚖️ BERABERLİK ({wins_a} - {wins_b})")
