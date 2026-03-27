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

# --- BÖLGESEL ÜLKE LİSTELERİ ---
bolge_gruplari = {
    "Güney Amerika": ["Argentina", "Brazil", "Uruguay", "Colombia", "Chile", "Ecuador", "Paraguay", "Peru", "Venezuela", "Bolivia"],
    "Avrupa (Genel)": ["Germany", "France", "Spain", "Italy", "Portugal", "Netherlands", "Belgium", "Switzerland", "Austria", "England"],
    "Kuzey Avrupa": ["Norway", "Sweden", "Denmark", "Finland", "Iceland"],
    "Afrika": ["Nigeria", "Senegal", "Ivory Coast", "Cameroon", "Ghana", "Algeria", "Morocco", "Egypt", "Mali", "Tunisia"],
    "Asya": ["Japan", "South Korea", "China", "Australia", "Iran", "Saudi Arabia", "Uzbekistan"],
    "Balkanlar/Doğu": ["Turkey", "Croatia", "Serbia", "Greece", "Bulgaria", "Romania", "Poland", "Czech Republic", "Slovakia", "Hungary", "Ukraine", "Russia"]
}

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .filter-box { background-color: rgba(25,25,25,0.98); padding: 15px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 10px; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; }
    </style>
    """, unsafe_allow_html=True)

# --- OTURUM ---
if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ YAP</h1>", unsafe_allow_html=True)
    user_name = st.text_input("", placeholder="Profil İsminiz (Örn: Ramazan)...").strip()
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
        df = pd.read_csv("players_export.csv", sep=None, engine='python')
        df.columns = ['ID','Oyuncu','Yaş','CA','PA','Ülke','Kulüp','Değer','Mevki','Rat','Pot_Rat'][:len(df.columns)]
        df['Ülke'] = df['Ülke'].fillna('Bilinmiyor').astype(str)
        df['Mevki'] = df['Mevki'].fillna('-').astype(str)
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    tabs = st.tabs(["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"])

    with tabs[0]: 
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        f_mevki = col1.multiselect("⚽ Mevki:", ["Kaleci", "Stoper", "Sağ Bek", "Sol Bek", "Ön Libero", "Merkez Orta Saha", "Sağ Kanat", "Sol Kanat", "On Numara", "Forvet"])
        f_bolge = col1.multiselect("🌎 Bölge/Kıta Seç:", list(bolge_gruplari.keys()))
        f_yas = col2.slider("🎂 Yaş:", 14, 45, (14, 45))
        f_pa = col2.slider("🔥 PA:", 0, 200, (0, 200))
        search = st.text_input("🔍 İsim veya Kulüp Ara:")
        st.markdown("</div>", unsafe_allow_html=True)

        # Filtreleme İşlemi
        f_df = df.copy()
        
        # Bölge Filtresi (DÜZELTİLDİ ✅)
        if f_bolge:
            secilen_ulkeler = []
            for b in f_bolge: secilen_ulkeler.extend(bolge_gruplari[b])
            f_df = f_df[f_df['Ülke'].isin(secilen_ulkeler)]

        # Diğer Filtreler
        f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        f_df = f_df[(f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1]) & (f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])]

        # Mevki Filtresi (Hatasız Regex ✅)
        mevki_map = {"Kaleci":"GK", "Stoper":"D (C)", "Sağ Bek":"D (R)", "Sol Bek":"D (L)", "Ön Libero":"DM", "Merkez Orta Saha":"M (C)", "Sağ Kanat":"(R)", "Sol Kanat":"(L)", "On Numara":"AM (C)", "Forvet":"S (C)"}
        if f_mevki:
            karsiliklar = [mevki_map[m] for m in f_mevki]
            f_df = f_df[f_df['Mevki'].apply(lambda x: any(re.search(re.escape(k), x, re.IGNORECASE) for k in karsiliklar))]

        st.subheader(f"✅ {len(f_df)} Oyuncu Listelendi")
        
        # Hızlı Favoriye Ekleme Listesi
        for idx, row in f_df.head(10).iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{row['Oyuncu']}** ({row['Yaş']}) - {row['Kulüp']} | PA: {row['PA']}")
            if c2.button("⭐", key=f"btn_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} kaydedildi!")

        st.dataframe(f_df[['Oyuncu', 'Yaş', 'PA', 'Mevki', 'Ülke', 'Kulüp', 'Değer']], use_container_width=True)

    with tabs[1]:
        st.markdown("### ⭐ Transfer Listem")
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            favs = [item['oyuncu_adi'] for item in res.data]
            st.dataframe(df[df['Oyuncu'].isin(favs)][['Oyuncu', 'Yaş', 'PA', 'Kulüp', 'Değer']], use_container_width=True)
            if st.button("Listeyi Temizle"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                st.rerun()
        else: st.info("Henüz favori oyuncun yok.")

    with tabs[2]:
        p_list = ["Seçiniz..."] + sorted(df['Oyuncu'].unique().tolist())
        c1, c2 = st.columns(2)
        sel1 = c1.selectbox("1. Oyuncu:", p_list, key="s1")
        sel2 = c2.selectbox("2. Oyuncu:", p_list, key="s2")
        if sel1 != "Seçiniz..." and sel2 != "Seçiniz...":
            d1, d2 = df[df['Oyuncu'] == sel1].iloc[0], df[df['Oyuncu'] == sel2].iloc[0]
            st.metric(sel1, f"PA: {d1['PA']}", f"Yaş: {d1['Yaş']}")
            st.metric(sel2, f"PA: {d2['PA']}", f"Yaş: {d2['Yaş']}")
