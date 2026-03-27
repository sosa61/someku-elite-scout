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

# FM POZİSYON SÖZLÜĞÜ (Ömer için)
pozisyon_sozlugu = {
    "GK": "Kaleci",
    "D C": "Stoper",
    "D L": "Sol Bek",
    "D R": "Sağ Bek",
    "DM": "Ön Libero",
    "M C": "Orta Saha",
    "M L": "Sol Orta Saha",
    "M R": "Sağ Orta Saha",
    "AM C": "On Numara",
    "AM L": "Sol Kanat",
    "AM R": "Sağ Kanat",
    "ST": "Forvet",
    "S C": "Santrafor",
    "WB L": "Sol Kanat Bek",
    "WB R": "Sağ Kanat Bek"
}

def turkcelestir(mevki):
    # Karmaşık mevkileri (Örn: AM LC) parçalayıp çevirir
    parcalar = mevki.replace("/", " ").split()
    ceviriler = [pozisyon_sozlugu.get(p, p) for p in parcalar]
    return f"{mevki} ({', '.join(ceviriler)})"

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return hashed_text if make_hashes(password) == hashed_text else False

# Tema
st.markdown("""<style>.stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.9), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }</style>""", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    user = st.text_input("Kullanıcı Adı").strip()
    password = st.text_input("Şifre", type="password")
    if st.button("Devam Et"):
        if mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": user, "password": make_hashes(password)}).execute()
            st.success("Kayıt tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", user).execute()
            if res.data and check_hashes(password, res.data[0]['password']):
                st.session_state.user = user
                st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
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
    
    tabs = st.tabs(["🔍 Scouting", "⭐ Listem", "⚔️ Kıyasla"])

    with tabs[0]:
        st.markdown("<div style='background:rgba(20,20,20,0.9);padding:15px;border-radius:10px;border:1px solid #00D2FF'>", unsafe_allow_html=True)
        search = st.text_input("🔍 İsim/Kulüp Ara:")
        
        # MEVKİ TÜRKÇELEŞTİRME BURADA ✅
        mevkiler = sorted(df['Mevki'].unique().tolist())
        mevki_secenekleri = {m: turkcelestir(m) for m in mevkiler}
        f_mevki_kodlar = st.multiselect("⚽ Mevki (Türkçe Açıklamalı):", options=list(mevki_secenekleri.keys()), format_func=lambda x: mevki_secenekleri[x])
        
        countries = set()
        for v in df['Ülke'].unique():
            for c in v.replace('/', ',').split(','): countries.add(c.strip())
        f_ulke = st.multiselect("🌎 Ülke:", sorted(list(countries)))
        
        c1, c2 = st.columns(2)
        f_pa = c1.slider("🔥 PA:", 0, 200, (0, 200))
        f_yas = c2.slider("🎂 Yaş:", 14, 45, (14, 45))
        st.markdown("</div>", unsafe_allow_html=True)

        f_df = df.copy()
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki_kodlar: f_df = f_df[f_df['Mevki'].isin(f_mevki_kodlar)]
        if f_ulke: f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]
        f_df = f_df[(f_df['PA'] >= f_pa[0]) & (f_df['PA'] <= f_pa[1]) & (f_df['Yaş'] >= f_yas[0]) & (f_df['Yaş'] <= f_yas[1])]

        st.subheader(f"✅ {len(f_df)} Oyuncu")
        p_sel = st.selectbox("⭐ Ekle:", ["Seç..."] + f_df['Oyuncu'].tolist())
        if st.button("Kaydet") and p_sel != "Seç...":
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_sel}).execute()
            st.toast("Eklendi!")
        st.dataframe(f_df, use_container_width=True)

    with tabs[1]: # LİSTEM
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in res.data])], use_container_width=True)
            if st.button("Tümünü Sil"): supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute(); st.rerun()

    with tabs[2]: # KIYASLA
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("1. Oyuncu", ["Seç..."] + sorted(df['Oyuncu'].tolist()), key="k1")
        p2 = c2.selectbox("2. Oyuncu", ["Seç..."] + sorted(df['Oyuncu'].tolist()), key="k2")
        if p1 != "Seç..." and p2 != "Seç...":
            r1, r2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.table(pd.DataFrame({"Özellik": ["PA", "CA", "Yaş", "Kulüp"], p1: [r1['PA'], r1['CA'], r1['Yaş'], r1['Kulüp']], p2: [r2['PA'], r2['CA'], r2['Yaş'], r2['Kulüp']]}))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
