import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .loader-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh; }
    .magnifier { font-size: 80px; animation: bounce 2s infinite ease-in-out; }
    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; transition: 0.3s; }
    .fav-active { border: 2px solid #f2cc60 !important; border-left: 10px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; font-weight: bold; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- VERİ FONKSİYONLARI ---
def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V90 Yayında!"
    except: return "🔥 SOMEKU SCOUT V90 Yayında!"

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data]
    except: return []

# --- YÜKLEME EKRANI ---
if 'lottie_shown' not in st.session_state:
    st.markdown('<div class="loader-container"><div class="magnifier">🕵️‍♂️</div><h2 style="color: #58a6ff;">Elite Veritabanı Hazırlanıyor...</h2></div>', unsafe_allow_html=True)
    time.sleep(1.5); st.session_state.lottie_shown = True; st.rerun()

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        u_id = st.text_input("Kullanıcı Adı:", key="l_u")
        u_pw = st.text_input("Şifre:", type="password", key="l_p")
        if st.button("Giriş", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
                st.session_state.user = u_id
                st.session_state.fav_list = get_user_favs(u_id)
                st.rerun()
            else: st.error("Hatalı Giriş!")
    with t2:
        n_u = st.text_input("Yeni Kullanıcı:", key="r_u"); n_p = st.text_input("Yeni Şifre:", type="password", key="r_p")
        if st.button("Kayıt Ol", use_container_width=True):
            try: supabase.table("users").insert({"username": n_u, "password": n_p}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Hata!")
    st.stop()

# --- ÜST PANEL ---
st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.write(f"👤 **{st.session_state.user}**")
    if st.button("🚪 Çıkış"): st.session_state.user = None; st.session_state.pop('lottie_shown', None); st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🏟️ KARİYER RULETİ", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan"]}
    
    f1, f2, f3 = st.columns(3)
    with f1: name_f = st.text_input("👤 Oyuncu Ara:"); team_f = st.text_input("🏟️ Takım Ara:")
    with f2: reg_f = st.selectbox("🌍 Bölge:", list(REG_TR.keys())); country_f = st.text_input("🏳️ Ülke Ara (Örn: Brazil):")
    with f3: pos_f = st.selectbox("👟 Mevki:", list(POS_TR.keys())); sort_f = st.selectbox("🔃 Sıralama:", ["pa", "ca", "yas"])
    
    v1, v2 = st.columns(2)
    with v1: age_f = st.slider("🎂 Yaş:", 14, 50, (14, 25))
    with v2: pa_f = st.slider("📊 PA:", 0, 200, (140, 200))
    
    # Piyasa Değeri Filtresi (Sayısal Giriş)
    max_val = st.number_input("💰 Max Piyasa Değeri (M€):", value=300, min_value=0, max_value=500)
    
    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if country_f: query = query.ilike("ulke", f"%{country_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REG_TR[reg_f])
    
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'''
                    <div class="player-card {"fav-active" if is_fav else ""}">
                        <span class="pa-badge">PA: {p["pa"]}</span>
                        <h3 style="margin:0;">{p["oyuncu_adi"]}</h3>
                        <p style="color:#8b949e; font-size:0.9rem; margin:5px 0;">📍 {p.get("ulke","")} | 🏟️ {p["kulup"]} | 👟 {p["mevki"]}</p>
                        <p style="font-size:0.95rem;">📊 CA: {p["ca"]} | 🎂 Yaş: {p["yas"]} | 💰 Değer: {p.get("deger", "Bilinmiyor")}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a>
                    </div>
                ''', unsafe_allow_html=True)
                ck1, ck2 = st.columns([3, 1])
                ck1.code(p['oyuncu_adi'])
                if ck2.button(f"{'⭐' if is_fav else '☆'}", key=f"btn_{p['oyuncu_adi']}"):
                    if is_fav:
                        supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute()
                        st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else:
                        supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                        st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET ---
with tabs[1]:
    if st.button("🎰 ÇEVİR!", use_container_width=True):
        lucky = supabase.table("oyuncular").select("*").gte("pa", 150).lte("yas", 21).limit(100).execute()
        if lucky.data: st.session_state.roulette_player = random.choice(lucky.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_fav = p['oyuncu_adi'] in st.session_state.fav_list
        st.markdown(f'<div class="player-card fav-active"><h2>🌟 {p["oyuncu_adi"]}</h2><p>{p["kulup"]} | PA: {p["pa"]} | Yaş: {p["yas"]}</p></div>', unsafe_allow_html=True)
        st.code(p['oyuncu_adi'])
        if st.button("⭐ Rulet Yıldızını Favorile"):
            if not is_fav:
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                st.session_state.fav_list.append(p['oyuncu_adi']); st.rerun()

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    formasyon = st.selectbox("Diziliş Seç:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2"])
    f_names = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    st.markdown('<div class="section-header">🧤 KALECİ</div>', unsafe_allow_html=True); gk = st.selectbox("GK:", f_names, key="k_gk")
    st.markdown('<div class="section-header">🛡️ DEFANS HATTI</div>', unsafe_allow_html=True)
    d_cols = st.columns(4); d1 = d_cols[0].selectbox("LB:", f_names); d2 = d_cols[1].selectbox("CB1:", f_names); d3 = d_cols[2].selectbox("CB2:", f_names); d4 = d_cols[3].selectbox("RB:", f_names)
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(3); m1 = m_cols[0].selectbox("LM/LW:", f_names); m2 = m_cols[1].selectbox("CM/DM:", f_names); m3 = m_cols[2].selectbox("RM/RW:", f_names)
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(2); s1 = s_cols[0].selectbox("ST1:", f_names); s2 = s_cols[1].selectbox("ST2:", f_names)
    if st.button("Kadro Savaşçılarını Kaydet"): st.success("Elite 11 Hazır!")

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Senin Kalıcı Favorilerin")
    db_favs = get_user_favs(st.session_state.user)
    if db_favs:
        for f_name in db_favs:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f_name}</b></div>', unsafe_allow_html=True)
            if c2.button("🗑️", key=f"del_{f_name}"):
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", f_name).execute()
                if f_name in st.session_state.fav_list: st.session_state.fav_list.remove(f_name)
                st.rerun()
    else: st.info("Favori listen boş.")

# --- 5. KARİYER RULETİ ---
with tabs[4]:
    st.subheader("🏟️ Takım Bulma Çarkı")
    lig_c = st.selectbox("Ülke/Lig Filtresi:", ["Hepsi", "Türkiye", "İngiltere", "Almanya", "İspanya", "Fransa", "İtalya", "Hollanda", "Portekiz"])
    if st.button("🏟️ ÇARK-I TAKIM!"):
        try:
            query_t = supabase.table("oyuncular").select("kulup")
            if lig_c != "Hepsi": query_t = query_t.ilike("ulke", f"%{lig_c}%")
            t_res = query_t.limit(1000).execute()
            if t_res.data:
                t_havuz = list(set([x['kulup'] for x in t_res.data]))
                secilen = random.choice(t_havuz)
                st.markdown(f'<div class="player-card fav-active" style="text-align:center;"><h3>Yolculuk Başlıyor:</h3><h1>🏟️ {secilen}</h1></div>', unsafe_allow_html=True)
            else: st.warning("Bu filtreye uygun profesyonel takım bulunamadı.")
        except: st.error("Bağlantı hatası.")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Admin Paneli")
        adm1, adm2, adm3 = st.tabs(["✏️ Veri", "📢 Duyuru", "👥 Üyeler"])
        with adm1:
            e_s = st.text_input("Oyuncu Ara:")
            if e_s:
                e_r = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_s}%").limit(5).execute()
                if e_r.data:
                    target = st.selectbox("Seç:", [x['oyuncu_adi'] for x in e_r.data])
                    n_pa = st.number_input("Yeni PA:", value=180)
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", target).execute()
                        st.success("PA Güncellendi!")
        with adm2:
            n_msg = st.text_area("Yeni Duyuru:", value=get_announcement())
            if st.button("Duyuruyu Yayınla"):
                supabase.table("sistem").update({"duyuru": n_msg}).eq("id", 1).execute(); st.rerun()
        with adm3:
            st.write("👥 **Kayıtlı Üyeler ve Şifreleri**")
            u_l = supabase.table("users").select("*").execute()
            if u_l.data: st.table(pd.DataFrame(u_l.data))
    else: st.error("Admin Yetkisi Yok.")
