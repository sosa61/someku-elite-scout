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

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM GÜNCELLEMESİ ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.94), rgba(14,23,23,0.94)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    
    /* BUTON KESİN KARTIN İÇİNDE ✅ */
    .player-card { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00D2FF; 
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 25px; 
        display: flex;
        flex-direction: column;
    }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; align-self: flex-end; }
    
    /* Kartın içindeki butonun CSS'i */
    .player-card button {
        background-color: transparent !important;
        color: #00D2FF !important;
        border: 1px solid #00D2FF !important;
        width: 100% !important;
        margin-top: 15px !important;
        border-radius: 8px !important;
    }

    /* SAHA İÇİ DİZİLİŞ TASARIMI ✅ */
    .field-container {
        background-color: #2c8c2c;
        border: 3px solid white;
        border-radius: 15px;
        padding: 20px;
        min-height: 700px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .field-line { border-bottom: 2px solid rgba(255,255,255,0.3); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True); u_in = st.text_input("Kullanıcı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Bağlan"):
        if mode == "Kayıt Ol": supabase.table("kullanicilar").insert({"username": u_in, "password": get_hash(p_in)}).execute(); st.success("Tamam!")
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
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    
    u_low = st.session_state.user.lower()
    menu = ["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    if any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"]): menu.append("🛠️ Admin")
    tabs = st.tabs(menu)

    with tabs[0]: # SCOUT
        search = st.text_input("🔍 Ara:"); f_pa = st.slider("🔥 Min PA:", 0, 200, 130)
        f_df = df[df['PA'] >= f_pa]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        
        items_per_page = 15; page = st.number_input("Sayfa", 1, 100, 1); start_idx = (page-1)*items_per_page
        
        for idx, row in f_df.iloc[start_idx:start_idx+items_per_page].iterrows():
            with st.container():
                # BUTON KARTIN İÇİNDE ✅
                st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {row['PA']}</span><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Ülke']}</small><br><small style="color:#00FFC2">{row['Mevki']} | {row['Değer']}</small>""", unsafe_allow_html=True)
                if st.button(f"⭐ Ekle", key=f"btn_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} eklendi!")
                st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]: # KADROM (SAHA İÇİ SEÇİM ✅)
        st.subheader("⚽ Taktik Tahtası (Saha Üstü Seçim)")
        plist = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        st.markdown('<div class="field-container">', unsafe_allow_html=True)
        
        # FORVETLER
        st.write("🏃 **FORVET HATTI**")
        c_fw = st.columns(3)
        lw = c_fw[0].selectbox("Sol Kanat", plist, key="f_lw")
        st_p = c_fw[1].selectbox("Santrafor", plist, key="f_st")
        rw = c_fw[2].selectbox("Sağ Kanat", plist, key="f_rw")
        
        st.markdown('<div class="field-line"></div>', unsafe_allow_html=True)
        
        # ORTA SAHALAR
        st.write("🎯 **ORTA SAHA HATTI**")
        c_md = st.columns(3)
        cm1 = c_md[0].selectbox("OS 1", plist, key="f_cm1")
        cm2 = c_md[1].selectbox("OS 2", plist, key="f_cm2")
        cm3 = c_md[2].selectbox("OS 3", plist, key="f_cm3")
        
        st.markdown('<div class="field-line"></div>', unsafe_allow_html=True)
        
        # DEFANSLAR
        st.write("🛡️ **DEFANS HATTI**")
        c_df = st.columns(4)
        lb = c_df[0].selectbox("Sol Bek", plist, key="f_lb")
        cb1 = c_df[1].selectbox("Stoper 1", plist, key="f_cb1")
        cb2 = c_df[2].selectbox("Stoper 2", plist, key="f_cb2")
        rb = c_df[3].selectbox("Sağ Bek", plist, key="f_rb")
        
        # KALECİ
        st.write("🧤 **KALECİ**")
        gk = st.selectbox("Kaleci", plist, key="f_gk")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # DİĞERLERİNE DOKUNMADIM ✅
    with tabs[1]:
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data: st.table(pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().head(10))
    with tabs[2]:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data: st.dataframe(df[df['Oyuncu'].isin([i['oyuncu_adi'] for i in res.data])])
    with tabs[3]:
        pk1 = st.selectbox("1. Oyuncu", plist, key="pk1"); pk2 = st.selectbox("2. Oyuncu", plist, key="pk2")
        if pk1 != "Boş" and pk2 != "Boş": st.table(df[df['Oyuncu'].isin([pk1, pk2])])
    if len(menu) > 5:
        with tabs[5]:
            st.write(f"Üye: {len(supabase.table('kullanicilar').select('*').execute().data)}")
            st.dataframe(pd.DataFrame(supabase.table("favoriler").select("*").execute().data).tail(20))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
