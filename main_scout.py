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
    .filter-box { background-color: rgba(20,20,20,0.98); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 20px; }
    h1 { text-align: center; color: #00D2FF; font-size: 28px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state:
    st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ YAP VEYA KAYIT OL</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Giriş")
        l_user = st.text_input("Kullanıcı Adı", key="login_u").strip()
        l_pass = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Bağlan"):
            res = supabase.table("kullanicilar").select("*").eq("username", l_user).execute()
            if res.data and check_hashes(l_pass, res.data[0]['password']):
                st.session_state.user = l_user
                st.rerun()
            else:
                st.error("Hatalı giriş!")
    with c2:
        st.subheader("Yeni Kayıt")
        r_user = st.text_input("Kullanıcı Adı Seç", key="reg_u").strip()
        r_pass = st.text_input("Şifre Seç", type="password", key="reg_p")
        if st.button("Hesap Aç"):
            supabase.table("kullanicilar").insert({"username": r_user, "password": make_hashes(r_pass)}).execute()
            st.success("Kayıt Başarılı! Şimdi Giriş Yapabilirsin.")

else:
    # --- VERİ YÜKLEME ---
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"):
            return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']:
            df[col] = df[col].fillna('---').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    tab_names = ["🔍 Scouting", "⭐ Listem", "⚔️ Kıyasla"]
    if st.session_state.user.lower() in ["someku", "ömer", "ramazan"]:
        tab_names.append("🛠️ Admin")
    
    tabs = st.tabs(tab_names)

    with tabs[0]: # SCOUTING
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        search = st.text_input("🔍 İsim veya Kulüp Ara:")
        countries = set()
        for val in df['Ülke'].unique():
            for c in val.replace('/', ',').split(','):
                countries.add(c.strip())
        f_ulke = st.multiselect("🌎 Ülke Seç:", sorted(list(countries)))
        f_mevki = st.multiselect("⚽ Mevki:", sorted(df['Mevki'].unique().tolist()))
        c1, c2 = st.columns(2)
        f_pa = c1.slider("🔥 PA:", 0, 200, (0, 200))
        f_yas = c2.slider("🎂 Yaş:", 14, 45, (14, 45))
        st.markdown("</div>", unsafe_allow_html=True)

        f_df = df.copy()
        if search:
            f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki:
            f_df = f_df[f_df['Mevki'].isin(f_mevki)]
        if f_ulke:
            f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]
        f_df = f_df[(f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1])]
        f_df = f_df[(f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1])]

        st.info("Listeye eklemek için aşağıdaki kutudan seçim yap:")
        p_select = st.selectbox("Oyuncu Seç:", ["Seçiniz..."] + f_df['Oyuncu'].tolist())
        if st.button("⭐ Listeme Ekle") and p_select != "Seçiniz...":
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_select}).execute()
            st.toast(f"{p_select} kaydedildi!")
        
        st.dataframe(f_df, use_container_width=True)

    with tabs[1]: # LİSTEM
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            fav_names = [i['oyuncu_adi'] for i in res.data]
            st.dataframe(df[df['Oyuncu'].isin(fav_names)], use_container_width=True)
            if st.button("Temizle"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                st.rerun()
        else:
            st.info("Listen boş.")

    with tabs[2]: # KIYASLA
        st.subheader("⚔️ Oyuncu Karşılaştırma")
        c1, c2 = st.columns(2)
        all_p = sorted(df['Oyuncu'].tolist())
        p1 = c1.selectbox("1. Oyuncu", ["Seç..."] + all_p, key="p1_sel")
        p2 = c2.selectbox("2. Oyuncu", ["Seç..."] + all_p, key="p2_sel")
        if p1 != "Seç..." and p2 != "Seç...":
            r1, r2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            compare_df = pd.DataFrame({
                "Özellik": ["PA", "CA", "Yaş", "Mevki", "Kulüp", "Değer"],
                p1: [r1['PA'], r1['CA'], r1['Yaş'], r1['Mevki'], r1['Kulüp'], r1['Değer']],
                p2: [r2['PA'], r2['CA'], r2['Yaş'], r2['Mevki'], r2['Kulüp'], r2['Değer']]
            })
            st.table(compare_df)

    if len(tab_names) > 3: # ADMIN
        with tabs[3]:
            st.subheader("🛠️ Admin Paneli")
            adm_res = supabase.table("favoriler").select("*").execute()
            if adm_res.data:
                st.dataframe(pd.DataFrame(adm_res.data).tail(30))

    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None
        st.rerun()
