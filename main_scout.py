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

# --- TASARIM VE PANEL GÖRSELİ ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .player-card { 
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(0,210,255,0.05) 100%);
        border: 1px solid #00D2FF; border-radius: 12px; padding: 18px; margin-bottom: 15px; transition: 0.3s;
    }
    .player-card:hover { border-color: #ffffff; box-shadow: 0px 0px 10px rgba(0,210,255,0.2); }
    .stat-box { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px; }
    .pa-box { background: #FFD700; color: black; padding: 4px 10px; border-radius: 6px; font-weight: bold; }
    .tm-button { display: inline-block; padding: 8px 15px; background-color: transparent; color: #00D2FF !important; text-decoration: none; border-radius: 8px; font-weight: bold; border: 1.5px solid #00D2FF; font-size: 13px; margin-top: 15px; }
    .pitch-sector { background: rgba(0, 210, 255, 0.08); border-left: 5px solid #00D2FF; padding: 10px; margin-bottom: 10px; font-weight: bold; }
    .admin-stat { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 20px; border-radius: 10px; text-align: center; }
    .duyuru-bandi { background: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 2px solid white; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- DUYURU SİSTEMİ (Ömer, burayı değiştirirsen sitede yayınlanır) ---
duyuru_metni = "📢 FM 24 Veritabanı V2 Yayında! Tüm Pozisyonlar Güncellendi."

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    st.markdown(f'<div class="duyuru-bandi">{duyuru_metni}</div>', unsafe_allow_html=True)
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    rem = st.checkbox("Beni Hatırla")
    if st.button("Devam"):
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
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        df['Pasaportlar'] = df['Ülke'].apply(lambda x: [c.strip() for c in str(x).replace('-', '/').replace(',', '/').split('/') if c.strip()])
        return df

    df = load_data()
    user_favs_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", st.session_state.user).execute()
    user_favs = [x['oyuncu_adi'] for x in user_favs_res.data] if user_favs_res.data else []

    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "🛠️ ADMIN"])

    with tabs[0]: # SCOUT (V65'DEKİ ŞIK KARTLAR KORUNDU)
        c1, c2, c3 = st.columns([1, 1, 1])
        f_name = c1.text_input("İsim Ara:")
        all_unique_countries = sorted(list(set([c for sublist in df['Pasaportlar'] for c in sublist])))
        f_country = c2.multiselect("Ülke Seç:", all_unique_countries)
        f_club = c3.text_input("Takım Ara:")
        c_sort, c_pa, c_age = st.columns([1, 1, 1])
        sort_by = c_sort.selectbox("Sırala:", ["PA (Yüksek)", "CA (Yüksek)", "Yaş (Genç)"])
        f_pa = c_pa.slider("Min PA:", 0, 200, 100); f_age = c_age.slider("Yaş:", 15, 45, (15, 45))
        f_pos = st.multiselect("Mevki:", ["GK", "D C", "D L", "D R", "DM", "M C", "AM C", "AM L", "AM R", "ST"])
        
        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_age[0]) & (df['Yaş'] <= f_age[1])]
        if f_name: f_df = f_df[f_df['Oyuncu'].str.contains(f_name, case=False)]
        if f_club: f_df = f_df[f_df['Kulüp'].str.contains(f_club, case=False)]
        if f_country: f_df = f_df[f_df['Pasaportlar'].apply(lambda x: any(c in x for c in f_country))]
        if f_pos: f_df = f_df[f_df['Mevki'].apply(lambda x: any(p in str(x) for p in f_pos))]

        if sort_by == "PA (Yüksek)": f_df = f_df.sort_values("PA", ascending=False)
        elif sort_by == "CA (Yüksek)": f_df = f_df.sort_values("CA", ascending=False)
        else: f_df = f_df.sort_values("Yaş", ascending=True)

        sz = 15; pg = (len(f_df)//sz)+(1 if len(f_df)%sz>0 else 0)
        if pg > 1:
            p_num = st.number_input(f"Sayfa (1-{pg}):", 1, pg, 1)
            f_df = f_df.iloc[(p_num-1)*sz : p_num*sz]
        
        for _, r in f_df.iterrows():
            is_fav = r['Oyuncu'] in user_favs
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(r['Oyuncu'])}"
            st.markdown(f'<div class="player-card"><div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-size:18px;font-weight:bold;">{r["Oyuncu"]} {"✅" if is_fav else ""}</span><span class="pa-box">PA: {r["PA"]}</span></div><div style="margin-top:5px;color:#aaa;font-size:14px;">{r["Kulüp"]} | {r["Ülke"]} | {r["Yaş"]} Yaş</div><div style="margin-top:10px;"><span class="stat-box">CA: {r["CA"]}</span><span class="stat-box">{r["Mevki"]}</span></div><div style="margin-top:12px;color:#00D2FF;font-weight:bold;">Değer: {r["Değer"]}</div><a href="{tm_url}" target="_blank" class="tm-button">TRANSFERMARKT PROFİLİ</a></div>', unsafe_allow_html=True)
            if not is_fav:
                if st.button(f"⭐ Ekle", key=f"s_{r['Oyuncu']}"):
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": r['Oyuncu']}).execute(); st.rerun()

    with tabs[4]: # KADROM (11 MEVKİ KORUNDU)
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
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": k_data}).execute(); st.success("Kaydedildi!")

    with tabs[5]: # YENİ GELİŞMİŞ ADMIN PANELİ ✅
        if any(adm in st.session_state.user.lower() for adm in ["someku", "omer", "admin"]):
            st.subheader("🛠️ Elite Scout Yönetim Merkezi")
            
            # Verileri Çek
            u_data = supabase.table("kullanicilar").select("username").execute()
            f_data = supabase.table("favoriler").select("*").execute()
            f_df = pd.DataFrame(f_data.data) if f_data.data else pd.DataFrame()

            # Özet Kartları
            a1, a2, a3 = st.columns(3)
            a1.markdown(f'<div class="admin-stat"><h3>👥 Kayıtlı Üye</h3><h2>{len(u_data.data)}</h2></div>', unsafe_allow_html=True)
            a2.markdown(f'<div class="admin-stat"><h3>⭐ Toplam Fav</h3><h2>{len(f_df)}</h2></div>', unsafe_allow_html=True)
            if not f_df.empty:
                top_user = f_df['kullanici_adi'].value_counts().idxmax()
                a3.markdown(f'<div class="admin-stat"><h3>🏆 En Aktif</h3><h2>{top_user}</h2></div>', unsafe_allow_html=True)
            
            st.write("---")
            st.subheader("Kullanıcı Detayları")
            u_filter = st.selectbox("Kullanıcı Seç:", ["Hepsi"] + [x['username'] for x in u_data.data])
            if u_filter == "Hepsi":
                st.dataframe(f_df[['kullanici_adi', 'oyuncu_adi', 'created_at']], use_container_width=True)
            else:
                st.dataframe(f_df[f_df['kullanici_adi'] == u_filter][['oyuncu_adi', 'created_at']], use_container_width=True)
        else:
            st.error("Admin yetkiniz yok.")

    # Diğer Popüler/Listem/Kıyas sekmeleri V65 ile aynıdır.
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
