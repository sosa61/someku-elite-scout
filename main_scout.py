import streamlit as st
import pandas as pd
import os
import hashlib
import random
import urllib.parse
import re
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Türkçe Pozisyonlar
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .p-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .progress-bar { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin: 10px 0; overflow: hidden; }
    .progress-val { height: 100%; border-radius: 10px; transition: 0.5s; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'seed' not in st.session_state: st.session_state.seed = random.randint(0, 9999)

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    u_in = st.text_input("Kullanıcı"); p_in = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        res = supabase.table("kullanicilar").select("*").eq("username", u_in).execute()
        if res.data and res.data[0]['password'] == get_hash(p_in): st.session_state.user = u_in; st.rerun()
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

    # --- BARROW AI ---
    with st.container():
        q = st.text_input("Barrow AI Sorgu:", placeholder="Brezilyalı forvet, 19 yaş stoper...", key="ai_q").lower()
        if st.button("🔄 Karıştır / Getir"): st.session_state.seed = random.randint(0, 9999)
        if q:
            ai_df = df.copy()
            mil_map = {"türk": "Tur", "alman": "Ger", "italyan": "Ita", "fransız": "Fra", "ispanyol": "Spa", "brezilya": "Bra", "arjantin": "Arg"}
            for k, v in mil_map.items():
                if k in q: ai_df = ai_df[ai_df['Ülke'].str.contains(v, na=False, case=False)]
            age_m = re.search(r'(\d+)\s*yaş', q)
            if age_m: ai_df = ai_df[ai_df['Yaş'] == int(age_m.group(1))]
            if "forvet" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("ST", na=False)]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            
            final = ai_df.sort_values(by="PA", ascending=False).head(30)
            if not final.empty:
                show = final.sample(min(len(final), 3), random_state=st.session_state.seed)
                c_ai = st.columns(3)
                for i, (idx, r) in enumerate(show.iterrows()):
                    with c_ai[i]: st.info(f"**{r['Oyuncu']}**\n\nPA: {r['PA']} | {r['Kulüp']}\n🌎 {r['Ülke']}")
            else: st.warning("Bulunamadı.")

    # --- SEKMELER ---
    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT
        c1, c2 = st.columns(2); s_in = c1.text_input("🔍 Ara:"); f_pa = c2.slider("Min PA:", 0, 200, 130)
        res = df[df['PA'] >= f_pa]
        if s_in: res = res[res['Oyuncu'].str.contains(s_in, case=False)]
        for idx, row in res.head(10).iterrows():
            st.markdown(f'<div class="p-card"><b>{row["Oyuncu"]}</b> ({row["Yaş"]}) - {row["Kulüp"]}<br><small>PA: {row["PA"]} | {row["Mevki"]}</small></div>', unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"fav_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} Eklendi!")

    with tabs[1]: # 🔥 POPÜLER (TAMİR EDİLDİ ✅)
        st.subheader("🔥 En Çok Takibe Alınanlar")
        pop_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop_res.data:
            pop_df = pd.DataFrame(pop_res.data)['oyuncu_adi'].value_counts().reset_index()
            pop_df.columns = ['Oyuncu', 'Takip Sayısı']
            # Mevcut dataframe (df) ile birleştirerek mevki ve PA bilgilerini ekleyelim
            pop_full = pd.merge(pop_df.head(10), df[['Oyuncu', 'Mevki', 'PA', 'Kulüp']], on='Oyuncu', how='left')
            st.table(pop_full)
        else:
            st.info("Henüz favori oyuncu yok.")

    with tabs[2]: # ⭐ LİSTE
        my_favs = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if my_favs.data:
            f_list = [i['oyuncu_adi'] for i in my_favs.data]
            st.dataframe(df[df['Oyuncu'].isin(f_list)][['Oyuncu', 'Yaş', 'PA', 'Kulüp', 'Değer']])

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
