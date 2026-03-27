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

# --- GELİŞMİŞ TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.94), rgba(14,23,23,0.94)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card { background: rgba(255, 255, 255, 0.06); border: 1px solid #00D2FF; border-radius: 15px; padding: 15px; margin-bottom: 15px; position: relative; }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 10px; border-radius: 10px; font-weight: bold; float: right; }
    .card-btn { background-color: transparent !important; color: #00FFC2 !important; border: 1px solid #00FFC2 !important; width: 100% !important; margin-top: 10px !important; border-radius: 8px !important; }
    .taktik-saha { background: #1a4a1a; border: 3px solid white; border-radius: 10px; padding: 20px; position: relative; min-height: 500px; }
    .mevki-kutu { background: rgba(0,0,0,0.7); border: 1px solid white; padding: 5px; border-radius: 5px; text-align: center; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

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
    def load_full_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]; df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
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

    with tabs[0]: # 🔍 SCOUT (SAYFALAMA + KART İÇİ BUTON)
        st.markdown("<div style='background:rgba(0,0,0,0.3);padding:15px;border-radius:10px;margin-bottom:20px;'>", unsafe_allow_html=True)
        search = st.text_input("🔍 İsim/Kulüp:")
        col_f1, col_f2 = st.columns(2)
        f_mevki = col_f1.multiselect("⚽ Mevki:", options=list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        all_c = sorted(list(set([c.strip() for v in df['Ülke'].unique() for c in v.replace('/', ',').split(',')])))
        f_ulke = col_f1.multiselect("🌎 Ülke:", all_c)
        f_pa = col_f2.slider("🔥 Min PA:", 0, 200, 130)
        f_yas = col_f2.slider("🎂 Max Yaş:", 14, 45, 45)
        st.markdown("</div>", unsafe_allow_html=True)

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] <= f_yas)]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]

        # --- SAYFALAMA (PAGINATION) ---
        items_per_page = 15
        total_pages = (len(f_df) // items_per_page) + 1
        page = st.number_input("Sayfa", min_value=1, max_value=total_pages, step=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        for idx, row in f_df.iloc[start_idx:end_idx].iterrows():
            with st.container():
                st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {row['PA']}</span><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</small><br><small style="color:#00FFC2">⚽ {row['Mevki']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
                if st.button(f"⭐ Listeye Ekle", key=f"add_{idx}", help="Kartın içinde"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast("Eklendi!")
                st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]: # 🔥 POPÜLER (EN ÇOK EKLENENLER)
        st.subheader("🔥 Globalde En Çok Listelenen Oyuncular")
        pop_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop_res.data:
            pop_df = pd.DataFrame(pop_res.data)['oyuncu_adi'].value_counts().reset_index()
            pop_df.columns = ['Oyuncu', 'Eklenme Sayısı']
            st.table(pop_df.head(10))

    with tabs[2]: # ⭐ LİSTE
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if res.data:
            fav_names = [i['oyuncu_adi'] for i in res.data]
            st.dataframe(df[df['Oyuncu'].isin(fav_names)], use_container_width=True)
        else: st.info("Listen boş.")

    with tabs[3]: # ⚔️ KIYAS
        plist = sorted(df['Oyuncu'].tolist())
        c1, c2 = st.columns(2); p1 = c1.selectbox("1. Oyuncu", ["Seç..."]+plist, key="k1"); p2 = c2.selectbox("2. Oyuncu", ["Seç..."]+plist, key="k2")
        if p1 != "Seç..." and p2 != "Seç...":
            r1, r2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.table(pd.DataFrame({"Özellik":["PA","CA","Yaş","Mevki"], p1:[r1['PA'],r1['CA'],r1['Yaş'],r1['Mevki']], p2:[r2['PA'],r2['CA'],r2['Yaş'],r2['Mevki']]}))

    with tabs[4]: # ⚽ KADROM (SAHA GÖRÜNÜMÜ)
        st.subheader("⚽ Taktik Tahtası")
        dizilis = st.selectbox("Diziliş:", ["4-3-3", "4-4-2", "4-2-3-1"])
        
        # Saha Tasarımı
        st.markdown('<div class="taktik-saha">', unsafe_allow_html=True)
        plist = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        # Basit 4-3-3 Görsel Dizilimi (3 Satırda Selectboxlar)
        row1 = st.columns(3) # Forvetler
        st_p = row1[1].selectbox("Santrafor", plist, key="st_sq")
        lw_p = row1[0].selectbox("Sol Kanat", plist, key="lw_sq")
        rw_p = row1[2].selectbox("Sağ Kanat", plist, key="rw_sq")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        row2 = st.columns(3) # Orta Sahalar
        cm1 = row2[0].selectbox("OS 1", plist, key="cm1_sq")
        cm2 = row2[1].selectbox("OS 2", plist, key="cm2_sq")
        cm3 = row2[2].selectbox("OS 3", plist, key="cm3_sq")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        row3 = st.columns(4) # Defanslar
        lb = row3[0].selectbox("Sol Bek", plist, key="lb_sq")
        cb1 = row3[1].selectbox("Stoper 1", plist, key="cb1_sq")
        cb2 = row3[2].selectbox("Stoper 2", plist, key="cb2_sq")
        rb = row3[3].selectbox("Sağ Bek", plist, key="rb_sq")
        
        st.markdown("<br>", unsafe_allow_html=True)
        gk = st.selectbox("Kaleci", plist, key="gk_sq")
        st.markdown('</div>', unsafe_allow_html=True)

    if len(menu) > 5:
        with tabs[5]:
            st.subheader("🛠️ Admin")
            st.write(f"Toplam Üye: {len(supabase.table('kullanicilar').select('*').execute().data)}")
            adm_res = supabase.table("favoriler").select("*").execute()
            if adm_res.data: st.dataframe(pd.DataFrame(adm_res.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
