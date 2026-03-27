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

# Şifreleme Fonksiyonu (Güvenlik için)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

# Tema Ayarları
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .auth-box { background-color: rgba(25,25,25,0.98); padding: 30px; border-radius: 15px; border: 1px solid #00D2FF; max-width: 400px; margin: auto; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ VE KAYIT EKRANI ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 SOMEKU SCOUT GÜVENLİK</h1>", unsafe_allow_html=True)
    
    auth_mode = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    
    with st.container():
        st.markdown("<div class='auth-box'>", unsafe_allow_html=True)
        user = st.text_input("Kullanıcı Adı:")
        password = st.text_input("Şifre:", type="password")
        
        if auth_mode == "Kayıt Ol":
            if st.button("Hesap Oluştur"):
                # Kullanıcı var mı kontrol et
                check = supabase.table("kullanicilar").select("*").eq("username", user).execute()
                if len(check.data) > 0:
                    st.error("Bu kullanıcı adı zaten alınmış!")
                else:
                    hashed_pw = make_hashes(password)
                    supabase.table("kullanicilar").insert({"username": user, "password": hashed_pw}).execute()
                    st.success("Kayıt başarılı! Şimdi Giriş Yap diyerek bağlanabilirsin.")
        
        else: # Giriş Yap modu
            if st.button("Giriş"):
                res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
                if res.data:
                    if check_hashes(password, res.data[0]['password']):
                        st.session_state.user = user
                        st.success(f"Hoş geldin {user}!")
                        st.rerun()
                    else:
                        st.error("Hatalı şifre!")
                else:
                    st.error("Kullanıcı bulunamadı!")
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- ANA PROGRAM (ÖNCEKİ KODUN DEVAMI) ---
    st.markdown(f"<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    st.sidebar.success(f"👤 Oturum: {st.session_state.user}")
    
    @st.cache_data
    def load_data():
        df = pd.read_csv("players_export.csv", sep=None, engine='python')
        df.columns = [c.strip() for c in df.columns]
        for col in ['PA', 'Yaş']:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    
    tab_list = ["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"]
    if st.session_state.user.lower() in ["ömer", "someku", "ramazan"]:
        tab_list.append("🛠️ Admin")
    
    tabs = st.tabs(tab_list)

    with tabs[0]: # SCOUTING
        search = st.text_input("🔍 Oyuncu Ara:")
        f_df = df[df['Oyuncu'].str.contains(search, case=False, na=False)].head(15)
        for idx, row in f_df.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"**{row['Oyuncu']}** - PA: {row['PA']}")
            if c2.button("⭐", key=f"f_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")

    with tabs[1]: # TRANSFER LİSTEM
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            favs = [item['oyuncu_adi'] for item in res.data]
            st.dataframe(df[df['Oyuncu'].isin(favs)], use_container_width=True)
        else: st.write("Listeniz boş.")

    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()
