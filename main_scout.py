import streamlit as st
import pandas as pd
import os
import re
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Tema Ayarları
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .filter-box { background-color: rgba(25,25,25,0.98); padding: 15px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 10px; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; font-size: 22px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ YAP</h1>", unsafe_allow_html=True)
    # İSTEDİĞİN ÖRNEK İSİMLER BURADA:
    user_name = st.text_input("", placeholder="ömer veya bahadır veya nuri").strip()
    if st.button("Sisteme Gir"):
        if user_name: 
            st.session_state.user = user_name
            st.rerun()
else:
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    st.sidebar.success(f"👤 Profil: {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()

    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        for col in ['PA', 'Yaş', 'CA']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Mevki', 'Kulüp']:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()

    if df is not None:
        tabs = st.tabs(["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"])

        with tabs[0]: 
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            # Dinamik Filtreleme (Dosyadan Okur)
            mevki_listesi = sorted(df['Mevki'].unique().tolist())
            ulke_listesi = sorted(df['Ülke'].unique().tolist())
            
            f_mevki = col1.multiselect("⚽ Mevki Seç:", mevki_listesi)
            f_ulke = col1.multiselect("🌎 Ülke Seç:", ulke_listesi)
            
            f_yas = col2.slider("🎂 Yaş:", int(df['Yaş'].min()), int(df['Yaş'].max()), (14, 45))
            f_pa = col2.slider("🔥 PA:", int(df['PA'].min()), int(df['PA'].max()), (0, 200))
            search = st.text_input("🔍 İsim veya Kulüp Ara:")
            st.markdown("</div>", unsafe_allow_html=True)

            f_df = df.copy()
            if f_mevki: f_df = f_df[f_df['Mevki'].isin(f_mevki)]
            if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]
            
            f_df = f_df[
                ((f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))) &
                (f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1]) &
                (f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])
            ]

            st.subheader(f"✅ {len(f_df)} Oyuncu")
            
            for idx, row in f_df.head(12).iterrows():
                c1, c2 = st.columns([5, 1])
                c1.write(f"**{row['Oyuncu']}** ({row['Yaş']}) - {row['Kulüp']} | PA: {row['PA']}")
                if c2.button("⭐", key=f"btn_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} listeye eklendi!")

            st.dataframe(f_df, use_container_width=True)

        with tabs[1]:
            st.markdown("### ⭐ Senin Transfer Listen")
            res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
            if res.data:
                fav_names = [item['oyuncu_adi'] for item in res.data]
                st.dataframe(df[df['Oyuncu'].isin(fav_names)], use_container_width=True)
                if st.button("Listeyi Temizle"):
                    supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                    st.rerun()
            else: st.info("Henüz favori oyuncun yok.")
