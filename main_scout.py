import streamlit as st
import pandas as pd
import os
import re
import hashlib
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Şifreleme
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return hashed_text if make_hashes(password) == hashed_text else False

# Tema (Bozmadım!)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .auth-box, .filter-box { background-color: rgba(25,25,25,0.98); padding: 25px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 10px; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 SOMEKU SCOUT GÜVENLİK</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    with st.container():
        st.markdown("<div class='auth-box'>", unsafe_allow_html=True)
        user = st.text_input("Kullanıcı Adı:").strip()
        password = st.text_input("Şifre:", type="password")
        if auth_mode == "Kayıt Ol":
            if st.button("Hesap Oluştur"):
                check = supabase.table("kullanicilar").select("*").eq("username", user).execute()
                if len(check.data) > 0: st.error("Bu kullanıcı adı dolu!")
                else:
                    supabase.table("kullanicilar").insert({"username": user, "password": make_hashes(password)}).execute()
                    st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
        else:
            if st.button("Giriş"):
                res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
                if res.data and check_hashes(password, res.data[0]['password']):
                    st.session_state.user = user
                    st.rerun()
                else: st.error("Hatalı kullanıcı veya şifre!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- VERİ YÜKLEME ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns] # Boşlukları temizle
        
        # Sütunları sayıya çevir ve temizle
        cols_to_fix = {'PA': 'PA', 'Yaş': 'Yaş', 'Oyuncu': 'Oyuncu', 'Mevki': 'Mevki', 'Ülke': 'Ülke', 'Kulüp': 'Kulüp'}
        for col in df.columns:
            if col in ['PA', 'Yaş', 'CA']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            else:
                df[col] = df[col].fillna('Unknown').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    st.sidebar.success(f"👤 Oturum: {st.session_state.user}")

    if df is not None:
        tab_list = ["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"]
        if st.session_state.user.lower() in ["someku", "ömer", "ramazan"]: tab_list.append("🛠️ Admin")
        tabs = st.tabs(tab_list)

        with tabs[0]: # SCOUTING & FİLTRELER
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            # Dinamik Filtre Listeleri
            mevki_listesi = sorted(df['Mevki'].unique().tolist())
            ulke_listesi = sorted(df['Ülke'].unique().tolist())
            
            f_mevki = c1.multiselect("⚽ Mevki Seç:", mevki_listesi)
            f_ulke = c1.multiselect("🌎 Ülke Seç:", ulke_listesi)
            f_yas = c2.slider("🎂 Yaş:", int(df['Yaş'].min()), int(df['Yaş'].max()), (14, 45))
            f_pa = c2.slider("🔥 PA:", int(df['PA'].min()), int(df['PA'].max()), (0, 200))
            search = st.text_input("🔍 Oyuncu veya Kulüp İsmi Yazın...")
            st.markdown("</div>", unsafe_allow_html=True)

            # Filtreleme Mantığı
            f_df = df.copy()
            if f_mevki: f_df = f_df[f_df['Mevki'].isin(f_mevki)]
            if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]
            if search:
                f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False, na=False)) | (f_df['Kulüp'].str.contains(search, case=False, na=False))]
            f_df = f_df[(f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1]) & (f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])]

            st.subheader(f"✅ {len(f_df)} Oyuncu")
            
            for idx, row in f_df.head(15).iterrows():
                col_data, col_btn = st.columns([5, 1])
                col_data.write(f"**{row['Oyuncu']}** ({row['Yaş']}) - {row['Kulüp']} | PA: {row['PA']} | {row['Mevki']}")
                if col_btn.button("⭐", key=f"fav_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} listene eklendi!")
            st.dataframe(f_df, use_container_width=True)

        with tabs[1]: # TRANSFER LİSTEM
            res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
            if res.data:
                fav_names = [item['oyuncu_adi'] for item in res.data]
                st.dataframe(df[df['Oyuncu'].isin(fav_names)], use_container_width=True)
                if st.button("Listeyi Temizle"):
                    supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                    st.rerun()
            else: st.info("Favori listeniz boş.")

        with tabs[2]: # KARŞILAŞTIRMA
            p_list = ["Seçiniz..."] + sorted(df['Oyuncu'].unique().tolist())
            sc1, sc2 = st.columns(2)
            s1 = sc1.selectbox("1. Oyuncu:", p_list, key="comp1")
            s2 = sc2.selectbox("2. Oyuncu:", p_list, key="comp2")
            if s1 != "Seçiniz..." and s2 != "Seçiniz...":
                d1, d2 = df[df['Oyuncu'] == s1].iloc[0], df[df['Oyuncu'] == s2].iloc[0]
                st.metric(s1, f"PA: {d1['PA']}", f"Yaş: {d1['Yaş']}")
                st.metric(s2, f"PA: {d2['PA']}", f"Yaş: {d2['Yaş']}")

        if len(tabs) > 3: # ADMIN
            with tabs[3]:
                st.write("### 👑 Tüm Kullanıcı Kayıtları")
                adm = supabase.table("favoriler").select("*").execute()
                if adm.data: st.table(pd.DataFrame(adm.data)[['kullanici_adi', 'oyuncu_adi', 'created_at']].tail(20))

    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()
