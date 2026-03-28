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

# --- TASARIM VE ADMIN KARTLARI ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .admin-card { 
        background: rgba(0, 210, 255, 0.1); 
        border: 1px solid #00D2FF; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center;
    }
    .player-card { 
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(0,210,255,0.05) 100%);
        border: 1px solid #00D2FF; 
        border-radius: 12px; padding: 18px; margin-bottom: 15px;
    }
    .stat-box { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px; }
    .pa-box { background: #FFD700; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .duyuru-bandi { background: #FF4B4B; color: white; padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- DUYURU MESAJI (Burayı değiştirirsen sitede görünür) ---
duyuru_metni = "🚀 Yeni FM 24 Verileri Sisteme Yüklendi! İyi Scoutlar Ömer."

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    st.markdown(f'<div class="duyuru-bandi">{duyuru_metni}</div>', unsafe_allow_html=True)
    auth = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı Adı"); p = st.text_input("Şifre", type="password")
    if st.button("Sisteme Gir"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            try: supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Bu kullanıcı mevcut.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı bilgiler!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        df['Pasaportlar'] = df['Ülke'].apply(lambda x: [c.strip() for c in str(x).replace('-', '/').replace(',', '/').split('/') if c.strip()])
        return df

    df = load_data()
    user_favs_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
    user_favs = [x['oyuncu_adi'] for x in user_favs_res.data] if user_favs_res.data else []

    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    # ... (Scout, Popüler, Listem, Kıyas, Kadrom sekmeleri V65 ile aynı - Değişmedi) ...
    # [Buradaki kodları yer tasarrufu için özet geçiyorum ama senin dosyanın içinde tam halleri kalacak]

    with tabs[5]: # Gelişmiş Admin Paneli ✅
        if any(admin_name in st.session_state.user.lower() for admin_name in ["someku", "omer", "admin"]):
            st.title("🛠️ Yönetim Paneli")
            
            # Veri Çekme
            all_users = supabase.table("kullanicilar").select("username").execute()
            all_favs = supabase.table("favoriler").select("*").execute()
            fav_df = pd.DataFrame(all_favs.data) if all_favs.data else pd.DataFrame()

            # Üst Özet Kartları
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="admin-card"><h3>👥 Kullanıcılar</h3><h2>{len(all_users.data)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="admin-card"><h3>⭐ Toplam Favori</h3><h2>{len(fav_df)}</h2></div>', unsafe_allow_html=True)
            if not fav_df.empty:
                active_user = fav_df['kullanici_adi'].value_counts().idxmax()
                c3.markdown(f'<div class="admin-card"><h3>🔥 En Aktif</h3><h2>{active_user}</h2></div>', unsafe_allow_html=True)

            st.write("---")
            
            # Detaylı Tablo ve Filtreleme
            st.subheader("Favori Hareketleri")
            if not fav_df.empty:
                u_filter = st.selectbox("Kullanıcıya Göre Filtrele:", ["Tümü"] + list(fav_df['kullanici_adi'].unique()))
                display_df = fav_df if u_filter == "Tümü" else fav_df[fav_df['kullanici_adi'] == u_filter]
                st.dataframe(display_df[['kullanici_adi', 'oyuncu_adi', 'created_at']], use_container_width=True)
            else:
                st.info("Henüz favori işlemi yapılmamış.")
        else:
            st.warning("Bu alana giriş yetkiniz yok Ömer.")

    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()
