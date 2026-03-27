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

# Tema (Daha Keskin Hatlar)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1A1C23; border-radius: 5px; padding: 10px 20px; color: white; }
    .filter-box { background-color: rgba(20,20,20,0.98); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 20px; }
    h1 { text-align: center; color: #00D2FF; font-size: 28px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ YAP VEYA KAYIT OL</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Giriş")
        l_user = st.text_input("Kullanıcı Adı", key="l_u").strip()
        l_pass = st.text_input("Şifre", type="password", key="l_p")
        if st.button("Bağlan"):
            res = supabase.table("kullanicilar").select("*").eq("username", l_user).execute()
            if res.data and check_hashes(l_pass, res.data[0]['password']):
                st.session_state.user = l_user
                st.rerun()
            else: st.error("Hatalı!")
    with c2:
        st.subheader("Yeni Kayıt")
        r_user = st.text_input("Kullanıcı Adı Seç", key="r_u").strip()
        r_pass = st.text_input("Şifre Seç", type="password", key="r_p")
        if st.button("Hesap Aç"):
            supabase.table("kullanicilar").insert({"username": r_user, "password": make_hashes(r_pass)}).execute()
            st.success("Kayıt Tamam!")

else:
    # --- AKILLI VERİ YÜKLEME ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        # Kayma olsa bile veriyi oku, ilk satırı atla
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        
        # Sütunları manuel zorla (En güvenli yol)
        # 1:İsim, 2:Yaş, 3:CA, 4:PA, 5:Ülke, 6:Kulüp, 7:Değer, 8:Mevki
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        
        # Temizlik
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', '
