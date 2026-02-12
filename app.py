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

# --- CSS STİL (ESKİ GÜZEL GÖRÜNÜM) ---
st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    .stDataFrame {font-size: 1.1rem;}
    /* Fotoğrafları büyük yapan stil */
    .player-card {
        background-color: #262730; 
        border-radius: 10px; 
        padding: 0px; 
        text-align: center; 
        margin-bottom: 20px; 
        border: 1px solid #444;
        overflow: hidden;
    }
    .player-name {
        font-weight: bold; 
        font-size: 16px; 
        padding: 10px; 
        color: white; 
        background-color: #333;
    }
    .badge-container {display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 5px;}
    .badge {font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: white;}
    .badge-scorer {background-color: #d63031;} 
    .badge-shooter {background-color: #0984e3;}
    .badge-wall {background-color: #6c5ce7;}
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
    "Bu sayfa değerli ligimizin değerli üyelerinin ve komisyonerlerinin takaslardaki farkları daha net şekilde görebilmesi için oluşturulmuştur. Umarım ki yardımı dokunur."
</div>
""", unsafe_allow_html=True)

# Session State
if 'team_a_package' not in st.session_state: st.session_state.team_a_package = []
if 'team_b_package' not in st.session_state: st.session_state.team_b_package = []

@st.cache_data
def load_nba_teams():
    teams = analyzer.get_all_nba_teams()
    return {t['full_name']: t['id'] for t in teams}

nba_teams_dict = load_nba_teams()
team_names = sorted(list(nba_teams_dict.keys()))

# --- SIDEBAR (ESKİ KUTUCUKLU SİSTEM) ---
st.sidebar.header("🛠️ Ayarlar")
analysis_mode = st.sidebar.radio("Analiz Aralığı:", ("Sezon Geneli", "Son 30 Gün"), index=1)
mode_code = 'LAST30' if analysis_mode == "Son 30 Gün" else 'SEASON'

st.sidebar.divider()

# TAKIM A (MULTISELECT)
st.sidebar.markdown("### 🟢 Takım A (Gidenler)")
team_a_select = st.sidebar.selectbox("Takım Seç (A)", team_names, key="sel_a")
roster_a = analyzer.get_team_roster(nba_teams_dict[team_a_select])
# İşte o eski güzel kutucuklu yapı:
team_a_package = st.sidebar.multiselect("Oyuncuları Seç (A):", roster_a, key="multi_a")

st.sidebar.markdown("---")

# TAKIM B (MULTISELECT)
st.sidebar.markdown("### 🔵 Takım B (Gelenler)")
team_b_select = st.sidebar.selectbox("Takım Seç (B)", team_names, index=1, key="sel_b")
roster_b = analyzer.get_team_roster(nba_teams_dict[team_b_select])
# İşte o eski güzel kutucuklu yapı:
team_b_package = st.sidebar.multiselect("Oyuncuları Seç (B):", roster_b, key="multi_b")

st.sidebar.divider()

# Punt
with st.sidebar.expander("🚫 Punt Stratejisi"):
    punt_cats = []
    cats = ['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    c1, c2 = st.columns(2)
    for c in cats:
        if st.checkbox(f"Punt {c}"): punt_cats.append(c)

# Rozet Fonksiyonu
def get_badges_html(stats):
    b = []
    if stats['PTS']>=24: b.append(f"<span class='badge badge-scorer'>🔥 {stats['PTS']:.0f} PTS</span>")
    if stats['3PTM']>=3.5: b.append(f"<span class='badge badge-shooter'>🎯 {stats['3PTM']:.1f} 3P</span>")
    if stats['BLK']>=1.8: b.append(f"<span class='badge badge-wall'>🛡️ {stats['BLK']:.1f} BLK</span>")
    if stats['AST']>=8.0: b.append(f"<span class='badge badge-dimer'>🎩 {stats['AST']:.1f} AST</span>")
    if stats['REB']>=10.0: b.append(f"<span class='badge badge-glass'>🦍 {stats['REB']:.0f} REB</span>")
    return "".join(b)

# Grafikler
def plot_radar_chart(stats_a, stats_b, categories):
    vals_a, vals_b = [], []
    valid_cats = [c for c in categories if c not in punt_cats]
    for cat in valid_cats:
        val_a, val_b = stats_a.get(cat, 0), stats_b.get(cat, 0)
        if cat == 'TOV':
            total = val_a + val_b
            if total == 0: v_a, v_b = 0.5, 0.5
            else: v_a, v_b = 1-(val_a/total), 1-(val_b/total)
        else:
            total = val_a + val_b
            if total == 0: v_a, v_b = 0, 0
            else: v_a, v_b = val_a/total, val_b/total
        vals_a.append(v_a); vals_b.append(v_b)
    if vals_a: vals_a.append(vals_a[0]); vals_b.append(vals_b[0]); valid_cats.append(valid_cats[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals_a, theta=valid_cats, fill='toself', name='Takım A', line_color='#1f77b4'))
    fig.add_trace(go.Scatterpolar(r=vals_b, theta=valid_cats, fill='toself', name='Takım B', line_color='#ff7f0e'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False)), showlegend=True, margin=dict(l=40,r=40,t=20,b=20), height=300, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

def plot_gauge_chart(score_a, score_b):
    diff = score_a - score_b
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta", value = diff,
        title = {'text': "Takas Dengesi (Puan)", 'font': {'size': 18, 'color': 'white'}},
        delta = {'reference': 0, 'increasing': {'color': "#1f77b4"}, 'decreasing': {'color': "#ff7f0e"}},
        gauge = {
            'axis': {'range': [-30, 30], 'tickcolor': "white"},
            'bar': {'color': "rgba(0,0,0,0)"},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [{'range': [-30, -5], 'color': '#ff7f0e'}, {'range': [-5, 5], 'color': '#555'}, {'range': [5, 30], 'color': '#1f77b4'}]
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20,r=20,t=30,b=20), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

# --- ANA İŞLEM (ANALİZ ET) ---
if st.sidebar.button("ANALİZ ET", type="primary"):
    if not team_a_package or not team_b_package:
        st.error("Lütfen her iki taraftan da oyuncu seç kral!")
    else:
        with st.spinner(f'{analysis_mode} verileri analiz ediliyor...'):
            stats_a, score_a, players_a, missing_a = analyzer.get_combined_stats(team_a_package, mode=mode_code)
            stats_b, score_b, players_b, missing_b = analyzer.get_combined_stats(team_b_package, mode_code)

            # 1. KARTLAR (BÜYÜK FOTOĞRAFLI)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<h3 style='text-align:center; color:#1f77b4'>GIDENLER (Takım A)</h3>", unsafe_allow_html=True)
                cols = st.columns(len(players_a) if len(players_a)>0 else 1)
                for i, p in enumerate(players_a):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="player-card">
                            <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{p['id']}.png" style="width:100%">
                            <div class="player-name">{p['name']}</div>
                            <div class="badge-container">{get_badges_html(p['stats'])}</div>
                        </div>""", unsafe_allow_html=True)
                if missing_a: st.error(f"⚠️ Veri Yok: {', '.join(missing_a)}")

            with c2:
                st.markdown(f"<h3 style='text-align:center; color:#ff7f0e'>GELENLER (Takım B)</h3>", unsafe_allow_html=True)
                cols = st.columns(len(players_b) if len(players_b)>0 else 1)
                for i, p in enumerate(players_b):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="player-card">
                            <img src="https://cdn.nba.com/headshots/nba/latest/1040x760/{p['id']}.png" style="width:100%">
                            <div class="player-name">{p['name']}</div>
                            <div class="badge-container">{get_badges_html(p['stats'])}</div>
                        </div>""", unsafe_allow_html=True)
                if missing_b: st.error(f"⚠️ Veri Yok: {', '.join(missing_b)}")
            
            st.divider()
            
            # 2. GRAFİKLER
            g1, g2 = st.columns([1,1.5])
            with g1: st.plotly_chart(plot_gauge_chart(score_a, score_b), use_container_width=True)
            with g2: st.plotly_chart(plot_radar_chart(stats_a, stats_b, cats), use_container_width=True)
            
            # 3. NET DEĞİŞİM (+/-)
            st.subheader("📈 Net Değişim")
            delta_cols = st.columns(9)
            wins_a, wins_b = 0, 0
            for idx, cat in enumerate(cats):
                if cat in punt_cats: continue
                val_a, val_b = stats_a.get(cat, 0), stats_b.get(cat, 0)
                diff = val_a - val_b
                # TOV için farkı tersine çevir (daha az TOV iyidir)
                if cat == 'TOV': diff = val_b - val_a # Bu sadece ekranda kırmızı/yeşil göstermek için
                
                fmt_diff = f"{val_a-val_b:+.1f}" # Değeri normal hesapla
                if cat in ['FG%', 'FT%']: fmt_diff = f"{(val_a-val_b)*100:+.1f}%"
                
                # Renk mantığı
                is_pos = (val_a > val_b) if cat != 'TOV' else (val_a < val_b)
                
                with delta_cols[idx]:
                    st.metric(label=cat, value=fmt_diff, delta=fmt_diff, delta_color="normal" if is_pos else "inverse")

            st.divider()

            # 4. TABLO (İSABETLER EKLENDİ)
            ct, cc = st.columns([1.5, 0.1]) # Tabloyu genişlettim
            data = []
            for cat in cats:
                is_punted = cat in punt_cats
                val_a, val_b = stats_a.get(cat, 0), stats_b.get(cat, 0)
                
                # --- İSABET/DENEME BURADA ---
                if cat == 'FG%':
                    str_a = f"%{val_a*100:.1f} ({stats_a.get('FGM',0):.1f}/{stats_a.get('FGA',0):.1f})"
                    str_b = f"%{val_b*100:.1f} ({stats_b.get('FGM',0):.1f}/{stats_b.get('FGA',0):.1f})"
                elif cat == 'FT%':
                    str_a = f"%{val_a*100:.1f} ({stats_a.get('FTM',0):.1f}/{stats_a.get('FTA',0):.1f})"
                    str_b = f"%{val_b*100:.1f} ({stats_b.get('FTM',0):.1f}/{stats_b.get('FTA',0):.1f})"
                else:
                    str_a, str_b = f"{val_a:.1f}", f"{val_b:.1f}"
                # ---------------------------

                if not is_punted:
                    if cat == 'TOV': winner = "Takım A" if val_a < val_b else "Takım B"
                    else: winner = "Takım A" if val_a > val_b else "Takım B"
                    if winner == "Takım A": wins_a +=1
                    else: wins_b += 1
                else: winner = "🚫 PUNT"
                data.append({'Kategori': cat, 'Takım A': str_a, 'Takım B': str_b, 'Kazanan': winner})

            with ct:
                st.subheader("📊 İstatistikler")
                def color_rows(row):
                    if row['Kazanan'] == 'Takım A': return ['background-color: #1f77b4; color: white']*4
                    elif row['Kazanan'] == 'Takım B': return ['background-color: #d63031; color: white']*4
                    elif row['Kazanan'] == '🚫 PUNT': return ['color: gray; text-decoration: line-through']*4
                    return ['']*4
                st.dataframe(pd.DataFrame(data).style.apply(color_rows, axis=1), use_container_width=True, hide_index=True, height=380)

            st.markdown("### 🧠 Sonuç")
            if wins_a > wins_b: st.success(f"✅ **TAKIM A KAZANIR** ({wins_a} - {wins_b})")
            elif wins_b > wins_a: st.error(f"✅ **TAKIM B KAZANIR** ({wins_b} - {wins_a})")
            else: st.warning(f"⚖️ **BERABERLİK** ({wins_a} - {wins_b})")
