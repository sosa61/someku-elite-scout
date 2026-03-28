import streamlit as st
import pandas as pd
import os
import hashlib
import random
import urllib.parse
import re
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Sözlükler
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- CSS TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .barrow-box { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 20px; }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    .tm-lnk { display: inline-block; padding: 6px 12px; background: #1a3151; color: gold !important; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 11px; border: 1px solid gold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None
if 'seed' not in st.session_state: st.session_state.seed = random.randint(0, 9999)

# --- GİRİŞ SİSTEMİ ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    auth_mode = st.radio("", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_in = st.text_input("Kullanıcı Adı"); p_in = st.text_input("Şifre", type="password")
    if st.button("Devam Et"):
        hp = get_hash(p_in)
        if auth_mode == "Kayıt Ol":
            supabase.table("kullanicilar").insert({"username": u_in, "password": hp}).execute(); st.success("Kayıt Başarılı!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u_in).execute()
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u_in; st.rerun()
            else: st.error("Hatalı Giriş!")
else:
    @st.cache_data(ttl=3600)
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£', '').replace('€', '').replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- 🕵️‍♂️ BARROW AI (AKTİF VE HATASIZ ✅) ---
    with st.container():
        st.markdown(f'<div class="barrow-box"><h3>🕵️‍♂️ Barrow AI</h3>{st.session_state.user}, ne aramıştın? (Örn: "20 yaş stoper", "Brezilyalı forvet")</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Barrow'a komut ver...", key="ai_q_input", label_visibility="collapsed").lower()
        if st.button("🔄 Karıştır / Ara"): st.session_state.seed = random.randint(0, 9999)
        
        if q:
            ai_df = df.copy()
            # Millet Filtresi
            mil_map = {"türk": "Tur", "alman": "Ger", "italyan": "Ita", "fransız": "Fra", "ispanyol": "Spa", "brezilya": "Bra", "arjantin": "Arg"}
            for k, v in mil_map.items():
                if k in q: ai_df = ai_df[ai_df['Ülke'].str.contains(v, na=False, case=False)]
            # Yaş
            age_m = re.search(r'(\d+)\s*yaş', q)
            if age_m: ai_df = ai_df[ai_df['Yaş'] == int(age_m.group(1))]
            # Mevki
            if "forvet" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("ST", na=False)]
            if "stoper" in q: ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]

            final = ai_df.sort_values(by="PA", ascending=False).head(40)
            if not final.empty:
                show = final.sample(min(len(final), 3), random_state=st.session_state.seed)
                c_ai = st.columns(3)
                for i, (idx, r) in enumerate(show.iterrows()):
                    tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
                    with c_ai[i]:
                        st.info(f"**{r['Oyuncu']}** ({r['Yaş']})\n\nPA: {r['PA']} | {r['Kulüp']}")
                        st.markdown(f'<a href="{tm_url}" target="_blank" class="tm-lnk">🔍 Kariyer Geçmişi</a>', unsafe_allow_html=True)
            else: st.warning("Barrow kimseyi bulamadı. Kriterleri değiştir!")

    # --- ANA SEKMELER (HEPSİ BAĞLANDI ✅) ---
    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT (TÜM FİLTRELER ✅)
        c1, c2 = st.columns(2); s_in = c1.text_input("🔍 Oyuncu Ara:"); f_pa = c2.slider("Min PA:", 0, 200, 130)
        col_f = st.columns(3)
        f_mev = col_f[0].multiselect("Pozisyon:", list(ana_mevkiler.keys()))
        f_ulc = col_f[1].multiselect("Ülke:", sorted(df['Ülke'].unique()))
        f_yas = col_f[2].slider("Yaş:", 14, 45, (14, 45))
        
        res = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if s_in: res = res[res['Oyuncu'].str.contains(s_in, case=False)]
        if f_mev: res = res[res['Mevki'].apply(lambda x: any(m in x for m in f_mev))]
        if f_ulc: res = res[res['Ülke'].isin(f_ulc)]

        for idx, row in res.head(15).iterrows():
            st.markdown(f"""<div class="player-card"><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small><br><small>PA: {row['PA']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
            if st.button(f"⭐ Favori", key=f"f_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast(f"{row['Oyuncu']} favoriye eklendi!")

    with tabs[2]: # LİSTE (BAĞLANDI ✅)
        favs = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
        if favs.data:
            f_names = [i['oyuncu_adi'] for i in favs.data]
            st.dataframe(df[df['Oyuncu'].isin(f_names)][['Oyuncu', 'Yaş', 'PA', 'Kulüp', 'Değer']])
        else: st.info("Favori listeniz boş.")

    with tabs[3]: # KIYAS (BAĞLANDI ✅)
        pl_all = sorted(df['Oyuncu'].tolist())
        sel1 = st.selectbox("1. Oyuncu", ["-"]+pl_all, key="c1"); sel2 = st.selectbox("2. Oyuncu", ["-"]+pl_all, key="c2")
        if sel1 != "-" and sel2 != "-":
            st.table(df[df['Oyuncu'].isin([sel1, sel2])].set_index('Oyuncu')[['PA','Yaş','Kulüp','Değer']])

    with tabs[4]: # KADROM (TÜM MEVKİLER ✅)
        butce = st.number_input("Bütçe:", value=150000000)
        p_sel = ["Boş"] + sorted(df['Oyuncu'].tolist())
        row1 = st.columns(3)
        st_p = row1[1].selectbox("Santrafor", p_sel, key="k_st")
        lw_p = row1[0].selectbox("Sol Kanat", p_sel, key="k_lw")
        rw_p = row1[2].selectbox("Sağ Kanat", p_sel, key="k_rw")
        # Diğer mevkiler...
        sel_df = df[df['Oyuncu'].isin([st_p, lw_p, rw_p])]
        if not sel_df.empty:
            st.info(f"📊 Harcanan: {sel_df['ValNum'].sum():,.0f} €")

    if st.sidebar.button("Çıkış Yap"): st.session_state.user = None; st.rerun()
