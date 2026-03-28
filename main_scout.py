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

# Türkçe Açıklamalı Pozisyonlar ✅
pozisyon_map = {
    "GK": "Kaleci (GK)", "D C": "Stoper (DC)", "D L": "Sol Bek (DL)", "D R": "Sağ Bek (DR)", 
    "DM": "Ön Libero (DM)", "M C": "Orta Saha (MC)", "AM C": "On Numara (AMC)", 
    "AM L": "Sol Kanat (AML)", "AM R": "Sağ Kanat (AMR)", "ST": "Forvet (ST)"
}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM (MAVİ-BEYAZ TM BUTONU ✅) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .tm-button { display: inline-block; padding: 6px 14px; background-color: #001e3f; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #ffffff; font-size: 13px; margin-top: 10px; }
    .tm-button:hover { background-color: #003366; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ & KAYIT ---
if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute()
            st.success("Kayıt Başarılı! Giriş yapabilirsiniz.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp:
                st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        return df

    df = load_data()
    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT (TÜM FİLTRELER GERİ GELDİ ✅)
        st.subheader("Gelişmiş Filtreleme")
        c1, c2 = st.columns(2)
        f_name = c1.text_input("Oyuncu İsmi:")
        f_country = c2.multiselect("Ülke Seç:", sorted(df['Ülke'].unique()))
        
        c3, c4 = st.columns(2)
        f_pa = c3.slider("Minimum Potansiyel (PA):", 0, 200, 100)
        f_age = c4.slider("Yaş Aralığı:", 15, 45, (15, 45))
        
        f_pos = st.multiselect("Pozisyon Seç (Türkçe):", list(pozisyon_map.keys()), format_func=lambda x: pozisyon_map[x])
        
        # Filtreleme Uygula
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        if f_country: f_df = f_df[f_df['Ülke'].isin(f_country)]
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]
        
        for _, r in f_df.head(15).iterrows():
            # TM Arama Düzeltildi (Direkt oyuncu profili hedefli) ✅
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
            st.markdown(f"""
            <div class="player-card">
                <b>{r['Oyuncu']}</b> ({r['Yaş']}) | {r['Kulüp']}<br>
                <small>Mevki: {r['Mevki']} | PA: {r['PA']} | Ülke: {r['Ülke']}</small><br>
                <a href="{tm_url}" target="_blank" class="tm-button">🔍 Transfermarkt Profili</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"⭐ Listeye Ekle", key=f"add_{r['Oyuncu']}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                st.toast("Eklendi!")

    with tabs[1]: # POPÜLER
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data:
            counts = pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().reset_index()
            counts.columns = ['Oyuncu', 'Takip Sayısı']
            st.table(counts.head(10))

    with tabs[2]: # LİSTEM (TAMİR EDİLDİ ✅)
        my_list = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if my_list.data:
            st.dataframe(df[df['Oyuncu'].isin([x['oyuncu_adi'] for x in my_list.data])][['Oyuncu','Yaş','PA','Mevki','Değer']])
        else: st.info("Listen boş.")

    with tabs[3]: # KIYAS (TAMİR EDİLDİ ✅)
        p_opt = sorted(df['Oyuncu'].tolist())
        o1 = st.selectbox("1. Oyuncu", ["Seç"] + p_opt, key="o1")
        o2 = st.selectbox("2. Oyuncu", ["Seç"] + p_opt, key="o2")
        if o1 != "Seç" and o2 != "Seç":
            st.table(df[df['Oyuncu'].isin([o1, o2])].set_index('Oyuncu')[['PA','CA','Yaş','Mevki','Değer']])

    with tabs[4]: # KADROM (TÜM MEVKİLER ✅)
        st.subheader("11 Pozisyonlu Kadro Planı")
        all_p = ["Boş"] + sorted(df['Oyuncu'].tolist())
        row1 = st.columns(3)
        lw = row1[0].selectbox("Sol Kanat (AML)", all_p); st_p = row1[1].selectbox("Forvet (ST)", all_p); rw = row1[2].selectbox("Sağ Kanat (AMR)", all_p)
        row2 = st.columns(3)
        m1 = row2[0].selectbox("Orta Saha (MC) 1", all_p); dm = row2[1].selectbox("Ön Libero (DM)", all_p); m2 = row2[2].selectbox("Orta Saha (MC) 2", all_p)
        row3 = st.columns(4)
        lb = row3[0].selectbox("Sol Bek (DL)", all_p); cb1 = row3[1].selectbox("Stoper (DC) 1", all_p); cb2 = row3[2].selectbox("Stoper (DC) 2", all_p); rb = row3[3].selectbox("Sağ Bek (DR)", all_p)
        gk = st.selectbox("Kaleci (GK)", all_p)
        
        k_adi = st.text_input("Kadro İsmi:")
        if st.button("💾 Kadroyu Kaydet"):
            k_data = f"KADRO:{k_adi}|{json.dumps([lw, st_p, rw, m1, dm, m2, lb, cb1, cb2, rb, gk])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute()
            st.success("Kadro Kaydedildi!")

    with tabs[5]: # ADMIN (TAMİR EDİLDİ ✅)
        if "someku" in st.session_state.user.lower() or "omer" in st.session_state.user.lower():
            logs = supabase.table("favoriler").select("*").execute()
            st.dataframe(pd.DataFrame(logs.data))
        else: st.error("Yetkiniz yok.")

    if st.sidebar.button("Çıkış"):
        st.session_state.user = None; st.rerun()
