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

# Türkçe Pozisyonlar
pozisyon_map = {
    "GK": "Kaleci (GK)", "D C": "Stoper (DC)", "D L": "Sol Bek (DL)", "D R": "Sağ Bek (DR)", 
    "DM": "Ön Libero (DM)", "M C": "Orta Saha (MC)", "AM C": "On Numara (AMC)", 
    "AM L": "Sol Kanat (AML)", "AM R": "Sağ Kanat (AMR)", "ST": "Forvet (ST)"
}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .tm-button { display: inline-block; padding: 6px 14px; background-color: #001e3f; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #ffffff; font-size: 13px; margin-top: 10px; }
    .pitch-sector { background: rgba(0, 210, 255, 0.08); border-left: 5px solid #00D2FF; padding: 10px; margin-bottom: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ SİSTEMİ ---
if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute()
            st.success("Kayıt Başarılı!")
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
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        # Ülke Temizliği (Sadece ilk ismi al)
        df['Ulke_Temiz'] = df['Ülke'].apply(lambda x: str(x).split('/')[0].strip())
        return df

    df = load_data()
    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT (YAŞ FİLTRESİ GERİ GELDİ ✅)
        st.subheader("Gelişmiş Scout")
        c1, c2 = st.columns(2)
        f_name = c1.text_input("İsim Ara:")
        f_country = c2.multiselect("Ülke Seç (Tekli):", sorted(df['Ulke_Temiz'].unique()))
        
        c3, c4 = st.columns(2)
        f_pa = c3.slider("Min PA:", 0, 200, 100)
        f_age = c4.slider("Yaş Aralığı:", 15, 45, (15, 45)) # Yaş filtresi eklendi ✅
        
        f_pos = st.multiselect("Pozisyon:", list(pozisyon_map.keys()), format_func=lambda x: pozisyon_map[x])
        
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        
        if f_country:
            milli = ["Kenan Yıldız", "Can Uzun", "Ferdi Kadıoğlu"]
            if 'Turkey' in f_country:
                f_df = f_df[(f_df['Ulke_Temiz'].isin(f_country)) | (f_df['Oyuncu'].isin(milli))]
            else:
                f_df = f_df[f_df['Ulke_Temiz'].isin(f_country)]
        
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]
        
        for _, r in f_df.head(20).iterrows():
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
            st.markdown(f"""<div class="player-card"><b>{r['Oyuncu']}</b> ({r['Yaş']}) | {r['Kulüp']}<br><small>CA: {r['CA']} | PA: {r['PA']} | {r['Mevki']}</small><br><a href="{tm_url}" target="_blank" class="tm-button">🔍 Transfermarkt</a></div>""", unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"s_{r['Oyuncu']}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                st.toast("Eklendi!")

    with tabs[1]: # POPÜLER (TAMİR EDİLDİ ✅)
        st.subheader("En Çok Takip Edilenler")
        p_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if p_res.data:
            counts = pd.DataFrame(p_res.data)['oyuncu_adi'].value_counts().reset_index()
            counts.columns = ['Oyuncu', 'Takip']
            st.table(counts.head(10))

    with tabs[2]: # LİSTEM (TAMİR EDİLDİ ✅)
        st.subheader("Favorilerim")
        m_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if m_res.data:
            f_names = [x['oyuncu_adi'] for x in m_res.data if "KADRO:" not in x['oyuncu_adi']]
            st.dataframe(df[df['Oyuncu'].isin(f_names)][['Oyuncu','Yaş','CA','PA','Mevki']])
        else: st.info("Liste boş.")

    with tabs[3]: # KIYAS (TAMİR EDİLDİ ✅)
        st.subheader("Kıyasla")
        o_list = sorted(df['Oyuncu'].tolist())
        p1 = st.selectbox("1. Oyuncu", ["Seç"] + o_list, key="k1")
        p2 = st.selectbox("2. Oyuncu", ["Seç"] + o_list, key="k2")
        if p1 != "Seç" and p2 != "Seç":
            st.table(df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['CA','PA','Yaş','Mevki','Değer']])

    with tabs[4]: # KADROM (SAHA DİZİLİŞİ - DOKUNULMADI ✅)
        st.subheader("⚽ Taktik Tahtası (4-3-3)")
        all_p = ["Boş"] + sorted(df['Oyuncu'].tolist())
        st.markdown('<div class="pitch-sector">FORVET</div>', unsafe_allow_html=True)
        cfw = st.columns(3); lw = cfw[0].selectbox("AML", all_p); stp = cfw[1].selectbox("ST", all_p); rw = cfw[2].selectbox("AMR", all_p)
        st.markdown('<div class="pitch-sector">ORTA SAHA</div>', unsafe_allow_html=True)
        cmid = st.columns(3); m1 = cmid[0].selectbox("MC 1", all_p); dm = cmid[1].selectbox("DM", all_p); m2 = cmid[2].selectbox("MC 2", all_p)
        st.markdown('<div class="pitch-sector">DEFANS</div>', unsafe_allow_html=True)
        cdef = st.columns(4); lb = cdef[0].selectbox("DL", all_p); cb1 = cdef[1].selectbox("DC 1", all_p); cb2 = cdef[2].selectbox("DC 2", all_p); rb = cdef[3].selectbox("DR", all_p)
        gk = st.selectbox("GK", all_p)
        k_adi = st.text_input("Kadro İsmi:")
        if st.button("💾 Kadroyu Kaydet"):
            k_data = f"KADRO:{k_adi}|{json.dumps([lw, stp, rw, m1, dm, m2, lb, cb1, cb2, rb, gk])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute()
            st.success("Kadro Kaydedildi!")

    with tabs[5]: # ADMIN (TAMİR EDİLDİ ✅)
        if any(x in st.session_state.user.lower() for x in ["someku", "omer"]):
            adm = supabase.table("favoriler").select("*").execute()
            st.dataframe(pd.DataFrame(adm.data))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
