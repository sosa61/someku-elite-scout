import streamlit as st
import pandas as pd
import os
import hashlib
import json
import urllib.parse
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

ana_mevkiler = ["GK", "D C", "D L", "D R", "DM", "M C", "AM C", "AM L", "AM R", "ST"]

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .tm-button { display: inline-block; padding: 6px 12px; background-color: #1a3151; color: gold !important; text-decoration: none; border-radius: 6px; font-weight: bold; border: 1px solid gold; font-size: 12px; margin-top: 8px; }
    .tm-button:hover { background-color: #24416b; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- AUTH SİSTEMİ ---
if st.session_state.user is None:
    st.title("🌪️ SOMEKU SCOUT")
    auth_tab = st.radio("Seçim:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        hp = get_hash(p)
        if auth_tab == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute()
            st.success("Kayıt Başarılı!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp:
                st.session_state.user = u
                st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Kulüp', 'Mevki', 'Ülke']: df[col] = df[col].astype(str).str.strip()
        return df

    df = load_data()
    tabs = st.tabs(["🔍 SCOUT", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT (TRANSFERMARKT ENTEGRASYONU ✅)
        st.subheader("Oyuncu Arama & Scout")
        c1, c2 = st.columns(2)
        n_search = c1.text_input("İsim Ara:")
        m_filter = c2.multiselect("Pozisyon:", ana_mevkiler)
        
        f_df = df.copy()
        if n_search: f_df = f_df[f_df['Oyuncu'].str.contains(n_search, case=False)]
        if m_filter: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in str(x) for m in m_filter))]
        
        for _, r in f_df.head(15).iterrows():
            # TM Linki oluştur
            tm_q = urllib.parse.quote(f"{r['Oyuncu']} {r['Kulüp']}")
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={tm_q}"
            
            with st.container():
                st.markdown(f"""
                <div class="player-card">
                    <b>{r['Oyuncu']}</b> ({r['Yaş']}) | {r['Kulüp']}<br>
                    <small>{r['Mevki']} | PA: {r['PA']} | 🌎 {r['Ülke']}</small><br>
                    <a href="{tm_url}" target="_blank" class="tm-button">🔍 Transfermarkt Kariyer</a>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"⭐ Ekle", key=f"fav_{r['Oyuncu']}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                    st.toast("Eklendi!")

    with tabs[3]: # KADROM (KAYDETME ✅)
        st.subheader("Kadro Planla ve Kaydet")
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        c = st.columns(3)
        st_p = c[1].selectbox("Forvet", p_opt)
        lw_p = c[0].selectbox("Sol Kanat", p_opt)
        rw_p = c[2].selectbox("Sağ Kanat", p_opt)
        
        k_adi = st.text_input("Kadro İsmi:")
        if st.button("💾 Kaydet"):
            k_data = f"KADRO:{k_adi}|{json.dumps([lw_p, st_p, rw_p])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute()
            st.success("Kaydedildi!")

    if st.sidebar.button("Çıkış"):
        st.session_state.user = None
        st.rerun()
