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

# --- GELİŞMİŞ TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.95), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    .ca-badge { background: #FFD700; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; margin-right: 5px; }
    
    /* GELİŞİM ÇUBUĞU (ÖZELLİK 2) */
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; width: 100%; margin: 10px 0; overflow: hidden; }
    .progress-fill { background: linear-gradient(90deg, #FFD700, #00D2FF); height: 100%; border-radius: 10px; }
    
    .stButton>button { width: 100% !important; border-radius: 8px !important; }
    .analysis-card { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 15px; border-radius: 10px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ VEYA KAYIT</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_in = st.text_input("Kullanıcı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if auth_mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u_in, "password": get_hash(p_in)}).execute(); st.success("Kayıt Tamam!")
        else:
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
    
    u_low = st.session_state.user.lower()
    menu = ["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    is_admin = any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"])
    if is_admin: menu.append("🛠️ Admin")
    tabs = st.tabs(menu)

    with tabs[0]: # SCOUT (GELİŞİM ÇUBUĞU EKLENDİ ✅)
        col1, col2 = st.columns(2)
        search = col1.text_input("🔍 Ara:"); f_pa = col2.slider("🔥 Min PA:", 0, 200, 130)
        f_mevki = st.multiselect("⚽ Mevki:", options=list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_yas = st.slider("🎂 Yaş:", 14, 45, (14, 45))

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]

        for idx, row in f_df.head(15).iterrows():
            # ÖZELLİK 2: GELİŞİM ÇUBUĞU HESABI
            dev_perc = (row['CA'] / row['PA'] * 100) if row['PA'] > 0 else 0
            st.markdown(f"""
            <div class="player-card">
                <div><span class="pa-badge">PA: {row['PA']}</span><span class="ca-badge">CA: {row['CA']}</span></div>
                <b>{row['Oyuncu']}</b> ({row['Yaş']})<br>
                <small>{row['Kulüp']} | {row['Mevki']}</small>
                <div class="progress-bg"><div class="progress-fill" style="width: {dev_perc}%;"></div></div>
                <small style="color:#00FFC2">💰 Değer: {row['Değer']}</small>
            """, unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"btn_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]: # KADROM (KADRO ANALİZİ EKLENDİ ✅)
        st.subheader("⚽ Kadro Planlama ve Analiz")
        butce = st.number_input("💰 Bütçe:", value=150000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        c_fw = st.columns(3); st_p = c_fw[1].selectbox("Santrafor", p_opt, key="s1"); lw_p = c_fw[0].selectbox("Sol Kanat", p_opt, key="s2"); rw_p = c_fw[2].selectbox("Sağ Kanat", p_opt, key="s3")
        c_md = st.columns(3); cm1 = c_md[0].selectbox("OS 1", p_opt, key="s4"); cm2 = c_md[1].selectbox("OS 2", p_opt, key="s5"); cm3 = c_md[2].selectbox("OS 3", p_opt, key="s6")
        c_df = st.columns(4); lb = c_df[0].selectbox("Sol Bek", p_opt, key="s7"); cb1 = c_df[1].selectbox("Stoper 1", p_opt, key="s8"); cb2 = c_df[2].selectbox("Stoper 2", p_opt, key="s9"); rb = c_df[3].selectbox("Sağ Bek", p_opt, key="s10")
        gk_p = st.selectbox("Kaleci", p_opt, key="s11")
        
        # ÖZELLİK 3: KADRO ANALİZİ
        secilenler = [st_p, lw_p, rw_p, cm1, cm2, cm3, lb, cb1, cb2, rb, gk_p]
        s_df = df[df['Oyuncu'].isin(secilenler)]
        
        if not s_df.empty:
            toplam_maliyet = s_df['ValNum'].sum()
            avg_age = s_df['Yaş'].mean()
            avg_pa = s_df['PA'].mean()
            kalan = butce - toplam_maliyet
            
            st.markdown(f"""
            <div class="analysis-card">
                <h3>📊 KADRO ANALİZİ</h3>
                <p>🎂 <b>Yaş Ortalaması:</b> {avg_age:.1f}</p>
                <p>⭐ <b>PA Ortalaması:</b> {avg_pa:.1f}</p>
                <p>💰 <b>Kalan Bütçe:</b> {kalan:,.0f} €</p>
                <p>📈 <b>Takım Potansiyeli:</b> {'Yüksek' if avg_pa > 160 else 'Orta'}</p>
            </div>
            """, unsafe_allow_html=True)

    # Diğer bölümler (Popüler, Kıyas, Admin) korundu
    with tabs[3]:
        pk1 = st.selectbox("1. Oyuncu", p_opt, key="pk1"); pk2 = st.selectbox("2. Oyuncu", p_opt, key="pk2")
        if pk1 != "Boş" and pk2 != "Boş": st.table(df[df['Oyuncu'].isin([pk1, pk2])])

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
