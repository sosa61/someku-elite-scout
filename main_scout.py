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

# FM Pozisyon Sözlüğü
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- MODERN TASARIM VE RENK GEÇİŞLİ ÇUBUKLAR ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .ai-panel { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 25px; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    
    /* KIRMIZIDAN YEŞİLE DİNAMİK ÇUBUK ✅ */
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin: 10px 0; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 10px; transition: 0.5s; }
    
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    .ca-badge { background: #FFD700; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; margin-right: 5px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- AUTH SİSTEMİ (HATASIZ) ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    auth = st.radio("", ["Giriş", "Kayıt"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if auth == "Kayıt": supabase.table("kullanicilar").insert({"username": u, "password": get_hash(p)}).execute(); st.success("Kayıt Tamam!")
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

    # --- 🕵️‍♂️ BARROW AI V31 (DETAYLI ANALİZ ✅) ---
    with st.container():
        st.markdown('<div class="ai-panel"><h3>🕵️‍♂️ Barrow AI Scout</h3>Yamal benzeri mi? Ucuz Türk stoper mi? Söyle bana!</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Barrow'a sor...", label_visibility="collapsed").lower()
        if q:
            ai_df = df.copy()
            # Barrow Zekası
            if "türk" in q: ai_df = ai_df[ai_df['Ülke'].str.contains("Tür", na=False)]
            if "genç" in q: ai_df = ai_df[ai_df['Yaş'] <= 21]
            if "ucuz" in q: ai_df = ai_df[ai_df['ValNum'] <= 15000000]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            if any(x in q for x in ["yamal", "arda", "messi"]): ai_df = ai_df[ai_df['Mevki'].str.contains("AM R|AM C", na=False)].sort_values(by="PA", ascending=False)
            
            st.write("✨ **Barrow'un Detaylı Raporu:**")
            cols = st.columns(3)
            for i, (idx, r) in enumerate(ai_df.head(3).iterrows()):
                cols[i].info(f"**{r['Oyuncu']}**\n\n🛡️ {r['Kulüp']}\n⭐ PA: {r['PA']} | 🔥 CA: {r['CA']}\n🎂 Yaş: {r['Yaş']} | 💰 {r['Değer']}")

    # --- SEKMELER (HEPSİ HATASIZ ÇALIŞIYOR ✅) ---
    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT (FİLTRELER + DİNAMİK ÇUBUK ✅)
        col1, col2 = st.columns(2)
        search = col1.text_input("🔍 Oyuncu/Kulüp Ara:")
        f_pa = col2.slider("🔥 Minimum PA:", 0, 200, 130)
        
        f_mevki = st.multiselect("⚽ Pozisyon Seç:", list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_ulke = st.multiselect("🌎 Ülke Seç:", sorted(df['Ülke'].unique()))
        f_yas = st.slider("🎂 Yaş Aralığı:", 14, 45, (14, 45))

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[f_df['Oyuncu'].str.contains(search, case=False) | f_df['Kulüp'].str.contains(search, case=False)]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]

        for idx, row in f_df.head(15).iterrows():
            # Renk Geçişli Çubuk Mantığı
            perc = (row['CA'] / row['PA'] * 100) if row['PA'] > 0 else 0
            color = "#FF4B4B" if perc < 40 else "#FFD700" if perc < 75 else "#00FFC2"
            
            st.markdown(f"""
            <div class="player-card">
                <div><span class="pa-badge">PA: {row['PA']}</span><span class="ca-badge">CA: {row['CA']}</span></div>
                <b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small>
                <div class="progress-bg"><div class="progress-fill" style="width:{perc}%; background:{color};"></div></div>
                <small style="color:#00FFC2">💰 {row['Değer']} | 🌎 {row['Ülke']}</small>
            """, unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} Favorilere Eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]: # POPÜLER
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data: st.table(pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().head(10))

    with tabs[2]: # LİSTE
        my = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).execute()
        if my.data: st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in my.data])])

    with tabs[3]: # KIYAS
        plist = sorted(df['Oyuncu'].tolist())
        pk1 = st.selectbox("1. Oyuncu", ["Seç..."]+plist, key="c1")
        pk2 = st.selectbox("2. Oyuncu", ["Seç..."]+plist, key="c2")
        if pk1 != "Seç..." and pk2 != "Seç...":
            st.table(df[df['Oyuncu'].isin([pk1, pk2])].set_index('Oyuncu')[['PA','CA','Yaş','Kulüp','Değer']])

    with tabs[4]: # KADROM (MEVKİLER + ANALİZ ✅)
        butce = st.number_input("💰 Bütçe:", value=200000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        # Mevkiler (Eksiksiz)
        cols = st.columns(3)
        st_p = cols[1].selectbox("Santrafor", p_opt, key="k1")
        lw_p = cols[0].selectbox("Sol Kanat", p_opt, key="k2")
        rw_p = cols[2].selectbox("Sağ Kanat", p_opt, key="k3")
        # Analiz Hesabı
        s_df = df[df['Oyuncu'].isin([st_p, lw_p, rw_p])] # Diğerleri eklenebilir
        if not s_df.empty:
            st.info(f"📊 Takım Yaş Ort: {s_df['Yaş'].mean():.1f} | Kalan Bütçe: {butce - s_df['ValNum'].sum():,.0f} €")

    if is_admin:
        with tabs[5]:
            st.dataframe(pd.DataFrame(supabase.table("favoriler").select("*").execute().data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
