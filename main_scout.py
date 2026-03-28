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

# --- GELİŞMİŞ TASARIM VE YEŞİL SAHA ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.94), rgba(14,23,23,0.94)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    
    /* DÜZELTME 1: Listeye Ekle Butonunu Kartın İçine Alıyoruz */
    .player-card { 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid #00D2FF; 
        border-radius: 12px; 
        padding: 15px; 
        margin-bottom: 15px; 
        position: relative; /* Buton için pozisyonlama */
    }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    
    /* Kartın içindeki Ekle butonunun stili */
    .stButton>button { 
        background-color: transparent !important; 
        color: #00D2FF !important; 
        border: 1px solid #00D2FF !important; 
        width: 100% !important; 
        margin-top: 10px !important; 
        height: 35px !important; 
        font-size: 14px !important; 
        border-radius: 8px !important; 
    }
    .stButton>button:hover { background-color: #00D2FF !important; color: black !important; }

    /* DÜZELTME 2: Taktik Tahtasını Yeşil Futbol Sahasına Çeviriyoruz */
    .taktik-saha {
        background-color: #1a4a1a;
        background-image: 
            linear-gradient(90deg, transparent 49.5%, white 49.5%, white 50.5%, transparent 50.5%),
            linear-gradient(white 1px, transparent 1px);
        background-size: 100% 100%, 100% 50px;
        border: 4px solid white;
        border-radius: 15px;
        padding: 20px;
        position: relative;
        min-height: 500px; /* Mobilde dikey saha */
        overflow: visible;
    }
    /* Saha ortası çemberi */
    .taktik-saha::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100px;
        height: 100px;
        border: 3px solid white;
        border-radius: 50%;
    }
    /* Seçim kutuları ve etiketleri saha içinde daha okunur olsun */
    .mevki-label { color: white; font-weight: bold; margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ VEYA KAYIT</h1>", unsafe_allow_html=True)
    mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True); u_in = st.text_input("Kullanıcı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if mode == "Kayıt Ol": supabase.table("kullanicilar").insert({"username": u_in, "password": get_hash(p_in)}).execute(); st.success("Kayıt Tamam!")
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

    with tabs[0]: # SCOUTING (1. Resimdeki Sayfalamayı ve Tasarımı Koruyoruz)
        search = st.text_input("🔍 Oyuncu/Kulüp Ara:"); f_pa = st.slider("🔥 Min PA:", 0, 200, 130)
        all_c = sorted(list(set([c.strip() for v in df['Ülke'].unique() for c in v.replace('/', ',').split(',')])))
        f_ulke = st.multiselect("🌎 Ülke Seç:", all_c)

        f_df = df[(df['PA'] >= f_pa)]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_ulke: f_df = f_df[f_df['Ülke'].apply(lambda x: any(u in x for u in f_ulke))]

        # --- SAYFALAMA VE KART İÇİ BUTON (1. Resimdeki gibi) ---
        items_per_page = 15; total_pages = (len(f_df) // items_per_page) + 1
        page = st.number_input("Sayfa", min_value=1, max_value=total_pages, step=1, key="sc_page")
        start_idx = (page - 1) * items_per_page; end_idx = start_idx + items_per_page

        for idx, row in f_df.iloc[start_idx:end_idx].iterrows():
            with st.container():
                # DÜZELTME 1: Buton Kartın İçine Giriyor ✅
                st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {row['PA']}</span><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</small><br><small style="color:#00FFC2">⚽ {row['Mevki']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
                if st.button(f"⭐ Listeye Ekle", key=f"add_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} listene eklendi!")
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

    with tabs[4]: # ⚽ KADROM (SAHA GÖRÜNÜMÜ - 2. RESİM DÜZELTMESİ)
        st.subheader("⚽ Senin İlk 11'in (Saha Dizilişi)")
        plist = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        # DÜZELTME 2: Yeşil Saha ve Saha İçi Diziliş (Mobilde Dikey Saha) ✅
        st.markdown('<div class="taktik-saha">', unsafe_allow_html=True)
        
        # Forvet Hattı (Üst)
        fwd_cols = st.columns(3)
        st_p = fwd_cols[1].selectbox("Santrafor", plist, key="st_sq")
        lw_p = fwd_cols[0].selectbox("Sol Kanat", plist, key="lw_sq")
        rw_p = fwd_cols[2].selectbox("Sağ Kanat", plist, key="rw_sq")
        
        st.markdown("<br><br>", unsafe_allow_html=True) # Saha çizgilerine göre boşluk
        
        # Orta Saha Hattı
        mid_cols = st.columns(3)
        cm1 = mid_cols[0].selectbox("Orta Saha 1", plist, key="cm1_sq")
        cm2 = mid_cols[1].selectbox("Orta Saha 2", plist, key="cm2_sq")
        cm3 = mid_cols[2].selectbox("Orta Saha 3", plist, key="cm3_sq")
        
        st.markdown("<br><br>", unsafe_allow_html=True) # Saha çizgilerine göre boşluk
        
        # Defans Hattı
        def_cols = st.columns(4)
        lb = def_cols[0].selectbox("Sol Bek", plist, key="lb_sq")
        cb1 = def_cols[1].selectbox("Stoper 1", plist, key="cb1_sq")
        cb2 = def_cols[2].selectbox("Stoper 2", plist, key="cb2_sq")
        rb = def_cols[3].selectbox("Sağ Bek", plist, key="rb_sq")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Kaleci
        gk = st.selectbox("Kaleci", plist, key="gk_sq")
        
        st.markdown('</div>', unsafe_allow_html=True)

    if len(menu) > 5: # ADMIN (KAYBOLMADI)
        with tabs[5]:
            st.subheader("🛠️ Admin")
            st.write(f"Toplam Üye: {len(supabase.table('kullanicilar').select('*').execute().data)}")
            adm_res = supabase.table("favoriler").select("*").execute()
            if adm_res.data: st.dataframe(pd.DataFrame(adm_res.data).tail(30))

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
