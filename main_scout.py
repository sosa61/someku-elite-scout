import streamlit as st
import pandas as pd
import os
import hashlib
import json
import urllib.parse
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6I..." # Mevcut keyin kalsın
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

pozisyon_map = {
    "GK": "Kaleci (GK)", "D C": "Stoper (DC)", "D L": "Sol Bek (DL)", "D R": "Sağ Bek (DR)", 
    "DM": "Ön Libero (DM)", "M C": "Orta Saha (MC)", "AM C": "On Numara (AMC)", 
    "AM L": "Sol Kanat (AML)", "AM R": "Sağ Kanat (AMR)", "ST": "Forvet (ST)"
}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

st.markdown("""<style>.stApp { background-color: #0E1117; color: white; }.player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }.tm-button { display: inline-block; padding: 6px 14px; background-color: #001e3f; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; border: 2px solid #ffffff; font-size: 13px; margin-top: 10px; }.pitch-sector { background: rgba(0, 210, 255, 0.08); border-left: 5px solid #00D2FF; padding: 10px; margin-bottom: 10px; font-weight: bold; }</style>""", unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    rem = st.checkbox("Beni Hatırla")
    if st.button("Devam"):
        hp = get_hash(p); res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
        if auth == "Kayıt Ol":
            if not res.data: supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute(); st.session_state.user = u; st.rerun()
            else: st.error("Mevcut!")
        else:
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        df['Pasaportlar'] = df['Ülke'].apply(lambda x: [c.strip() for c in str(x).replace('-', '/').replace(',', '/').split('/') if c.strip()])
        return df

    df = load_data()
    user_favs_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
    user_favs = [x['oyuncu_adi'] for x in user_favs_res.data] if user_favs_res.data else []

    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT (TAKIM ARAMA EKLENDİ ✅)
        c1, c2, c3 = st.columns([1, 1, 1])
        f_name = c1.text_input("İsim Ara:")
        all_unique_countries = sorted(list(set([c for sublist in df['Pasaportlar'] for c in sublist])))
        f_country = c2.multiselect("Ülke Seç:", all_unique_countries)
        f_club = c3.text_input("Takım (Kulüp) Ara:") # İSTEDİĞİN ÖZELLİK ✅

        c_sort, c_pa, c_age = st.columns([1, 1, 1])
        sort_by = c_sort.selectbox("Sırala:", ["PA (Yüksek)", "CA (Yüksek)", "Yaş (Genç)", "Yaş (Tecrübeli)"])
        f_pa = c_pa.slider("Min PA:", 0, 200, 100)
        f_age = c_age.slider("Yaş:", 15, 45, (15, 45))
        f_pos = st.multiselect("Mevki:", list(pozisyon_map.keys()), format_func=lambda x: pozisyon_map[x])
        
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        if f_club: f_df = f_df[f_df['Kulüp'].str.contains(f_club, case=False)] # TAKIM FİLTRESİ ✅
        if f_country: f_df = f_df[f_df['Pasaportlar'].apply(lambda x: any(c in x for c in f_country))]
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]

        if sort_by == "PA (Yüksek)": f_df = f_df.sort_values("PA", ascending=False)
        elif sort_by == "CA (Yüksek)": f_df = f_df.sort_values("CA", ascending=False)
        elif sort_by == "Yaş (Genç)": f_df = f_df.sort_values("Yaş", ascending=True)
        else: f_df = f_df.sort_values("Yaş", ascending=False)

        sz = 20; pg = (len(f_df)//sz)+(1 if len(f_df)%sz>0 else 0)
        if pg > 1:
            p_num = st.number_input(f"Sayfa (1-{pg}):", 1, pg, 1)
            f_df = f_df.iloc[(p_num-1)*sz : p_num*sz]
        
        for _, r in f_df.iterrows():
            is_fav = r['Oyuncu'] in user_favs
            st.markdown(f'<div class="player-card"><b>{r["Oyuncu"]}</b> {"✅" if is_fav else ""} ({r["Yaş"]}) | {r["Kulüp"]}<br><small>CA: {r["CA"]} | PA: {r["PA"]} | {r["Ülke"]}</small></div>', unsafe_allow_html=True)
            if not is_fav:
                if st.button(f"⭐ Ekle", key=f"s_{r['Oyuncu']}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute()
                    st.rerun()

    with tabs[4]: # KADROM (TÜM MEVKİLER GERİ GELDİ ✅)
        st.subheader("⚽ Taktik Tahtası (4-3-3)")
        all_p = ["Boş"] + sorted(df['Oyuncu'].tolist())
        st.markdown('<div class="pitch-sector">FORVET</div>', unsafe_allow_html=True)
        c_f = st.columns(3); lw = c_f[0].selectbox("AML", all_p); stp = c_f[1].selectbox("ST", all_p); rw = c_f[2].selectbox("AMR", all_p)
        st.markdown('<div class="pitch-sector">ORTA SAHA</div>', unsafe_allow_html=True)
        c_m = st.columns(3); m1 = c_m[0].selectbox("MC 1", all_p); dm = c_m[1].selectbox("DM", all_p); m2 = c_m[2].selectbox("MC 2", all_p)
        st.markdown('<div class="pitch-sector">DEFANS</div>', unsafe_allow_html=True)
        c_d = st.columns(4); lb = c_d[0].selectbox("DL", all_p); cb1 = c_d[1].selectbox("DC 1", all_p); cb2 = c_d[2].selectbox("DC 2", all_p); rb = c_d[3].selectbox("DR", all_p)
        gk = st.selectbox("GK", all_p)
        if st.button("💾 Kaydet"):
            k_data = f"KADRO:{json.dumps([lw, stp, rw, m1, dm, m2, lb, cb1, cb2, rb, gk])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute(); st.success("Kadronuz Kaydedildi!")

    with tabs[1]: # POPÜLER
        p_res = supabase.table("favoriler").select("oyuncu_adi").execute()
        if p_res.data:
            c = pd.DataFrame(p_res.data)['oyuncu_adi'].value_counts().reset_index()
            c.columns=['Oyuncu','Takip']; st.table(c.head(10))
    with tabs[2]: # LİSTEM
        m_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if m_res.data:
            f_names = [x['oyuncu_adi'] for x in m_res.data if "KADRO:" not in x['oyuncu_adi']]
            st.dataframe(df[df['Oyuncu'].isin(f_names)][['Oyuncu','Yaş','CA','PA','Mevki']])
    with tabs[3]: # KIYAS
        o_list = sorted(df['Oyuncu'].tolist()); p1 = st.selectbox("1", ["Seç"] + o_list, key="k1"); p2 = st.selectbox("2", ["Seç"] + o_list, key="k2")
        if p1 != "Seç" and p2 != "Seç": st.table(df[df['Oyuncu'].isin([p1, p2])].set_index('Oyuncu')[['CA','PA','Yaş','Mevki','Değer']])
    with tabs[5]: # ADMIN
        if any(x in st.session_state.user.lower() for x in ["someku", "omer"]):
            adm = supabase.table("favoriler").select("*").execute(); st.dataframe(pd.DataFrame(adm.data))
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
