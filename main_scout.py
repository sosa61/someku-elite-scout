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
    .magnifier { font-size: 100px; animation: search 2s infinite ease-in-out; }
    @keyframes search {
        0% { transform: translate(-20px, -20px) rotate(0deg); }
        50% { transform: translate(20px, 20px) rotate(15deg); }
        100% { transform: translate(-20px, -20px) rotate(0deg); }
    }
    .welcome-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px; }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; margin-bottom: 12px; transition: 0.3s; border-left: 5px solid #3b82f6; }
    .fav-active { border: 2px solid #f2cc60 !important; border-left: 8px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; font-weight: 500; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- KALICI VERİ FONKSİYONLARI (HATA KORUMALI) ---
def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V84 Yayında!"
    except: return "🔥 SOMEKU SCOUT V84 Yayında!"

# --- YÜKLEME EKRANI ---
if 'lottie_shown' not in st.session_state:
    st.markdown('<div class="loader-container"><div class="magnifier">🕵️‍♂️🔍</div><h2 style="color: #58a6ff; margin-top: 20px;">Someku Elite Veritabanı Hazırlanıyor...</h2></div>', unsafe_allow_html=True)
    time.sleep(1.5)
    st.session_state.lottie_shown = True
    st.rerun()

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ / KAYIT SİSTEMİ ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Giriş Yapın veya Yeni Hesap Oluşturun</p></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        u_id = st.text_input("Kullanıcı Adı:", key="l_u")
        u_pw = st.text_input("Şifre:", type="password", key="l_p")
        if st.button("Giriş", use_container_width=True):
            if u_id == "someku" and u_pw == "28616128Ok":
                st.session_state.user = "someku"
                st.rerun()
            else:
                try:
                    res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                    if res.data:
                        st.session_state.user = res.data[0]['username']
                        st.rerun()
                    else: st.error("Hatalı Giriş!")
                except: st.error("Bağlantı Hatası!")
    with t2:
        n_u = st.text_input("Yeni Kullanıcı:", key="r_u")
        n_p = st.text_input("Yeni Şifre:", type="password", key="r_p")
        if st.button("Kayıt Ol", use_container_width=True):
            try:
                supabase.table("users").insert({"username": n_u, "password": n_p}).execute()
                st.success("Kayıt Başarılı! Giriş yapabilirsiniz.")
            except: st.error("Veritabanı hatası veya kullanıcı adı mevcut.")
    st.stop()

# --- ÜST PANEL ---
st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.write(f"👤 **{st.session_state.user}**")
    if st.button("🚪 Çıkış"):
        st.session_state.user = None
        st.session_state.pop('lottie_shown', None)
        st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REGIONS = {"Hepsi": [], "Avrupa": ["Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz"], "Afrika": ["Nijerya", "Senegal", "Mısır"], "Güney Amerika": ["Brezilya", "Arjantin"]}
    
    with f1: name_f = st.text_input("Oyuncu/Takım:"); team_f = st.text_input("Lig/Kulüp:")
    with f2: pos_f = st.selectbox("Mevki:", list(POS_TR.keys())); reg_f = st.selectbox("Bölge:", list(REGIONS.keys()))
    with f3: age_f = st.slider("Yaş:", 14, 50, (15, 25)); pa_f = st.slider("PA:", 0, 200, (140, 200))
    with f4: sort_f = st.selectbox("Sıra:", ["pa", "ca", "yas"])
    
    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REGIONS[reg_f])
    
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'<div class="player-card {"fav-active" if is_fav else ""}"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3><p>{p["kulup"]} | {p["mevki"]}<br>CA: {p["ca"]} | Yaş: {p["yas"]}</p><a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>', unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Favorile'}", key=f"btn_{p['oyuncu_adi']}"):
                    if is_fav: st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else: st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET ---
with tabs[1]:
    st.subheader("🎰 Wonderkid Ruleti")
    if st.button("🎰 ÇEVİR!", use_container_width=True):
        lucky = supabase.table("oyuncular").select("*").gte("pa", 145).lte("yas", 21).limit(100).execute()
        if lucky.data: st.session_state.roulette_player = random.choice(lucky.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_fav = p['oyuncu_adi'] in st.session_state.fav_list
        st.markdown(f'<div class="player-card fav-active"><h2>🌟 {p["oyuncu_adi"]}</h2><p>{p["kulup"]} | PA: {p["pa"]}</p></div>', unsafe_allow_html=True)
        if st.button("⭐ Favoriye Ekle", key="roul_fav"):
            if p['oyuncu_adi'] not in st.session_state.fav_list:
                st.session_state.fav_list.append(p['oyuncu_adi'])
                st.rerun()

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    form = st.selectbox("Diziliş Seçin:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2"])
    f_names = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    st.markdown('<div class="section-header">🧤 KALECİ</div>', unsafe_allow_html=True)
    gk = st.selectbox("GK:", f_names)
    st.markdown('<div class="section-header">🛡️ DEFANS</div>', unsafe_allow_html=True)
    d_cols = st.columns(4)
    dl = d_cols[0].selectbox("DL:", f_names); dc1 = d_cols[1].selectbox("DC1:", f_names); dc2 = d_cols[2].selectbox("DC2:", f_names); dr = d_cols[3].selectbox("DR:", f_names)
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(3)
    ml = m_cols[0].selectbox("AML:", f_names); mc = m_cols[1].selectbox("MC:", f_names); mr = m_cols[2].selectbox("AMR:", f_names)
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(3)
    s1 = s_cols[0].selectbox("ST1:", f_names); s2 = s_cols[1].selectbox("ST2:", f_names); s3 = s_cols[2].selectbox("ST3:", f_names)
    if st.button("Kadroyu Kaydet"): st.success("Elite 11 Kaydedildi!")

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Favori Listen")
    if st.session_state.fav_list:
        for f_name in st.session_state.fav_list:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f_name}</b></div>', unsafe_allow_html=True)
            if c2.button("🗑️", key=f"del_{f_name}"):
                st.session_state.fav_list.remove(f_name)
                st.rerun()
    else: st.info("Henüz favori eklenmedi.")

# --- 5. ÖNERİLER ---
with tabs[4]:
    st.subheader("💡 Öneri & Hata Bildirimi")
    with st.form("o_form"):
        o_t = st.selectbox("Konu:", ["Veri Hatası", "Tasarım", "Özellik İsteği"])
        o_m = st.text_area("Mesaj:")
        if st.form_submit_button("Gönder"):
            try:
                supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": o_t, "mesaj": o_m}).execute()
                st.success("Admin'e iletildi!")
            except: st.error("Gönderim sırasında hata oluştu.")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Admin Paneli")
        try:
            p_c = supabase.table("oyuncular").select("id", count="exact").execute().count
            st.metric("Toplam Oyuncu", p_c)
        except: pass
        adm1, adm2, adm3, adm4 = st.tabs(["✏️ Veri", "📢 Duyuru", "👥 Üyeler", "📩 Öneriler"])
        with adm1:
            e_s = st.text_input("Oyuncu Ara:")
            if e_s:
                e_r = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_s}%").limit(5).execute()
                if e_r.data:
                    e_target = st.selectbox("Seç:", [x['oyuncu_adi'] for x in e_r.data])
                    n_p = st.number_input("Yeni PA:", value=180)
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": n_p}).eq("oyuncu_adi", e_target).execute()
                        st.success("Güncellendi!")
        with adm2:
            n_msg = st.text_area("Yeni Duyuru:", value=get_announcement())
            if st.button("Kaydet"):
                try:
                    supabase.table("sistem").update({"duyuru": n_msg}).eq("id", 1).execute()
                    st.rerun()
                except: st.error("Bu işlem için 'sistem' tablosu gerekli.")
        with adm3:
            try:
                u_l = supabase.table("users").select("*").execute()
                if u_l.data: st.table(pd.DataFrame(u_l.data))
            except: st.info("Kullanıcı listesi okunamıyor.")
        with adm4:
            try:
                o_l = supabase.table("oneriler").select("*").execute()
                if o_l.data: st.table(pd.DataFrame(o_l.data))
            except: st.info("Öneri listesi okunamıyor.")
    else: st.error("Admin Yetkisi Yok.")
