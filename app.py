import streamlit as st
import os

# --- ARKA KAPI KURULUMU (HATA VERMESİN DİYE) ---
try:
    import nba_api
except ImportError:
    os.system("pip install nba_api pandas plotly")
    st.rerun()

import pandas as pd
import analyzer
import plotly.graph_objects as go

st.set_page_config(page_title="NBA Trade Analyzer", layout="wide")

# --- CSS STİL (Eski Güzel Görünüm İçin) ---
st.markdown("""
<style>
    thead tr th:first-child {display:none}
    tbody th {display:none}
    .stDataFrame {font-size: 1.1rem;}
    /* Fotoğrafları büyüten ve ortalayan stil */
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
    .intro-box {
        background-color: #262730; padding: 15px; border-radius: 8px;
        border-left: 5px solid #ff4b4b; margin-bottom: 25px; font-style: italic; color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏀 NBA Fantasy Trade Analyzer")
st.markdown('<div class="intro-box">"Bu sayfa değerli ligimizin değerli komisyonerlerinin takaslardaki farkları daha net görebilmesi için oluşturulmuştur."</div>', unsafe_allow_html=True)

# Session State
if 'init' not in st.session_state: st.session_state.init = True

@st.cache_data
def load_nba_teams():
    return {t['full_name']: t['id'] for t in analyzer.get_all_nba_teams()}

nba_teams_dict = load_nba_teams()
team_names = sorted(list(nba_teams_dict.keys()))

# --- SOL TARAFTAKİ AYARLAR (ESKİ HALİNE DÖNDÜ) ---
st.sidebar.header("🛠️ Ayarlar")
analysis_mode = st.sidebar.radio("Analiz Aralığı:", ("Sezon Geneli", "Son 30 Gün"), index=0)
mode_code = 'LAST30' if analysis_mode == "Son 30 Gün" else 'SEASON'

st.sidebar.divider()

# --- TAKIM A SEÇİMİ (ESKİ MULTISELECT SİSTEMİ) ---
st.sidebar.markdown("### 🟢 Takım A (Gidenler)")
team_a_select = st.sidebar.selectbox("Takım (A)", team_names, key="sel_a")
roster_a = analyzer.get_team_roster(nba_teams_dict[team_a_select])
# İşte o özlediğin kutucuklu yapı:
team_a_package = st.sidebar.multiselect("Oyuncuları Seç:", roster_a, key="multi_a")

st.sidebar.markdown("---")

# --- TAKIM B SEÇİMİ (ESKİ MULTISELECT SİSTEMİ) ---
st.sidebar.markdown("### 🔵 Takım B (Gelenler)")
team_b_select = st.sidebar.selectbox("Takım (B)", team_names, index=1, key="sel_b")
roster_b = analyzer.get_team_roster(nba_teams_dict[team_b_select])
# İşte o özlediğin kutucuklu yapı:
team_b_package = st.sidebar.multiselect("Oyuncuları Seç:", roster_b, key="multi_b")

st.sidebar.divider()

# Punt Ayarları
with st.sidebar.expander("🚫 Punt Stratejisi"):
    punt_cats = []
    cats_list = ['FG%', 'FT%', '3PTM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']
    for c in cats_list:
        if st.checkbox(f"Punt {c}"): punt_cats.append(c)

# --- GRAFİKLER ---
def plot_radar(stats_a, stats_b):
    cats = [c for c in cats_list if c not in punt_cats]
    va, vb = [], []
    for c in cats:
        v1, v2 = stats_a.get(c,0), stats_b.get(c,0)
        tot = v1+v2
        if tot==0: r1, r2 = 0,0
        elif c=='TOV': r1, r2 = 1-(v1/tot), 1-(v2/tot)
        else: r1, r2 = v1/tot, v2/tot
        va.append(r1); vb.append(r2)
    if va: va.append(va[0]); vb.append(vb[0]); cats.append(cats[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=va, theta=cats, fill='toself', name='Takım A', line_color='#1f77b4'))
    fig.add_trace(go.Scatterpolar(r=vb, theta=cats, fill='toself', name='Takım B', line_color='#ff7f0e'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=False)), height=350, margin=dict(t=30,b=30), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

def plot_gauge(sa, sb):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=sa-sb, title={'text':"Güç Farkı"},
        delta={'reference':0},
        gauge={'axis':{'range':[-30,30]}, 'bar':{'color':'white'}, 'steps':[{'range':[-30,-5],'color':'#ff7f0e'},{'range':[5,30],'color':'#1f77b4'}]}
    ))
    fig.update_layout(height=250, margin=dict(t=40,b=10), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    return fig

# --- ANA ANALİZ EKRANI ---
if st.sidebar.button("ANALİZ ET", type="primary"):
    if not team_a_package or not team_b_package:
        st.error("Lütfen her iki takımdan da oyuncu seç kral!")
    else:
        with st.spinner('Veriler Çekiliyor...'):
            stats_a, score_a, players_a, _ = analyzer.get_combined_stats(team_a_package, mode_code)
            stats_b, score_b, players_b, _ = analyzer.get_combined_stats(team_b_package, mode_code)
            
            # 1. OYUNCU FOTOĞRAFLARI (BÜYÜK BOYUT - ESKİ HALİ)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f"<h3 style='text-align:center; color:#1f77b4'>GIDENLER (Takım A)</h3>", unsafe_allow_html=True)
                cols = st.columns(len(players_a))
                for i, p in enumerate(players_a):
                    with cols[i]:
                        st.image(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p['id']}.png", use_container_width=True)
                        st.markdown(f"<div style='text-align:center; font-weight:bold;'>{p['name']}</div>", unsafe_allow_html=True)

            with c2:
                st.markdown(f"<h3 style='text-align:center; color:#ff7f0e'>GELENLER (Takım B)</h3>", unsafe_allow_html=True)
                cols = st.columns(len(players_b))
                for i, p in enumerate(players_b):
                    with cols[i]:
                        st.image(f"https://cdn.nba.com/headshots/nba/latest/1040x760/{p['id']}.png", use_container_width=True)
                        st.markdown(f"<div style='text-align:center; font-weight:bold;'>{p['name']}</div>", unsafe_allow_html=True)
            
            st.divider()

            # 2. GRAFİKLER
            g1, g2 = st.columns([1,1.5])
            with g1: st.plotly_chart(plot_gauge(score_a, score_b), use_container_width=True)
            with g2: st.plotly_chart(plot_radar(stats_a, stats_b), use_container_width=True)

            # 3. NET DEĞİŞİM
            st.subheader("📈 Net Değişim")
            m_cols = st.columns(9)
            for idx, cat in enumerate(cats_list):
                if cat in punt_cats: continue
                val_a = stats_a.get(cat, 0)
                val_b = stats_b.get(cat, 0)
                diff = val_b - val_a 
                if cat == 'TOV': diff = val_a - val_b 
                
                fmt = f"{diff*100:+.1f}%" if cat in ['FG%','FT%'] else f"{diff:+.1f}"
                delta_color = "normal" if diff >= 0 else "inverse"
                with m_cols[idx]:
                    st.metric(label=cat, value=fmt, delta=fmt, delta_color=delta_color)

            st.divider()
            
            # 4. TABLO (TEK YENİLİK BURASI: İSABET/DENEME EKLENDİ)
            st.subheader("📊 Detaylı İstatistikler")
            data = []
            wa, wb = 0, 0
            for c in cats_list:
                v1, v2 = stats_a.get(c,0), stats_b.get(c,0)
                
                # --- YENİ EKLENEN KISIM ---
                if c == 'FG%':
                    s1 = f"%{v1*100:.1f} ({stats_a['FGM']:.1f}/{stats_a['FGA']:.1f})"
                    s2 = f"%{v2*100:.1f} ({stats_b['FGM']:.1f}/{stats_b['FGA']:.1f})"
                elif c == 'FT%':
                    s1 = f"%{v1*100:.1f} ({stats_a['FTM']:.1f}/{stats_a['FTA']:.1f})"
                    s2 = f"%{v2*100:.1f} ({stats_b['FTM']:.1f}/{stats_b['FTA']:.1f})"
                else:
                    s1, s2 = f"{v1:.1f}", f"{v2:.1f}"
                # -------------------------
                
                if c not in punt_cats:
                    if c=='TOV': win = "A" if v1<v2 else "B"
                    else: win = "A" if v1>v2 else "B"
                    if win=="A": wa+=1 
                    else: wb+=1
                else: win="-"
                data.append({'KAT': c, 'TAKIM A': s1, 'TAKIM B': s2, 'KAZANAN': win})
            
            def color_row(row):
                if row['KAZANAN']=='A': return ['background-color: #1f77b4; color: white']*4
                if row['KAZANAN']=='B': return ['background-color: #d63031; color: white']*4
                return ['color: gray; text-decoration: line-through']*4
            
            st.dataframe(pd.DataFrame(data).style.apply(color_row, axis=1), use_container_width=True, hide_index=True)
            
            if wa>wb: st.success(f"🏆 TAKIM A KAZANIR ({wa}-{wb})")
            elif wb>wa: st.error(f"🏆 TAKIM B KAZANIR ({wb}-{wa})")
            else: st.warning("BERABERLİK")
