import streamlit as st
import pandas as pd
import os
import hashlib
import json
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Pozisyonlar
ana_mevkiler = ["GK", "D C", "D L", "D R", "DM", "M C", "AM C", "AM L", "AM R", "ST"]

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 10px; padding: 15px; margin-bottom: 10px; }
    .save-box { background: rgba(0, 210, 255, 0.1); padding: 20px; border-radius: 10px; border: 1px dashed #00D2FF; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ & KAYIT SİSTEMİ ✅ ---
if st.session_state.user is None:
    st.title("🌪️ SOMEKU SCOUT")
    auth_tab = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı Adı")
    p = st.text_input("Şifre", type="password")
    
    if st.button("Devam Et"):
        hp = get_hash(p)
        if auth_tab == "Kayıt Ol":
            check = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if check.data: st.error("Bu kullanıcı adı zaten alınmış!")
            else:
                supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute()
                st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp:
                st.session_state.user = u
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£','').replace('€','').replace('M','000000').replace('K','000').replace('.','').replace(',','').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        return df

    df = load_data()
    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT
        st.subheader("Oyuncu Arama")
        col1, col2 = st.columns(2)
        n_search = col1.text_input("İsim:")
        p_filter = col2.multiselect("Mevki:", ana_mevkiler)
        
        res = df.copy()
        if n_search: res = res[res['Oyuncu'].str.contains(n_search, case=False)]
        if p_filter: res = res[res['Mevki'].apply(lambda x: any(m in str(x) for m in p_filter))]
        
        for _, r in res.head(10).iterrows():
            st.markdown(f'<div class="player-card"><b>{r["Oyuncu"]}</b> ({r["Mevki"]}) - {r["Kulüp"]} | PA: {r["PA"]}</div>', unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{r['Oyuncu']}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                st.toast("Eklendi!")

    with tabs[4]: # KADROM (KAYDETME ÖZELLİĞİ ✅)
        st.subheader("⚽ Kadro Kur ve Kaydet")
        p_list = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        c_k = st.columns(3)
        lw = c_k[0].selectbox("Sol Kanat", p_list); st_p = c_k[1].selectbox("Forvet", p_list); rw = c_k[2].selectbox("Sağ Kanat", p_list)
        
        c_m = st.columns(3)
        m1 = c_m[0].selectbox("OS 1", p_list); m2 = c_m[1].selectbox("OS 2", p_list); m3 = c_m[2].selectbox("OS 3", p_list)
        
        c_d = st.columns(4)
        lb = c_d[0].selectbox("Sol Bek", p_list); cb1 = c_d[1].selectbox("Stoper 1", p_list); cb2 = c_d[2].selectbox("Stoper 2", p_list); rb = c_d[3].selectbox("Sağ Bek", p_list)
        gk = st.selectbox("Kaleci", p_list)

        kadro_adi = st.text_input("Kadroya Bir İsim Ver:", placeholder="Örn: 2026 Şampiyon Kadro")
        if st.button("💾 Kadroyu Veritabanına Kaydet"):
            kadro_data = {
                "owner": st.session_state.user,
                "name": kadro_adi if kadro_adi else "İsimsiz Kadro",
                "players": [lw, st_p, rw, m1, m2, m3, lb, cb1, cb2, rb, gk]
            }
            # Favoriler tablosunu veya yeni bir tabloyu kullanabiliriz, şimdilik favoriler üzerinden 'Kadro:' ön ekiyle kaydedelim
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": f"KADRO:{kadro_adi}|{json.dumps(kadro_data['players'])}"}).execute()
            st.success("Kadro başarıyla kaydedildi!")

        st.divider()
        st.subheader("📂 Kayıtlı Kadrolarım")
        saved = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).like("oyuncu_adi", "KADRO:%").execute()
        if saved.data:
            for k in saved.data:
                raw = k['oyuncu_adi'].replace("KADRO:", "").split("|")
                st.expander(f"📋 {raw[0]}").write(", ".join(json.loads(raw[1])))
        else: st.info("Henüz kayıtlı bir kadronuz yok.")

    if st.sidebar.button("Çıkış"):
        st.session_state.user = None
        st.rerun()
