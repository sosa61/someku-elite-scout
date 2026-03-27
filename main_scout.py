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

# Tema (Değişmedi)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .filter-box { background-color: rgba(25,25,25,0.98); padding: 15px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 10px; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; font-size: 24px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

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
                if len(check.data) > 0: st.error("Bu kullanıcı adı alınmış!")
                else:
                    supabase.table("kullanicilar").insert({"username": user, "password": make_hashes(password)}).execute()
                    st.success("Kayıt başarılı! Şimdi giriş yapabilirsin.")
        else:
            if st.button("Giriş"):
                res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
                if res.data and check_hashes(password, res.data[0]['password']):
                    st.session_state.user = user
                    st.rerun()
                else: st.error("Hatalı kullanıcı veya şifre!")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- VERİ YÜKLEME (SIRALAMA KORUMALI) ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        # Dosyayı oku, başlık satırını atla ve kendi başlıklarımızı koy
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        
        # Sütunları manuel eşleştiriyoruz (Resimdeki kaymaya göre)
        # 1: Oyuncu, 2: Yaş, 3: CA, 4: PA, 5: Ülke, 6: Kulüp, 7: Değer, 8: Mevki
        df = df[[1, 2, 3, 4, 5, 6, 7, 8]] 
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        
        # Temizlik ve Sayıya Çevirme
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']:
            df[col] = df[col].fillna('Bilinmiyor').astype(str).str.strip()
            
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    if df is not None:
        tabs = st.tabs(["🔍 Scouting", "⭐ Transfer Listem", "⚔️ Karşılaştır"])

        with tabs[0]: # SCOUTING
            st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
            search = st.text_input("🔍 Oyuncu veya Kulüp Ara:")
            c1, c2 = st.columns(2)
            f_mevki = c1.multiselect("⚽ Mevki:", sorted(df['Mevki'].unique().tolist()))
            f_ulke = c1.multiselect("🌎 Ülke:", sorted(df['Ülke'].unique().tolist()))
            f_pa = c2.slider("🔥 PA:", 0, 200, (0, 200))
            f_yas = c2.slider("🎂 Yaş:", 14, 45, (14, 45))
            st.markdown("</div>", unsafe_allow_html=True)

            # Filtreleme
            f_df = df.copy()
            if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
            if f_mevki: f_df = f_df[f_df['Mevki'].isin(f_mevki)]
            if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]
            f_df = f_df[(f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])]
            f_df = f_df[(f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1])]

            st.write(f"### ✅ {len(f_df)} Oyuncu")
            for idx, row in f_df.head(15).iterrows():
                col1, col2 = st.columns([5, 1])
                col1.write(f"**{row['Oyuncu']}** ({row['Yaş']}) - {row['Kulüp']} | PA: {row['PA']}")
                if col2.button("⭐", key=f"fav_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast("Kaydedildi!")
            st.dataframe(f_df, use_container_width=True)

        with tabs[1]: # FAVORİLER
            res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
            if res.data:
                fav_list = [item['oyuncu_adi'] for item in res.data]
                st.dataframe(df[df['Oyuncu'].isin(fav_list)], use_container_width=True)
            else: st.info("Henüz favori yok.")
