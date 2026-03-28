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

# --- TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.95), rgba(14,23,23,0.95)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    .pa-badge { background: #00D2FF; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; float: right; }
    .ca-badge { background: #FFD700; color: black; padding: 2px 8px; border-radius: 10px; font-weight: bold; margin-right: 5px; }
    .stButton>button { width: 100% !important; border-radius: 8px !important; }
    .budget-card { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 20px; border-radius: 10px; text-align: center; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ VEYA KAYIT</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_in = st.text_input("Kullanıcı Adı").strip(); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam Et"):
        h_p = get_hash(p_in)
        if auth_mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u_in, "password": h_p}).execute(); st.success("Kayıt Başarılı! Şimdi Giriş Yap.")
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
    st.markdown(f"<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
    
    u_low = st.session_state.user.lower()
    menu = ["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom"]
    is_admin = any(x in u_low for x in ["someku", "omer", "ömer", "ramazan"])
    if is_admin: menu.append("🛠️ Admin")
    tabs = st.tabs(menu)

    with tabs[0]: # SCOUT (TÜM FİLTRELER ✅)
        c1, c2 = st.columns(2)
        search = c1.text_input("🔍 Oyuncu veya Kulüp Ara:")
        f_pa = c2.slider("🔥 Minimum PA:", 0, 200, 130)
        
        col_f1, col_f2 = st.columns(2)
        f_mevki = col_f1.multiselect("⚽ Mevki Seç:", options=list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_ulke = col_f2.multiselect("🌎 Ülke Seç:", sorted(df['Ülke'].unique()))
        f_yas = st.slider("🎂 Yaş Aralığı:", 14, 45, (14, 45))

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[(f_df['Oyuncu'].str.contains(search, case=False)) | (f_df['Kulüp'].str.contains(search, case=False))]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]

        items_per_page = 15; page = st.number_input("Sayfa", 1, 100, 1); start_idx = (page-1)*items_per_page
        
        for idx, row in f_df.iloc[start_idx:start_idx+items_per_page].iterrows():
            with st.container():
                st.markdown(f"""<div class="player-card"><div><span class="pa-badge">PA: {row['PA']}</span><span class="ca-badge">CA: {row['CA']}</span></div><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>🛡️ {row['Kulüp']} | 🌎 {row['Ülke']}</small><br><small style="color:#00FFC2">⚽ {row['Mevki']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
                if st.button(f"⭐ Listeye Ekle", key=f"add_{idx}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                    st.toast(f"{row['Oyuncu']} favorilere eklendi!")
                st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]: # POPÜLER (OTOMATİK SIRALAMA ✅)
        st.subheader("🔥 En Çok Takibe Alınan Oyuncular")
        pop_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop_res.data:
            pop_df = pd.DataFrame(pop_res.data)['oyuncu_adi'].value_counts().reset_index()
            pop_df.columns = ['Oyuncu', 'Takipçi Sayısı']
            st.table(pop_df.head(10))

    with tabs[2]: # LİSTE (KİŞİSEL LİSTEM ✅)
        st.subheader("⭐ Takip Listem")
        my_res = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).execute()
        if my_res.data:
            my_players = [i['oyuncu_adi'] for i in my_res.data]
            list_df = df[df['Oyuncu'].isin(my_players)]
            st.dataframe(list_df[['Oyuncu', 'Yaş', 'CA', 'PA', 'Kulüp', 'Değer', 'Mevki']], use_container_width=True)
            if st.button("Listeyi Temizle"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).execute()
                st.rerun()

    with tabs[3]: # KIYAS (TABLO GÖRÜNÜMÜ ✅)
        st.subheader("⚔️ Oyuncu Karşılaştır")
        plist = sorted(df['Oyuncu'].tolist())
        col_k1, col_k2 = st.columns(2)
        p1 = col_k1.selectbox("1. Oyuncu", ["Seç..."] + plist, key="comp1")
        p2 = col_k2.selectbox("2. Oyuncu", ["Seç..."] + plist, key="comp2")
        if p1 != "Seç..." and p2 != "Seç...":
            c_df = df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['PA', 'CA', 'Yaş', 'Mevki', 'Kulüp', 'Değer']]
            st.table(c_df.T)

    with tabs[4]: # KADROM (BÜTÇE TAKİBİ ✅)
        st.subheader("⚽ Kadro Planlama")
        butce = st.number_input("💰 Toplam Transfer Bütçen:", value=150000000, step=1000000)
        p_opt = ["Boş"] + sorted(df['Oyuncu'].tolist())
        
        c_fw = st.columns(3); st_p = c_fw[1].selectbox("Santrafor", p_opt, key="s1"); lw_p = c_fw[0].selectbox("Sol Kanat", p_opt, key="s2"); rw_p = c_fw[2].selectbox("Sağ Kanat", p_opt, key="s3")
        c_md = st.columns(3); cm1 = c_md[0].selectbox("OS 1", p_opt, key="s4"); cm2 = c_md[1].selectbox("OS 2", p_opt, key="s5"); cm3 = c_md[2].selectbox("OS 3", p_opt, key="s6")
        c_df = st.columns(4); lb = c_df[0].selectbox("Sol Bek", p_opt, key="s7"); cb1 = c_df[1].selectbox("Stoper 1", p_opt, key="s8"); cb2 = c_df[2].selectbox("Stoper 2", p_opt, key="s9"); rb = c_df[3].selectbox("Sağ Bek", p_opt, key="s10")
        gk_p = st.selectbox("Kaleci", p_opt, key="s11")
        
        secilenler = [st_p, lw_p, rw_p, cm1, cm2, cm3, lb, cb1, cb2, rb, gk_p]
        toplam_maliyet = df[df['Oyuncu'].isin(secilenler)]['ValNum'].sum()
        kalan = butce - toplam_maliyet
        
        st.markdown(f"""<div class="budget-card"><h3>💰 Bütçe Durumu</h3><p>Harcanan: <b>{toplam_maliyet:,.0f} €</b></p><p>Kalan: <b style="color:{'#00FFC2' if kalan >= 0 else '#FF4B4B'}">{kalan:,.0f} €</b></p></div>""", unsafe_allow_html=True)

    if is_admin:
        with tabs[5]:
            st.subheader("🛠️ Admin Paneli")
            all_favs = supabase.table("favoriler").select("*").execute()
            if all_favs.data: st.dataframe(pd.DataFrame(all_favs.data).tail(50))

    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()
