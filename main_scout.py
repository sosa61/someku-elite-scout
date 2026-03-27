import streamlit as st
import pandas as pd
import os
import hashlib
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# FM Pozisyon Sözlüğü
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return hashed_text if make_hashes(password) == hashed_text else False

# --- YENİ MODERN TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #00D2FF;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        transition: 0.3s;
    }
    .player-card:hover { border-color: #00FFC2; background: rgba(255, 255, 255, 0.1); }
    .pa-badge {
        background: #00D2FF;
        color: black;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: bold;
        float: right;
    }
    .club-text { color: #AAAAAA; font-size: 14px; }
    .mevki-text { color: #00FFC2; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    user = st.text_input("Kullanıcı Adı").strip()
    pw = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": user, "password": make_hashes(pw)}).execute()
            st.success("Kayıt Tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
            if res.data and check_hashes(pw, res.data[0]['password']):
                st.session_state.user = user
                st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']:
            df[col] = df[col].fillna('---').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    
    u_lower = st.session_state.user.lower()
    tabs_to_show = ["🔍 Scouting", "⭐ Listem", "⚔️ Kıyasla"]
    if any(x in u_lower for x in ["someku", "omer", "ömer"]): tabs_to_show.append("🛠️ Admin")
    tabs = st.tabs(tabs_to_show)

    with tabs[0]: # SCOUTING (KART GÖRÜNÜMÜ)
        st.markdown("<div style='background:rgba(0,0,0,0.5);padding:15px;border-radius:10px;margin-bottom:20px;'>", unsafe_allow_html=True)
        search = st.text_input("🔍 Oyuncu veya Kulüp Ara:")
        f_mevki = st.multiselect("⚽ Mevki Seç:", options=list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_pa = st.slider("🔥 Minimum PA:", 0, 200, 130)
        st.markdown("</div>", unsafe_allow_html=True)

        f_df = df.copy()
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        f_df = f_df[f_df['PA'] >= f_pa]

        # KARTLARI LİSTELE
        for idx, row in f_df.head(20).iterrows():
            with st.container():
                st.markdown(f"""
                <div class="player-card">
                    <span class="pa-badge">PA: {row['PA']}</span>
                    <div style="font-size: 20px; font-weight: bold;">{row['Oyuncu']} <span style="font-size: 14px; font-weight: normal;">({row['Yaş']})</span></div>
                    <div class="club-text">🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</div>
                    <div class="mevki-text">⚽ {row['Mevki']} | 💰 {row['Değer']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"⭐ {row['Oyuncu']} Listeme Ekle", key=f"btn_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} eklendi!")

    with tabs[1]: # LİSTEM (KART GÖRÜNÜMÜ)
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            fav_names = [i['oyuncu_adi'] for i in res.data]
            f_favs = df[df['Oyuncu'].isin(fav_names)]
            for _, row in f_favs.iterrows():
                st.markdown(f'<div class="player-card"><span class="pa-badge">PA: {row["PA"]}</span><b>{row["Oyuncu"]}</b><br>{row["Kulüp"]}</div>', unsafe_allow_html=True)
            if st.button("Listeyi Temizle"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute(); st.rerun()

    if "🛠️ Admin" in tabs_to_show:
        with tabs[-1]:
            st.subheader("🛠️ Admin Paneli")
            adm = supabase.table("favoriler").select("*").execute()
            if adm.data: st.dataframe(pd.DataFrame(adm.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
