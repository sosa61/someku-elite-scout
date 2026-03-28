import streamlit as st
import pandas as pd
import os
import hashlib
import random
import urllib.parse
import re
from supabase import create_client, Client

# --- SUPABASE ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Türkçe Pozisyonlar (KADRO İÇİN TAM LİSTE ✅)
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .p-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .tm-lnk { display: inline-block; padding: 5px 10px; background: #1a3151; color: gold !important; border-radius: 5px; font-weight: bold; border: 1px solid gold; font-size: 11px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'seed' not in st.session_state: st.session_state.seed = random.randint(0, 9999)

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    u_in = st.text_input("Kullanıcı"); p_in = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        res = supabase.table("kullanicilar").select("*").eq("username", u_in).execute()
        if res.data and res.data[0]['password'] == get_hash(p_in): st.session_state.user = u_in; st.rerun()
        else: st.error("Hatalı!")
else:
    @st.cache_data(ttl=3600)
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£', '').replace('€', '').replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- 🕵️‍♂️ BARROW AI (MİLLET ANALİZİ TAMİR EDİLDİ ✅) ---
    with st.container():
        q = st.text_input("Barrow AI Sorgu:", placeholder="Brezilyalı forvet, 19 yaş stoper...", key="ai_q").lower()
        if st.button("🔄 Karıştır / Oyuncuları Getir"): st.session_state.seed = random.randint(0, 9999)
        if q:
            ai_df = df.copy()
            # Milletlerin her iki dilde de aranması sağlandı (Örn: Brazil veya Brezilya)
            mil_map = {"türk": "Tur", "alman": "Ger", "italyan": "Ita", "fransız": "Fra", "ispanyol": "Spa", "brezilya": "Bra", "arjantin": "Arg", "hollanda": "Ned", "portekiz": "Por"}
            for k, v in mil_map.items():
                if k in q: ai_df = ai_df[ai_df['Ülke'].str.contains(v, na=False, case=False)]
            
            age_m = re.search(r'(\d+)\s*yaş', q)
            if age_m: ai_df = ai_df[ai_df['Yaş'] == int(age_m.group(1))]
            if "forvet" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("ST", na=False)]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            
            final = ai_df.sort_values(by="PA", ascending=False).head(30)
            if not final.empty:
                show = final.sample(min(len(final), 3), random_state=st.session_state.seed)
                cols = st.columns(3)
                for i, (idx, r) in enumerate(show.iterrows()):
                    tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
                    with cols[i]:
                        st.info(f"**{r['Oyuncu']}**\n\nPA: {r['PA']} | {r['Kulüp']}\n🌎 {r['Ülke']}")
                        st.markdown(f'<a href="{tm_url}" target="_blank" class="tm-lnk">🔍 Kariyer</a>', unsafe_allow_html=True)
            else: st.warning("Barrow kimseyi bulamadı. Kriterleri değiştir Ömer!")

    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[3]: # ⚔️ KIYASLAMA (TAMİR EDİLDİ ✅)
        p_list = sorted(df['Oyuncu'].tolist())
        c1, c2 = st.columns(2)
        p1 = c1.selectbox("1. Oyuncu", ["Seç..."] + p_list, key="cmp1")
        p2 = c2.selectbox("2. Oyuncu", ["Seç..."] + p_list, key="cmp2")
        if p1 != "Seç..." and p2 != "Seç...":
            st.table(df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['PA','CA','Yaş','Mevki','Kulüp','Değer']])

    with tabs[4]: # ⚽ KADROM (TÜM MEVKİLER GERİ GELDİ ✅)
        st.subheader("⚽ Kadro Planlama")
        butce = st.number_input("💰 Transfer Bütçen:", value=200000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        row1 = st.columns(3)
        lw = row1[0].selectbox("Sol Kanat", p_opt, key="k1")
        st_p = row1[1].selectbox("Santrafor", p_opt, key="k2")
        rw = row1[2].selectbox("Sağ Kanat", p_opt, key="k3")
        
        row2 = st.columns(3)
        cm1 = row2[0].selectbox("Orta Saha 1", p_opt, key="k4")
        dm = row2[1].selectbox("Ön Libero", p_opt, key="k5")
        cm2 = row2[2].selectbox("Orta Saha 2", p_opt, key="k6")
        
        row3 = st.columns(4)
        lb = row3[0].selectbox("Sol Bek", p_opt, key="k7")
        cb1 = row3[1].selectbox("Stoper 1", p_opt, key="k8")
        cb2 = row3[2].selectbox("Stoper 2", p_opt, key="k9")
        rb = row3[3].selectbox("Sağ Bek", p_opt, key="k10")
        
        gk = st.selectbox("Kaleci", p_opt, key="k11")
        
        selected = df[df['Oyuncu'].isin([lw, st_p, rw, cm1, dm, cm2, lb, cb1, cb2, rb, gk])]
        if not selected.empty:
            kalan = butce - selected['ValNum'].sum()
            st.info(f"📊 Ortalama PA: {selected['PA'].mean():.1f} | Kalan Bütçe: {kalan:,.0f} €")

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
