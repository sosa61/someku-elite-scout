import streamlit as st
import pandas as pd
import os
import hashlib
import random
import urllib.parse
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Türkçe Pozisyon Sözlüğü
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM VE BUTON STİLLERİ ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .barrow-panel { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 12px; border: 1px solid #00D2FF; margin-bottom: 15px; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    .tm-button { display: inline-block; padding: 5px 10px; background-color: #1a3151; color: #ffffff !important; text-decoration: none; border-radius: 5px; font-size: 12px; border: 1px solid #d2ad5c; margin-top: 10px; font-weight: bold; }
    .tm-button:hover { background-color: #24416b; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'seed' not in st.session_state: st.session_state.seed = 42

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
        if res.data and res.data[0]['password'] == get_hash(p): st.session_state.user = u; st.rerun()
        else: st.error("Hatalı!")
else:
    @st.cache_data(ttl=3600)
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£', '').replace('€', '').replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- 🕵️‍♂️ BARROW AI V38: KARIŞTIR & TRANSFERMARKT ✅ ---
    with st.container():
        st.markdown(f'<div class="barrow-panel"><h3>🕵️‍♂️ Barrow AI</h3>{st.session_state.user}, transfer hedefini belirle! (Örn: "20 yaş stoper", "Alman kanat")</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Barrow'a talimat ver...", key="barrow_q", label_visibility="collapsed").lower()
        
        if q:
            ai_df = df.copy()
            import re
            age_match = re.search(r'(\d+)\s*yaş', q)
            if age_match: ai_df = ai_df[ai_df['Yaş'] == int(age_match.group(1))]
            
            milletler = {"türk": "Tur", "italyan": "Ita", "alman": "Ger", "fransız": "Fra", "ispanyol": "Spa", "brezilya": "Bra"}
            for k, v in milletler.items():
                if k in q: ai_df = ai_df[ai_df['Ülke'].str.contains(v, na=False)]
            
            if "forvet" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("ST", na=False)]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]

            if st.button("🔄 Başka Oyuncular Öner"):
                st.session_state.seed = random.randint(0, 1000)

            top_candidates = ai_df.sort_values(by="PA", ascending=False).head(30)
            final_df = top_candidates.sample(min(len(top_candidates), 3), random_state=st.session_state.seed)

            st.write(f"✨ **Barrow'un Scout Raporu:**")
            cols = st.columns(3)
            for i, (idx, r) in enumerate(final_df.iterrows()):
                tr_m = ", ".join([ana_mevkiler.get(m.strip(), m.strip()) for m in r['Mevki'].split(",")])
                # Transfermarkt Linki Oluşturma
                search_query = urllib.parse.quote(f"{r['Oyuncu']} {r['Kulüp']}")
                tm_link = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={search_query}"
                
                with cols[i]:
                    st.info(f"**{r['Oyuncu']}**\n\n🛡️ {r['Kulüp']}\n⚽ {tr_m}\n🎂 Yaş: {r['Yaş']} | PA: {r['PA']}")
                    st.markdown(f'<a href="{tm_link}" target="_blank" class="tm-button">🔍 Transfer Geçmişi (TM)</a>', unsafe_allow_html=True)

    # --- SEKMELER ---
    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "🛠️ Admin"])

    with tabs[0]: # SCOUT
        c1, c2 = st.columns(2); search = c1.text_input("🔍 Oyuncu Ara:"); f_pa = c2.slider("Min PA:", 0, 200, 130)
        res_df = df[df['PA'] >= f_pa]
        if search: res_df = res_df[res_df['Oyuncu'].str.contains(search, case=False)]

        for idx, row in res_df.head(10).iterrows():
            st.markdown(f'<div class="player-card"><b>{row["Oyuncu"]}</b> ({row["Yaş"]}) - {row["Kulüp"]}<br><small>PA: {row["PA"]} | {row["Mevki"]}</small></div>', unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"s_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")

    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()
