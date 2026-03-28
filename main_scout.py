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

# FM Pozisyon Sözlüğü (SİLİNMEDİ!)
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- GELİŞMİŞ TASARIM (Lineup11 Stilinde Saha) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.94), rgba(14,23,23,0.94)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    
    /* BUTON KARTIN İÇİNDE ✅ */
    .player-card { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00D2FF; 
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 20px; 
    }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    
    /* Kart içindeki buton tasarımı */
    div.stButton > button:first-child {
        background-color: transparent !important;
        color: #00D2FF !important;
        border: 1px solid #00D2FF !important;
        width: 100% !important;
        border-radius: 8px !important;
        margin-top: 10px !important;
    }

    /* RESİMDEKİ GİBİ GERÇEK SAHA TASARIMI ✅ */
    .field-bg {
        background-color: #2c8c2c;
        background-image: 
            linear-gradient(white 2px, transparent 2px),
            linear-gradient(90deg, white 2px, transparent 2px),
            radial-gradient(circle at 50% 50%, transparent 40px, white 40px, white 42px, transparent 42px);
        border: 3px solid white;
        border-radius: 10px;
        position: relative;
        min-height: 600px;
        padding: 20px;
    }
    .player-jersey {
        background: rgba(0,0,0,0.7);
        border: 1px solid #00D2FF;
        border-radius: 5px;
        text-align: center;
        padding: 2px;
        font-size: 11px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_in = st.text_input("Kullanıcı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if mode == "Kayıt Ol": supabase.table("kullanicilar").insert({"username": u_in, "password": get_hash(p_in)}).execute(); st.success("Tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u_in).execute()
            if res.data and res.data[0]['password'] == get_hash(p_in): st.session_state.user = u_in; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data(ttl=3600)
    def load_full_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df.sort_values(by='PA', ascending=False)

    df = load_full_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    
    u_low = st.session_state.user.lower()
    menu = ["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    if any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"]): menu.append("🛠️ Admin")
    tabs = st.tabs(menu)

    with tabs[0]: # SCOUT (YAŞ VE MEVKİ GERİ GELDİ ✅)
        col_s1, col_s2 = st.columns(2)
        search = col_s1.text_input("🔍 İsim/Kulüp Ara:")
        f_pa = col_s2.slider("🔥 Min PA:", 0, 200, 130)
        
        f_mevki = st.multiselect("⚽ Mevki Seç:", options=list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        all_c = sorted(list(set([c.strip() for v in df['Ülke'].unique() for c in v.replace('/', ',').split(',')])))
        f_ulke = st.multiselect("🌎 Ülke Seç:", all_c)
        f_yas = st.slider("🎂 Yaş Aralığı:", 14, 45, (14, 45)) # YAŞ GERİ GELDİ ✅

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]

        # SAYFALAMA
        items_per_page = 15; total_pages = (len(f_df) // items_per_page) + 1
        page = st.number_input("Sayfa", min_value=1, max_value=total_pages, step=1, key="page_sc")
        start_idx = (page - 1) * items_per_page; end_idx = start_idx + items_per_page

        for idx, row in f_df.iloc[start_idx:end_idx].iterrows():
            # BUTON KARTIN İÇİNDE ✅
            st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {row['PA']}</span><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</small><br><small style="color:#00FFC2">⚽ {row['Mevki']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
            if st.button(f"⭐ Listeye Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]: # KADROM (RESİMDEKİ GİBİ SAHA ✅)
        st.subheader("⚽ Taktik Tahtası (Lineup11 Stil)")
        plist = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        st.markdown('<div class="field-bg">', unsafe_allow_html=True)
        
        # Forvet Satırı
        c_fw = st.columns(3)
        st_p = c_fw[1].selectbox("ST", plist, key="s_st")
        lw_p = c_fw[0].selectbox("LW", plist, key="s_lw")
        rw_p = c_fw[2].selectbox("RW", plist, key="s_rw")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Orta Saha Satırı
        c_mid = st.columns(3)
        cm1 = c_mid[0].selectbox("CM1", plist, key="s_cm1")
        cm2 = c_mid[1].selectbox("CM2", plist, key="s_cm2")
        cm3 = c_mid[2].selectbox("CM3", plist, key="s_cm3")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Defans Satırı
        c_def = st.columns(4)
        lb = c_def[0].selectbox("LB", plist, key="s_lb")
        cb1 = c_def[1].selectbox("CB1", plist, key="s_cb1")
        cb2 = c_def[2].selectbox("CB2", plist, key="s_cb2")
        rb = c_def[3].selectbox("RB", plist, key="s_rb")
        
        st.markdown("<br>", unsafe_allow_html=True)
        gk = st.selectbox("GK", plist, key="s_gk")
        st.markdown('</div>', unsafe_allow_html=True)

    # DİĞER SEKME İÇERİKLERİ (Kıyasla, Popüler, Admin - SİLİNMEDİ ✅)
    with tabs[1]:
        pop_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop_res.data:
            pop_df = pd.DataFrame(pop_res.data)['oyuncu_adi'].value_counts().reset_index().head(10)
            st.table(pop_df)
    
    with tabs[2]:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data: st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in res.data])])
    
    with tabs[3]:
        pk1 = st.selectbox("1. Oyuncu", plist, key="pk1")
        pk2 = st.selectbox("2. Oyuncu", plist, key="pk2")
        if pk1 != "Boş" and pk2 != "Boş":
            st.table(df[df['Oyuncu'].isin([pk1, pk2])])

    if len(menu) > 5:
        with tabs[5]:
            st.write(f"Üye: {len(supabase.table('kullanicilar').select('*').execute().data)}")
            st.dataframe(pd.DataFrame(supabase.table("favoriler").select("*").execute().data).tail(20))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
