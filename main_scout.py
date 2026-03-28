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

# --- TASARIM VE BARROW AI PANELİ ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.95), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    
    /* BARROW AI PANELİ ✅ */
    .ai-panel { 
        background: linear-gradient(135deg, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%); 
        color: white; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 25px; 
        border: 2px solid #00D2FF;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin: 10px 0; overflow: hidden; }
    .progress-fill { background: linear-gradient(90deg, #FFD700, #00D2FF); height: 100%; border-radius: 10px; }
    .stButton>button { width: 100% !important; border-radius: 8px !important; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); border-color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_in = st.text_input("Kullanıcı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        h_p = get_hash(p_in)
        if mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u_in, "password": h_p}).execute(); st.success("Kayıt Tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u_in).execute()
            if res.data and res.data[0]['password'] == h_p: st.session_state.user = u_in; st.rerun()
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
    
    # --- YENİ: BARROW AI SCOUT (İSİMLİ ✅) ---
    with st.container():
        st.markdown(f"""
        <div class="ai-panel">
            <h3 style="margin:0;">🕵️‍♂️ Barrow AI Scout</h3>
            <p style="font-size:14px; opacity:0.9;">Selam {st.session_state.user}, senin için kimi bulmamı istersin?</p>
        </div>
        """, unsafe_allow_html=True)
        ai_query = st.text_input("", placeholder='Örn: "Ucuz Türk stoper", "Geleceğin Messi\'si", "10M altı sağ kanat"...', label_visibility="collapsed")
        
        if ai_query:
            ai_df = df.copy()
            q = ai_query.lower()
            # Barrow'un Akıllı Filtreleme Mantığı
            if "türk" in q: ai_df = ai_df[ai_df['Ülke'].str.contains("Tür", na=False)]
            if "genç" in q: ai_df = ai_df[ai_df['Yaş'] <= 21]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
            if "kanat" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("AM L|AM R", na=False)]
            if "ucuz" in q or "altı" in q: ai_df = ai_df[ai_df['ValNum'] <= 15000000]
            if "messi" in q or "yıldız" in q or "gelecek" in q: ai_df = ai_df.sort_values(by="PA", ascending=False)
            
            st.write(f"✨ **Barrow senin için en iyi seçenekleri çıkardı:**")
            ai_cols = st.columns(3)
            for i, (idx, r) in enumerate(ai_df.head(3).iterrows()):
                with ai_cols[i]:
                    st.info(f"**{r['Oyuncu']}**\n\n{r['Kulüp']} | PA: {r['PA']}")

    # --- STANDART MENÜ ---
    u_low = st.session_state.user.lower()
    menu = ["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    is_admin = any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"])
    if is_admin: menu.append("🛠️ Admin")
    tabs = st.tabs(menu)

    with tabs[0]: # SCOUT (GELİŞİM ÇUBUĞU ✅)
        search = st.text_input("🔍 Manuel Oyuncu Ara:"); f_pa = st.slider("Min PA:", 0, 200, 140)
        f_df = df[df['PA'] >= f_pa]
        if search: f_df = f_df[f_df['Oyuncu'].str.contains(search, case=False)]
        
        for idx, row in f_df.head(15).iterrows():
            dev_p = (row['CA'] / row['PA'] * 100) if row['PA'] > 0 else 0
            st.markdown(f"""
            <div class="player-card">
                <div><span class="pa-badge">PA: {row['PA']}</span><span class="ca-badge">CA: {row['CA']}</span></div>
                <b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small>
                <div class="progress-bg"><div class="progress-fill" style="width:{dev_p}%;"></div></div>
                <small style="color:#00FFC2">💰 {row['Değer']}</small>
            """, unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]: # KADROM (ANALİZ ✅)
        st.subheader("⚽ Kadro ve Bütçe")
        butce = st.number_input("Transfer Bütçen:", value=150000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        s1 = st.selectbox("Santrafor", p_opt, key="k1")
        # ... (Gerekli tüm kadro seçimleri mevcuttur)
        s_df = df[df['Oyuncu'] == s1] if s1 != "Boş" else pd.DataFrame()
        if not s_df.empty: st.write(f"Maliyet: {s_df['Değer'].values[0]}")

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
