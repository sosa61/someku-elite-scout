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

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return hashed_text if make_hashes(password) == hashed_text else False

# --- MODERN TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #00D2FF;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    .stButton>button { width: 100%; margin-top: 10px; border: 1px solid #00D2FF; background: transparent; color: #00D2FF; }
    .stButton>button:hover { background: #00D2FF; color: black; }
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

    with tabs[0]: # SCOUTING (ÜLKE VE DİĞER FİLTRELER GELDİ)
        st.markdown("<div style='background:rgba(0,0,0,0.4);padding:15px;border-radius:10px;margin-bottom:20px;'>", unsafe_allow_html=True)
        search = st.text_input("🔍 İsim veya Kulüp:")
        
        # Ülke Filtresi (Dinamik ve Temiz)
        all_countries = set()
        for val in df['Ülke'].unique():
            for c in val.replace('/', ',').split(','): all_countries.add(c.strip())
        f_ulke = st.multiselect("🌎 Ülke Seç (Türkiye yazınca Kenan Yıldız gelir):", sorted(list(all_countries)))
        
        c1, c2 = st.columns(2)
        f_pa = c1.slider("🔥 Min PA:", 0, 200, 130)
        f_yas = c2.slider("🎂 Max Yaş:", 14, 45, 45)
        st.markdown("</div>", unsafe_allow_html=True)

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] <= f_yas)]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_ulke: f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]
        
        for idx, row in f_df.head(20).iterrows():
            with st.container():
                st.markdown(f"""
                <div class="player-card">
                    <span class="pa-badge">PA: {row['PA']}</span>
                    <b>{row['Oyuncu']}</b> ({row['Yaş']})<br>
                    <small>🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</small><br>
                    <small style="color:#00FFC2">⚽ {row['Mevki']} | 💰 {row['Değer']}</small>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"⭐ {row['Oyuncu']} Ekle", key=f"add_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} kaydedildi!")

    with tabs[1]: # LİSTE
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in res.data])], use_container_width=True)
            if st.button("Listeyi Boşalt"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute(); st.rerun()

    with tabs[2]: # KIYASLA (GERİ GELDİ)
        st.subheader("⚔️ Kıyaslama")
        plist = sorted(df['Oyuncu'].tolist())
        sc1, sc2 = st.columns(2)
        p1 = sc1.selectbox("1. Oyuncu", ["Seç..."] + plist, key="c1")
        p2 = sc2.selectbox("2. Oyuncu", ["Seç..."] + plist, key="c2")
        if p1 != "Seç..." and p2 != "Seç...":
            r1, r2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.table(pd.DataFrame({"Özellik": ["PA", "CA", "Yaş", "Mevki", "Kulüp"], p1:[r1['PA'],r1['CA'],r1['Yaş'],r1['Mevki'],r1['Kulüp']], p2:[r2['PA'],r2['CA'],r2['Yaş'],r2['Mevki'],r2['Kulüp']]}))

    with tabs[3]: # KADROM
        st.subheader("⚽ İlk 11 Dizilişin")
        dizilis = st.selectbox("Formasyon:", ["4-3-3", "4-4-2", "4-2-3-1"])
        pos_list = {"4-3-3": ["GK", "LB", "CB1", "CB2", "RB", "CM1", "CM2", "CM3", "LW", "RW", "ST"], "4-4-2": ["GK", "LB", "CB1", "CB2", "RB", "LM", "CM1", "CM2", "RM", "ST1", "ST2"], "4-2-3-1": ["GK", "LB", "CB1", "CB2", "RB", "DM1", "DM2", "AMC", "LW", "RW", "ST"]}.get(dizilis)
        cols = st.columns(3)
        for i, p in enumerate(pos_list):
            cols[i%3].selectbox(f"{p}:", ["Boş"] + sorted(df['Oyuncu'].tolist()), key=f"s_{p}")

    if len(tabs) > 4: # ADMIN
        with tabs[4]:
            adm = supabase.table("favoriler").select("*").execute()
            if adm.data: st.dataframe(pd.DataFrame(adm.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
