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

# FM Pozisyon Sözlüğü (Geri Geldi ✅)
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.95), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .ai-panel { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 25px; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    .progress-fill { background: linear-gradient(90deg, #FFD700, #00D2FF); height: 8px; border-radius: 5px; }
    .stButton>button { width: 100% !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- AUTH ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    auth = st.radio("", ["Giriş", "Kayıt"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if auth == "Kayıt": supabase.table("kullanicilar").insert({"username": u, "password": get_hash(p)}).execute(); st.success("Tamam!")
        else:
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
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- BARROW AI ASİSTANI ✅ ---
    with st.container():
        st.markdown('<div class="ai-panel"><h3>🕵️‍♂️ Barrow AI Scout</h3>Ne aramıştın? (Örn: "Genç Türk stoper", "Geleceğin Messi\'si")</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Barrow'a sor...", label_visibility="collapsed").lower()
        if q:
            ai_df = df.copy()
            if "türk" in q: ai_df = ai_df[ai_df['Ülke'].str.contains("Tür", na=False)]
            if "genç" in q: ai_df = ai_df[ai_df['Yaş'] <= 21]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            if "kanat" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("AM L|AM R", na=False)]
            if "ucuz" in q: ai_df = ai_df[ai_df['ValNum'] <= 10000000]
            if any(x in q for x in ["yıldız", "messi", "gelecek"]): ai_df = ai_df.sort_values(by="PA", ascending=False)
            st.write("✨ Barrow Önerileri:")
            cols = st.columns(3)
            for i, (idx, r) in enumerate(ai_df.head(3).iterrows()):
                cols[i].info(f"**{r['Oyuncu']}**\n\n{r['Kulüp']} | PA: {r['PA']}")

    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT (TÜM FİLTRELER GERİ GELDİ ✅)
        c1, c2 = st.columns(2)
        search = c1.text_input("🔍 Oyuncu/Kulüp:")
        f_pa = c2.slider("🔥 Min PA:", 0, 200, 130)
        
        col_f1, col_f2 = st.columns(2)
        f_mevki = col_f1.multiselect("⚽ Pozisyon:", list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_ulke = col_f2.multiselect("🌎 Ülke:", sorted(df['Ülke'].unique()))
        f_yas = st.slider("🎂 Yaş:", 14, 45, (14, 45))

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[f_df['Oyuncu'].str.contains(search, case=False) | f_df['Kulüp'].str.contains(search, case=False)]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]

        for idx, row in f_df.head(15).iterrows():
            dev = (row['CA']/row['PA']*100) if row['PA']>0 else 0
            st.markdown(f"""<div class="player-card"><div><span class="pa-badge">PA: {row['PA']}</span><span class="ca-badge">CA: {row['CA']}</span></div><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small><div style="background:rgba(255,255,255,0.1);height:8px;border-radius:5px;margin:10px 0;"><div class="progress-fill" style="width:{dev}%;"></div></div><small style="color:#00FFC2">💰 {row['Değer']}</small>""", unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]: # POPÜLER (ÇALIŞIYOR ✅)
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data: st.table(pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().head(10))

    with tabs[2]: # LİSTE (ÇALIŞIYOR ✅)
        my = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).execute()
        if my.data: st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in my.data])])

    with tabs[3]: # KIYAS (ÇALIŞIYOR ✅)
        plist = sorted(df['Oyuncu'].tolist())
        p1 = st.selectbox("1. Oyuncu", ["Seç..."]+plist, key="c1")
        p2 = st.selectbox("2. Oyuncu", ["Seç..."]+plist, key="c2")
        if p1 != "Seç..." and p2 != "Seç...": st.table(df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['PA','CA','Yaş','Kulüp','Değer']])

    with tabs[4]: # KADROM (TÜM MEVKİLER GERİ GELDİ ✅)
        st.subheader("⚽ Kadro ve Analiz")
        butce = st.number_input("Bütçe:", value=150000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        c_fw = st.columns(3); st_p = c_fw[1].selectbox("Santrafor", p_opt, key="k1"); lw_p = c_fw[0].selectbox("Sol Kanat", p_opt, key="k2"); rw_p = c_fw[2].selectbox("Sağ Kanat", p_opt, key="k3")
        c_md = st.columns(3); cm1 = c_md[0].selectbox("OS 1", p_opt, key="k4"); cm2 = c_md[1].selectbox("OS 2", p_opt, key="k5"); cm3 = c_md[2].selectbox("OS 3", p_opt, key="k6")
        c_df = st.columns(4); lb = c_df[0].selectbox("Sol Bek", p_opt, key="k7"); cb1 = c_df[1].selectbox("Stoper 1", p_opt, key="k8"); cb2 = c_df[2].selectbox("Stoper 2", p_opt, key="k9"); rb = c_df[3].selectbox("Sağ Bek", p_opt, key="k10")
        gk_p = st.selectbox("Kaleci", p_opt, key="k11")
        
        s_df = df[df['Oyuncu'].isin([st_p, lw_p, rw_p, cm1, cm2, cm3, lb, cb1, cb2, rb, gk_p])]
        if not s_df.empty:
            kalan = butce - s_df['ValNum'].sum()
            st.info(f"📊 Takım Yaş Ort: {s_df['Yaş'].mean():.1f} | PA Ort: {s_df['PA'].mean():.1f} | Kalan: {kalan:,.0f} €")

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
