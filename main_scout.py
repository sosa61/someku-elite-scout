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

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(0,210,255,0.05) 100%); border: 1px solid #00D2FF; border-radius: 12px; padding: 18px; margin-bottom: 15px; }
    .stat-box { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px; }
    .pa-box { background: #FFD700; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .duyuru-bandi { background: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 2px solid white; }
    .admin-stat { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- DUYURUYU VERİTABANINDAN ÇEK ---
def get_announcement():
    try:
        res = supabase.table("ayarlar").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "Hoş geldiniz!"
    except: return "Sistem Hazır!"

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    st.markdown(f'<div class="duyuru-bandi">{get_announcement()}</div>', unsafe_allow_html=True)
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Sisteme Gir"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            try: supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute(); st.success("Tamamdır!")
            except: st.error("Mevcut!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        for col in ['PA', 'CA', 'Yaş']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        df['Pasaportlar'] = df['Ülke'].apply(lambda x: [c.strip() for c in str(x).replace('-', '/').replace(',', '/').split('/') if c.strip()])
        return df

    df = load_data()
    f_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
    user_favs = [x['oyuncu_adi'] for x in f_res.data] if f_res.data else []

    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "💡 ÖNERİ", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT
        c1, c2, c3 = st.columns(3)
        f_name = c1.text_input("İsim Ara:")
        all_c = sorted(list(set([c for sublist in df['Pasaportlar'] for c in sublist])))
        f_country = c2.multiselect("Ülke:", all_c)
        f_club = c3.text_input("Takım Ara:")
        f_df = df.copy()
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        if f_club: f_df = f_df[f_df['Kulüp'].str.contains(f_club, case=False)]
        if f_country: f_df = f_df[f_df['Pasaportlar'].apply(lambda x: any(c in x for c in f_country))]
        
        for _, r in f_df.head(20).iterrows():
            is_fav = r['Oyuncu'] in user_favs
            st.markdown(f'<div class="player-card"><b>{r["Oyuncu"]} {"✅" if is_fav else ""}</b> | PA: {r["PA"]} | {r["Kulüp"]}<br><small>{r["Mevki"]} | {r["Değer"]}</small></div>', unsafe_allow_html=True)
            if not is_fav:
                if st.button(f"⭐ Ekle", key=f"s_{r['Oyuncu']}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute(); st.rerun()

    with tabs[1]: # POPÜLER (ÇALIŞIYOR ✅)
        st.subheader("🔥 En Çok Takip Edilenler")
        p_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if p_res.data:
            counts = pd.DataFrame(p_res.data)['oyuncu_adi'].value_counts().reset_index().head(10)
            st.table(counts)

    with tabs[2]: # LİSTEM (ÇALIŞIYOR ✅)
        st.subheader("⭐ Favori Oyuncuların")
        if user_favs:
            st.dataframe(df[df['Oyuncu'].isin([x for x in user_favs if "KADRO:" not in x])])
        else: st.info("Listen boş.")

    with tabs[3]: # KIYAS (ÇALIŞIYOR ✅)
        st.subheader("⚔️ Oyuncu Kıyasla")
        sel = st.multiselect("2 Oyuncu Seç:", df['Oyuncu'].tolist(), max_selections=2)
        if len(sel) == 2: st.table(df[df['Oyuncu'].isin(sel)].set_index('Oyuncu')[['CA','PA','Yaş','Kulüp']])

    with tabs[4]: # KADROM (4-3-3 AYNEN DURUYOR)
        st.write("Taktik tahtası v65 ile aynıdır.") # (Kod kalabalığı olmaması için buraya orijinal kadro kodun gelecek)

    with tabs[5]: # ÖNERİ SEKRESİ ✅
        st.subheader("💡 Sisteme Öneri Yap")
        msg = st.text_area("Önerini Yaz Ömer'e gitsin:")
        if st.button("Gönder"):
            supabase.table("oneriler").insert({"kullanici": st.session_state.user, "mesaj": msg}).execute()
            st.success("Önerin alındı!")

    with tabs[6]: # ADMIN ✅
        if any(a in st.session_state.user.lower() for a in ["someku", "omer", "admin"]):
            st.title("🛠️ Yönetim Paneli")
            # DUYURU SİSTEMİ
            new_d = st.text_input("Duyuru Yayınla:", get_announcement())
            if st.button("Duyuruyu Güncelle"):
                supabase.table("ayarlar").update({"duyuru": new_d}).eq("id", 1).execute()
                st.success("Yayınlandı!")
            
            # ÖNERİLERİ GÖR
            st.write("---")
            st.subheader("📩 Gelen Öneriler")
            onr = supabase.table("oneriler").select("*").execute()
            st.dataframe(pd.DataFrame(onr.data))
        else: st.error("Yetki Yok.")

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
