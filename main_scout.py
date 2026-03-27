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

# Şifreleme Fonksiyonları
def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return hashed_text if make_hashes(password) == hashed_text else False

# Tema (Bozmadım!)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .auth-box { background-color: rgba(25,25,25,0.98); padding: 30px; border-radius: 15px; border: 1px solid #00D2FF; max-width: 400px; margin: auto; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; }
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
    # --- VERİ YÜKLEME (HATAYI ÇÖZEN YER) ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python')
        # Sütun isimlerini zorla temizle ve yeniden adlandır
        df.columns = [c.strip() for c in df.columns]
        
        # Eğer senin dosyanda 'PA' ismi farklıysa, onu otomatik 'PA' yapalım
        mapping = {'PA': 'PA', 'Potansiyel': 'PA', 'Pot': 'PA'} # FM diline göre esnetebiliriz
        for old, new in mapping.items():
            if old in df.columns: df = df.rename(columns={old: new})
        
        if 'PA' in df.columns:
            df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
            return df.sort_values(by='PA', ascending=False)
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    st.sidebar.success(f"👤 Oturum: {st.session_state.user}")

    if df is not None:
        tab_list = ["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"]
        if st.session_state.user.lower() in ["someku", "ömer", "ramazan"]: tab_list.append("🛠️ Admin")
        tabs = st.tabs(tab_list)

        with tabs[0]:
            search = st.text_input("🔍 Oyuncu Ara:")
            f_df = df[df['Oyuncu'].str.contains(search, case=False, na=False)].head(15) if 'Oyuncu' in df.columns else df.head(15)
            st.dataframe(f_df, use_container_width=True)
    else:
        st.error("Veri dosyası (players_export.csv) okunamadı veya sütunlar hatalı!")

    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()
