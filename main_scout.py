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

# --- MODERN TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #00D2FF;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 5px;
    }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    .stButton>button { background-color: transparent !important; color: #00D2FF !important; border: 1px solid #00D2FF !important; font-size: 12px !important; padding: 2px 10px !important; margin-top: 5px !important; }
    .stButton>button:hover { background-color: #00D2FF !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı Adı").strip()
    p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u, "password": make_hashes(p)}).execute(); st.success("Kayıt Tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and check_hashes(p, res.data[0]['password']): st.session_state.user = u; st.rerun()
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
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('---').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    
    u_low = st.session_state.user.lower()
    tabs_names = ["🔍 Scout", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    if any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"]): tabs_names.append("🛠️ Admin")
    tabs = st.tabs(tabs_names)

    with tabs[0]: # SCOUTING
        search = st.text_input("🔍 Ara:")
        f_pa = st.slider("🔥 Min PA:", 0, 200, 130)
        f_df = df[(df['PA'] >= f_pa)]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        
        for idx, row in f_df.head(20).iterrows():
            st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {row['PA']}</span><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small></div>""", unsafe_allow_html=True)
            if st.button(f"⭐ Listeye Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} eklendi!")

    with tabs[1]: # LİSTE
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            favs = [i['oyuncu_adi'] for i in res.data]
            st.dataframe(df[df['Oyuncu'].isin(favs)], use_container_width=True)
        else: st.info("Listen boş.")

    with tabs[2]: # KIYASLAMA
        c1, c2 = st.columns(2)
        all_p = sorted(df['Oyuncu'].tolist())
        p1 = c1.selectbox("1. Oyuncu", ["Seç..."] + all_p, key="k1")
        p2 = c2.selectbox("2. Oyuncu", ["Seç..."] + all_p, key="k2")
        if p1 != "Seç..." and p2 != "Seç...":
            r1, r2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.table(pd.DataFrame({"Özellik": ["PA", "Yaş", "Mevki", "Kulüp"], p1:[r1['PA'],r1['Yaş'],r1['Mevki'],r1['Kulüp']], p2:[r2['PA'],r2['Yaş'],r2['Mevki'],r2['Kulüp']]}))

    with tabs[3]: # KADROM (YENİ ÖZELLİK)
        st.subheader("⚽ Senin İlk 11'in")
        dizilis = st.selectbox("Diziliş Seç:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1"])
        kadro_pozisyonlari = {
            "4-3-3": ["GK", "LB", "CB1", "CB2", "RB", "CM1", "CM2", "CM3", "LW", "RW", "ST"],
            "4-4-2": ["GK", "LB", "CB1", "CB2", "RB", "LM", "CM1", "CM2", "RM", "ST1", "ST2"],
            "4-2-3-1": ["GK", "LB", "CB1", "CB2", "RB", "DM1", "DM2", "AMC", "LW", "RW", "ST"]
        }.get(dizilis, ["GK", "DEF", "DEF", "MID", "MID", "FWD"])
        
        my_squad = {}
        cols = st.columns(3)
        for i, pos in enumerate(kadro_pozisyonlari):
            my_squad[pos] = cols[i % 3].selectbox(f"{pos}:", ["Boş"] + sorted(df['Oyuncu'].tolist()), key=f"squad_{pos}")
        
        if st.button("Kadroyu Kaydet (Sadece Görsel)"):
            st.success("Kadro hazır! Ekran görüntüsü alabilirsin.")

    if len(tabs) > 4:
        with tabs[4]:
            adm = supabase.table("favoriler").select("*").execute()
            if adm.data: st.dataframe(pd.DataFrame(adm.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
