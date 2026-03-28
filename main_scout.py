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

# Türkçe Pozisyon Açıklamaları
pozisyon_map = {
    "GK": "Kaleci (GK)", "D C": "Stoper (DC)", "D L": "Sol Bek (DL)", "D R": "Sağ Bek (DR)", 
    "DM": "Ön Libero (DM)", "M C": "Orta Saha (MC)", "AM C": "On Numara (AMC)", 
    "AM L": "Sol Kanat (AML)", "AM R": "Sağ Kanat (AMR)", "ST": "Forvet (ST)"
}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM (MAVİ-BEYAZ TRANSFERMARKT) ---
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
    auth = st.radio("İşlem Seç:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute()
            st.success("Kayıt Başarılı! Şimdi giriş yapabilirsiniz.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp:
                st.session_state.user = u; st.rerun()
            else: st.error("Hatalı Giriş!")
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

    with tabs[0]: # SCOUT (AKILLI ÜLKE FİLTRESİ ✅)
        st.subheader("Gelişmiş Scout")
        c1, c2 = st.columns(2)
        f_name = c1.text_input("Oyuncu İsmi Ara:")
        f_country = c2.multiselect("Ülke Seç:", sorted(df['Ülke'].unique()))
        
        c3, c4 = st.columns(2)
        f_pa = c3.slider("Min PA:", 0, 200, 100)
        f_age = c4.slider("Yaş Aralığı:", 15, 45, (15, 45))
        
        f_pos = st.multiselect("Pozisyon (Türkçe):", list(pozisyon_map.keys()), format_func=lambda x: pozisyon_map[x])
        
        # --- AKILLI FİLTRELEME MANTIĞI ---
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        
        if f_country:
            # Kenan Yıldız ve Diğer Gurbetçiler İçin Global Kural ✅
            # Eğer seçilen ülke 'Turkey' ise, dosyadaki ülkesi farklı olsa bile bu isimleri dahil et
            gurbetci_listesi = ["Kenan Yıldız", "Can Uzun", "Ferdi Kadıoğlu", "Hakan Çalhanoğlu", "Salih Özcan"]
            if 'Turkey' in f_country:
                f_df = f_df[(f_df['Ülke'].isin(f_country)) | (f_df['Oyuncu'].isin(gurbetci_listesi))]
            else:
                f_df = f_df[f_df['Ülke'].isin(f_country)]
        
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]
        
        for _, r in f_df.head(20).iterrows():
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
            st.markdown(f"""
            <div class="player-card">
                <b>{r['Oyuncu']}</b> ({r['Yaş']}) | {r['Kulüp']}<br>
                <small>Pozisyon: {r['Mevki']} | PA: {r['PA']} | Ülke: {r['Ülke']}</small><br>
                <a href="{tm_url}" target="_blank" class="tm-button">🔍 Transfermarkt Kariyer</a>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{r['Oyuncu']}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                st.toast(f"{r['Oyuncu']} Listeye Eklendi!")

    with tabs[1]: # POPÜLER
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data:
            counts = pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().reset_index()
            counts.columns = ['Oyuncu', 'Takip']
            st.table(counts.head(10))

    with tabs[2]: # LİSTEM
        my = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if my.data:
            st.dataframe(df[df['Oyuncu'].isin([x['oyuncu_adi'] for x in my.data])][['Oyuncu','Yaş','PA','Mevki','Kulüp']])
        else: st.info("Listen henüz boş.")

    with tabs[3]: # KIYAS
        p_opt = sorted(df['Oyuncu'].tolist())
        o1 = st.selectbox("1. Oyuncu", ["Seç"] + p_opt, key="o1")
        o2 = st.selectbox("2. Oyuncu", ["Seç"] + p_opt, key="o2")
        if o1 != "Seç" and o2 != "Seç":
            st.table(df[df['Oyuncu'].isin([o1, o2])].set_index('Oyuncu')[['PA','CA','Yaş','Mevki','Değer']])

    with tabs[4]: # KADROM (11 MEVKİ TAMAM ✅)
        st.subheader("Kadro Planla & Kaydet")
        all_p = ["Boş"] + sorted(df['Oyuncu'].tolist())
        c_fw = st.columns(3); lw = c_fw[0].selectbox("Sol Kanat (AML)", all_p); st_p = c_fw[1].selectbox("Forvet (ST)", all_p); rw = c_fw[2].selectbox("Sağ Kanat (AMR)", all_p)
        c_mid = st.columns(3); m1 = c_mid[0].selectbox("Orta Saha 1", all_p); dm = c_mid[1].selectbox("Ön Libero", all_p); m2 = c_mid[2].selectbox("Orta Saha 2", all_p)
        c_def = st.columns(4); lb = c_def[0].selectbox("Sol Bek", all_p); cb1 = c_def[1].selectbox("Stoper 1", all_p); cb2 = c_def[2].selectbox("Stoper 2", all_p); rb = c_def[3].selectbox("Sağ Bek", all_p)
        gk = st.selectbox("Kaleci (GK)", all_p)
        
        k_adi = st.text_input("Kadro İsmi:")
        if st.button("💾 Kaydet"):
            k_data = f"KADRO:{k_adi}|{json.dumps([lw, st_p, rw, m1, dm, m2, lb, cb1, cb2, rb, gk])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute()
            st.success("Kadro Veritabanına İşlendi!")

    with tabs[5]: # ADMIN
        if any(x in st.session_state.user.lower() for x in ["someku", "omer", "ramazan"]):
            logs = supabase.table("favoriler").select("*").execute()
            st.dataframe(pd.DataFrame(logs.data))
        else: st.error("Yetkiniz yok.")

    if st.sidebar.button("Çıkış"):
        st.session_state.user = None; st.rerun()
