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

# Türkçe Pozisyon Sözlüğü
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .barrow-panel { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 12px; border: 1px solid #00D2FF; margin-bottom: 25px; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    .progress-fill { height: 8px; border-radius: 5px; transition: 0.5s; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
        if res.data and res.data[0]['password'] == get_hash(p): st.session_state.user = u; st.rerun()
        else: st.error("Hatalı!")
else:
    @st.cache_data(ttl=3600)
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£', '').replace('€', '').replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- 🕵️‍♂️ BARROW AI V35: KESİN FİLTRELEME ✅ ---
    with st.container():
        st.markdown(f'<div class="barrow-panel"><h3>🕵️‍♂️ Barrow AI</h3>{st.session_state.user}, ne arıyoruz? (Örn: "19 yaşında forvet", "İtalyan stoper", "Türk wonderkid")</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Komutunu buraya yaz...", label_visibility="collapsed").lower()
        
        if q:
            ai_df = df.copy()
            # Yaş Tespiti (Sayı yakalama)
            import re
            age_match = re.search(r'(\d+)\s*yaş', q)
            if age_match:
                target_age = int(age_match.group(1))
                ai_df = ai_df[ai_df['Yaş'] == target_age] # Takılı kalmaz, direkt o yaşı getirir ✅
            
            # Millet Tespiti
            milletler = {"türk": "Tur", "italyan": "Ita", "alman": "Ger", "fransız": "Fra", "ispanyol": "Spa", "brezilya": "Bra", "arjantin": "Arg", "afrika": "Afr"}
            for k, v in milletler.items():
                if k in q: ai_df = ai_df[ai_df['Ülke'].str.contains(v, na=False)]
            
            # Pozisyon Tespiti
            if "forvet" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("ST", na=False)]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            if "kanat" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("AM L|AM R", na=False)]

            ai_df = ai_df.sort_values(by="PA", ascending=False)
            st.write(f"✨ **Barrow Raporu:** {len(ai_df)} oyuncu bulundu.")
            cols = st.columns(3)
            for i, (idx, r) in enumerate(ai_df.head(3).iterrows()):
                tr_m = ", ".join([ana_mevkiler.get(m.strip(), m.strip()) for m in r['Mevki'].split(",")])
                cols[i].info(f"**{r['Oyuncu']}**\n\n🛡️ {r['Kulüp']}\n⚽ {tr_m}\n🎂 Yaş: {r['Yaş']} | PA: {r['PA']}")

    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT (DİNAMİK ÇUBUKLAR)
        c1, c2 = st.columns(2); search = c1.text_input("🔍 Ara:"); f_pa = c2.slider("Min PA:", 0, 200, 130)
        col_f = st.columns(3)
        f_mevki = col_f[0].multiselect("Pozisyon:", list(ana_mevkiler.keys()))
        f_ulke = col_f[1].multiselect("Ülke:", sorted(df['Ülke'].unique()))
        f_yas = col_f[2].slider("Yaş:", 14, 45, (14, 45))

        res_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: res_df = res_df[res_df['Oyuncu'].str.contains(search, case=False)]
        if f_mevki: res_df = res_df[res_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: res_df = res_df[res_df['Ülke'].isin(f_ulke)]

        for idx, row in res_df.head(10).iterrows():
            p = (row['CA']/row['PA']*100) if row['PA']>0 else 0
            color = "#FF4B4B" if p < 45 else "#00FFC2"
            st.markdown(f"""<div class="player-card"><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small><div style="background:rgba(255,255,255,0.1);height:8px;border-radius:5px;margin:10px 0;"><div class="progress-fill" style="width:{p}%; background:{color};"></div></div><small>PA: {row['PA']} | CA: {row['CA']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")

    with tabs[2]: # LİSTE (TAMİR EDİLDİ ✅)
        st.subheader("⭐ Favorilerim")
        my = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).execute()
        if my.data: st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in my.data])])

    with tabs[3]: # KIYAS (TAMİR EDİLDİ ✅)
        pl = sorted(df['Oyuncu'].tolist())
        p1 = st.selectbox("1. Oyuncu", ["-"]+pl, key="k1"); p2 = st.selectbox("2. Oyuncu", ["-"]+pl, key="k2")
        if p1 != "-" and p2 != "-": st.table(df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['PA','CA','Yaş','Değer']])

    with tabs[5]: # ADMİN (TAMİR EDİLDİ ✅)
        st.subheader("🛠️ Panel")
        logs = supabase.table("favoriler").select("*").execute()
        if logs.data: st.dataframe(pd.DataFrame(logs.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
