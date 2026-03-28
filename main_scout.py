import streamlit as st
import pandas as pd
import os
import hashlib
import json
import urllib.parse
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

pozisyon_map = {
    "GK": "Kaleci (GK)", "D C": "Stoper (DC)", "D L": "Sol Bek (DL)", "D R": "Sağ Bek (DR)", 
    "DM": "Ön Libero (DM)", "M C": "Orta Saha (MC)", "AM C": "On Numara (AMC)", 
    "AM L": "Sol Kanat (AML)", "AM R": "Sağ Kanat (AMR)", "ST": "Forvet (ST)"
}

st.markdown("""<style>.stApp { background-color: #0E1117; color: white; }.player-card { background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(0,210,255,0.05) 100%); border: 1px solid #00D2FF; border-radius: 12px; padding: 18px; margin-bottom: 15px; }.stat-box { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px; }.pa-box { background: #FFD700; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }.duyuru-bandi { background: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 2px solid white; }.pitch-sector { background: rgba(0, 210, 255, 0.08); border-left: 5px solid #00D2FF; padding: 10px; margin-bottom: 10px; font-weight: bold; margin-top: 15px; }.admin-stat { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 15px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

def get_announcement():
    try:
        res = supabase.table("ayarlar").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "Hoş geldiniz!"
    except: return "Sistem Hazır!"

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    st.markdown(f'<div class="duyuru-bandi">{get_announcement()}</div>', unsafe_allow_html=True)
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Sisteme Gir"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            try: supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Kullanıcı mevcut.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        for col in ['PA', 'CA', 'Yaş']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        df['Pasaportlar'] = df['Ülke'].apply(lambda x: [c.strip() for c in str(x).replace('-', '/').replace(',', '/').split('/') if c.strip()])
        return df

    df = load_data()
    f_res = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).execute()
    user_favs = [x['oyuncu_adi'] for x in f_res.data] if f_res.data else []

    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "💡 ÖNERİ", "🛠️ ADMIN"])

    with tabs[0]:
        c1, c2, c3 = st.columns(3)
        f_name = c1.text_input("İsim Ara:")
        all_c = sorted(list(set([c for sublist in df['Pasaportlar'] for c in sublist])))
        f_country = c2.multiselect("Ülke:", all_c)
        f_club = c3.text_input("Takım Ara:")

        sc1, sc2, sc3 = st.columns(3)
        f_pa = sc1.slider("Minimum PA (Potansiyel):", 0, 200, 100)
        f_age = sc2.slider("Yaş Aralığı:", 15, 45, (15, 45))
        sort_by = sc3.selectbox("Sıralama Ölçütü:", ["PA (Yüksek)", "CA (Yüksek)", "Yaş (Genç)", "Yaş (Tecrübeli)"])
        f_pos = st.multiselect("Mevki (Türkçe):", list(pozisyon_map.keys()), format_func=lambda x: pozisyon_map[x])
        
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        
        # TAKIM FİLTRESİ FIX ✅
        if f_club: f_df = f_df[f_df['Kulüp'].fillna("").str.contains(f_club, case=False)]
        
        if f_country: f_df = f_df[f_df['Pasaportlar'].apply(lambda x: any(c in x for c in f_country))]
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]

        if sort_by == "PA (Yüksek)": f_df = f_df.sort_values("PA", ascending=False)
        elif sort_by == "CA (Yüksek)": f_df = f_df.sort_values("CA", ascending=False)
        elif sort_by == "Yaş (Genç)": f_df = f_df.sort_values("Yaş", ascending=True)
        else: f_df = f_df.sort_values("Yaş", ascending=False)

        sz = 15; pg = (len(f_df)//sz)+(1 if len(f_df)%sz>0 else 0)
        if pg > 1:
            p_num = st.number_input(f"Sayfa (1-{pg}):", 1, pg, 1)
            f_df = f_df.iloc[(p_num-1)*sz : p_num*sz]
        
        for _, r in f_df.iterrows():
            is_fav = r['Oyuncu'] in user_favs
            st.markdown(f'<div class="player-card"><b>{r["Oyuncu"]} {"✅" if is_fav else ""}</b> | PA: {r["PA"]} | {r["Kulüp"]}<br><small>{r["Mevki"]} | {r["Değer"]}</small></div>', unsafe_allow_html=True)
            if not is_fav:
                if st.button(f"⭐ Ekle", key=f"s_{r['Oyuncu']}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute(); st.rerun()

    with tabs[2]: # LİSTEM SİLME ÖZELLİĞİYLE ✅
        st.subheader("⭐ Senin Listen")
        if user_favs:
            for fav_item in user_favs:
                if "KADRO:" not in fav_item:
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"📍 {fav_item}")
                    if c2.button("Sil", key=f"del_{fav_item}"):
                        supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", fav_item).execute(); st.rerun()
        else: st.info("Listen boş.")

    with tabs[4]: # KADROM (TÜM POZİSYONLAR - BÖLGELİ ✅)
        st.subheader("⚽ Taktik Tahtası (4-3-3)")
        all_p = ["Boş"] + sorted(df['Oyuncu'].tolist())
        st.markdown('<div class="pitch-sector">FORVET HATTI</div>', unsafe_allow_html=True)
        c_f = st.columns(3); lw = c_f[0].selectbox("AML", all_p); stp = c_f[1].selectbox("ST", all_p); rw = c_f[2].selectbox("AMR", all_p)
        st.markdown('<div class="pitch-sector">ORTA SAHA</div>', unsafe_allow_html=True)
        c_m = st.columns(3); m1 = c_m[0].selectbox("MC 1", all_p); dm = c_m[1].selectbox("DM", all_p); m2 = c_m[2].selectbox("MC 2", all_p)
        st.markdown('<div class="pitch-sector">DEFANS HATTI</div>', unsafe_allow_html=True)
        c_d = st.columns(4); lb = c_d[0].selectbox("DL", all_p); cb1 = c_d[1].selectbox("DC 1", all_p); cb2 = c_d[2].selectbox("DC 2", all_p); rb = c_d[3].selectbox("DR", all_p)
        gk = st.selectbox("GK (Kaleci)", all_p)
        if st.button("💾 Kadroyu Kaydet"):
            k_data = f"KADRO:{json.dumps([lw, stp, rw, m1, dm, m2, lb, cb1, cb2, rb, gk])}"
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute(); st.success("Kadron Kaydedildi!")

    with tabs[6]: # ADMIN DETAYLI ✅
        if any(a in st.session_state.user.lower() for a in ["someku", "omer", "admin"]):
            u_data = supabase.table("kullanicilar").select("username").execute()
            f_data = supabase.table("favoriler").select("*").execute()
            ac1, ac2 = st.columns(2)
            ac1.markdown(f'<div class="admin-stat"><h3>Üyeler</h3><h2>{len(u_data.data)}</h2></div>', unsafe_allow_html=True)
            ac2.markdown(f'<div class="admin-stat"><h3>İşlemler</h3><h2>{len(f_data.data)}</h2></div>', unsafe_allow_html=True)
            st.subheader("Üye Listesi"); st.dataframe(pd.DataFrame(u_data.data), use_container_width=True)
            new_d = st.text_input("Duyuru Yaz:", get_announcement())
            if st.button("Yayınla"):
                supabase.table("ayarlar").update({"duyuru": new_d}).eq("id", 1).execute(); st.success("Güncellendi!")
