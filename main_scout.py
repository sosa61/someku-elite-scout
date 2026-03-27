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

# Tema
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .filter-box { background-color: rgba(25,25,25,0.95); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 20px; }
    h1 { text-align: center; color: #00D2FF; text-shadow: 0 0 10px #00D2FF; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ EKRANI ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 SOMEKU SCOUT GİRİŞ</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    with st.container():
        user = st.text_input("Kullanıcı Adı:").strip()
        password = st.text_input("Şifre:", type="password")
        if auth_mode == "Kayıt Ol" and st.button("Hesap Oluştur"):
            check = supabase.table("kullanicilar").select("*").eq("username", user).execute()
            if len(check.data) > 0: st.error("Bu kullanıcı adı alınmış!")
            else:
                supabase.table("kullanicilar").insert({"username": user, "password": make_hashes(password)}).execute()
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
        elif auth_mode == "Giriş Yap" and st.button("Bağlan"):
            res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
            if res.data and check_hashes(password, res.data[0]['password']):
                st.session_state.user = user
                st.rerun()
            else: st.error("Hatalı giriş!")
else:
    # --- VERİ YÜKLEME ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df[[1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']:
            df[col] = df[col].fillna('Unknown').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # Sekmeleri oluştur
    tab_list = ["🔍 Scouting", "⭐ Listem", "⚔️ Karşılaştır"]
    if st.session_state.user.lower() in ["someku", "ömer", "ramazan"]:
        tab_list.append("🛠️ Admin")
    
    tabs = st.tabs(tab_list)

    with tabs[0]: # SCOUTING
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        search = st.text_input("🔍 İsim veya Kulüp Ara:")
        c1, c2 = st.columns(2)
        
        # Ülke Temizleme: Çift ülkeleri tek tek ayırıp temiz bir liste sunar
        all_countries = set()
        for c in df['Ülke'].unique():
            for part in c.replace('/', ',').split(','):
                all_countries.add(part.strip())
        
        f_ulke = c1.multiselect("🌎 Ülke Seç (Tekli veya Çoklu):", sorted(list(all_countries)))
        f_mevki = c1.multiselect("⚽ Mevki:", sorted(df['Mevki'].unique().tolist()))
        f_pa = c2.slider("🔥 PA:", 0, 200, (0, 200))
        f_yas = c2.slider("🎂 Yaş:", 14, 45, (14, 45))
        st.markdown("</div>", unsafe_allow_html=True)

        # Akıllı Filtreleme
        f_df = df.copy()
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].isin(f_mevki)]
        # Ülke filtresi düzeltmesi (İçinde geçmesi yeterli)
        if f_ulke:
            f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]
        
        f_df = f_df[(f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])]
        f_df = f_df[(f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1])]

        st.success(f"{len(f_df)} oyuncu bulundu.")
        
        # Favori Ekleme Seçeneği
        target_player = st.selectbox("⭐ Listeye Eklemek İçin Oyuncu Seç:", ["Seçiniz..."] + f_df['Oyuncu'].tolist())
        if st.button("Listeme Ekle") and target_player != "Seçiniz...":
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": target_player}).execute()
            st.toast(f"{target_player} başarıyla eklendi!")

        st.dataframe(f_df, use_container_width=True)

    with tabs[1]: # LİSTEM
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            favs = [item['oyuncu_adi'] for item in res.data]
            st.dataframe(df[df['Oyuncu'].isin(favs)], use_container_width=True)
            if st.button("Listeyi Boşalt"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                st.rerun()
        else: st.info("Listeniz boş.")

    with tabs[2]: # KARŞILAŞTIR
        st.subheader("⚔️ Oyuncu Kıyaslama")
        plist = sorted(df['Oyuncu'].tolist())
        sc1, sc2 = st.columns(2)
        p1 = sc1.selectbox("1. Oyuncu", ["Seç..."] + plist)
        p2 = sc2.selectbox("2. Oyuncu", ["Seç..."] + plist)
        
        if p1 != "Seç..." and p2 != "Seç...":
            d1 = df[df['Oyuncu'] == p1].iloc[0]
            d2 = df[df['Oyuncu'] == p2].iloc[0]
            
            comp_data = {
                "Özellik": ["PA", "CA", "Yaş", "Kulüp", "Mevki", "Değer"],
                p1: [d1['PA'], d1['CA'], d1['Yaş'], d1['Kulüp'], d1['Mevki'], d1['Değer']],
                p2: [d2['PA'], d2['CA'], d2['Yaş'], d2['Kulüp'], d2['Mevki'], d2['Değer']]
            }
            st.table(pd.DataFrame(comp_data))

    if len(tab_list) > 3: # ADMIN
        with tabs[3]:
            st.subheader("🛠️ Admin Kontrol Paneli")
            adm_res = supabase.table("favoriler").select("*").execute()
            if adm_res.data:
                st.write("Son Favori İşlemleri:")
                st.dataframe(pd.DataFrame(adm_res.data).tail(50))
            else: st.write("Henüz kayıt yok.")

    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()
