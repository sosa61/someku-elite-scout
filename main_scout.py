import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
from streamlit_lottie import st_lottie
import requests

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- ANIMASYON FONKSİYONU ---
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_scout = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_m6cu9msc.json") # Büyüteçli Scout Animasyonu

# --- YÜKLEME EKRANI (SADECE İLK AÇILIŞTA) ---
if 'lottie_shown' not in st.session_state:
    with st.container():
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st_lottie(lottie_scout, height=300, key="initial_load")
        st.markdown("<h2 style='text-align: center; color: #58a6ff;'>Someku Elite Veritabanı Hazırlanıyor...</h2>", unsafe_allow_html=True)
        time.sleep(2) # 2 saniye animasyon göster
        st.session_state.lottie_shown = True
        st.rerun()

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'favs' not in st.session_state: st.session_state.favs = []
if 'announcements' not in st.session_state: 
    st.session_state.announcements = "🔥 SOMEKU SCOUT V81 Yayında! | 💡 470.000 oyuncu arasından seçiminizi yapın."
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- TANIMLAMALAR (TÜRKÇE MEVKİLER) ---
REGIONS = {
    "Hepsi": [], "Avrupa": ["Almanya", "Fransa", "İngiltere", "İtalya", "İspanya"],
    "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka"], "Afrika": ["Nijerya", "Senegal", "Mısır"],
    "Güney Amerika": ["Brezilya", "Arjantin"], "Asya/Okyanusya": ["Japonya", "Güney Kore"]
}

POS_TR = {
    "Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R",
    "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R",
    "Ofansif Orta Saha": "AM C", "Forvet": "ST"
}

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .welcome-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px; }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 18px; margin-bottom: 12px; transition: 0.3s; border-left: 5px solid #3b82f6; }
    .fav-active { border-left: 5px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; font-weight: 500; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Giriş Yaparak Veritabanına Erişin</p></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    u_id = c1.text_input("Kullanıcı Adı:")
    u_pw = c2.text_input("Şifre:", type="password")
    col_b1, col_b2 = st.columns(2)
    if col_b1.button("Giriş Yap", use_container_width=True):
        if u_id == "someku" and u_pw == "28616128Ok":
            st.session_state.user = "someku"
            st.rerun()
        else:
            try:
                res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                if res.data: st.session_state.user = res.data[0]['username']; st.rerun()
                else: st.error("Hatalı Giriş!")
            except: st.error("Bağlantı Hatası!")
    st.stop()

# --- DUYURU VE ÇIKIŞ ---
st.markdown(f'<div class="ann-box">{st.session_state.announcements}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("👤 Profil")
    st.write(f"Hoş geldin, **{st.session_state.user}**")
    if st.button("🚪 Hesaptan Çıkış", use_container_width=True):
        st.session_state.user = None
        st.session_state.pop('lottie_shown', None)
        st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 WONDERKID RULETİ", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    with f1: f_name = st.text_input("Oyuncu Adı:"); f_team = st.text_input("Takım/Kulüp:")
    with f2: f_region = st.selectbox("Bölge:", list(REGIONS.keys())); f_pos = st.selectbox("Mevki (TR):", list(POS_TR.keys()))
    with f3: f_age = st.slider("Yaş Aralığı:", 14, 50, (15, 25)); f_pa = st.slider("PA Aralığı:", 0, 200, (140, 200))
    with f4: 
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        if st.button("🔍 UYGULA", use_container_width=True): st.session_state.page = 0

    limit = 12
    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_team: query = query.ilike("kulup", f"%{f_team}%")
    if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    
    res = query.order(sort_by, desc=True).range(st.session_state.page*limit, (st.session_state.page*limit)+limit-1).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'''
                    <div class="player-card {'fav-active' if is_fav else ''}">
                        <span class="pa-badge">PA: {p["pa"]}</span>
                        <h3 style="margin:0;">{p["oyuncu_adi"]}</h3>
                        <p style="color:#8b949e; margin:5px 0;">🏟️ {p["kulup"]} | 📍 {p["ulke"]} | 👟 {p["mevki"]}</p>
                        <p style="font-size:0.9rem;"><b>CA:</b> {p["ca"]} | <b>Yaş:</b> {p["yas"]} | <b>Değer:</b> {p["deger"]}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt Profili ➔</a>
                    </div>
                ''', unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"sc_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()

# --- 2. WONDERKID RULETİ (MAX 21 YAŞ) ---
with tabs[1]:
    st.subheader("🎰 Wonderkid Ruleti")
    st.write("Butona bas ve 145+ PA ve **Maksimum 21 Yaş** olan rastgele bir yıldızı keşfet!")
    
    if st.button("🎰 ÇEVİR!", use_container_width=True):
        lucky_res = supabase.table("oyuncular").select("*").gte("pa", 145).lte("yas", 21).limit(100).execute()
        if lucky_res.data:
            st.session_state.roulette_player = random.choice(lucky_res.data)
            st.balloons()

    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        st.markdown(f'''
            <div class="player-card fav-active" style="max-width: 600px; margin: 0 auto; border: 2px solid #f2cc60;">
                <h1 style="text-align:center; color:#f2cc60;">🌟 ŞANSLI WONDERKID 🌟</h1>
                <span class="pa-badge" style="font-size: 1.5rem;">PA: {p["pa"]}</span>
                <h2 style="margin:0;">{p["oyuncu_adi"]}</h2>
                <hr style="border-color:#30363d;">
                <p style="font-size:1.2rem;">🏟️ <b>Kulüp:</b> {p["kulup"]} | 🎂 <b>Yaş:</b> {p["yas"]}</p>
                <p style="font-size:1.2rem;">📍 <b>Ülke:</b> {p["ulke"]} | 👟 <b>Mevki:</b> {p["mevki"]}</p>
                <a href="{tm_url}" target="_blank" class="tm-link" style="font-size:1rem; padding:10px;">Transfermarkt Profili ➔</a>
            </div>
        ''', unsafe_allow_html=True)
        if st.button(f"{'⭐ Favoriden Çıkar' if is_fav else '⭐ Favoriye Ekle'}", key="roulette_fav"):
            if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
            else: st.session_state.favs.append(p)
            st.rerun()

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    formasyon = st.selectbox("Diziliş:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1"])
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    st.markdown('<div class="section-header">🛡️ DEFANS</div>', unsafe_allow_html=True)
    d_cols = st.columns(5)
    gk = d_cols[0].selectbox("GK", f_list); dl = d_cols[1].selectbox("DL", f_list); dr = d_cols[4].selectbox("DR", f_list)
    dc1 = d_cols[2].selectbox("DC1", f_list); dc2 = d_cols[3].selectbox("DC2", f_list)
    st.markdown('<div class="section-header">🎯 HÜCUM</div>', unsafe_allow_html=True)
    h_cols = st.columns(4)
    mc = h_cols[0].selectbox("MC", f_list); st1 = h_cols[3].selectbox("ST", f_list)
    if st.button("Kadroyu Kaydet"): st.success("Kadro Kaydedildi!")

# --- 4. FAVORİLER (SİLME ÖZELLİĞİ) ---
with tabs[3]:
    st.subheader("⭐ Favori Listeniz")
    if st.session_state.favs:
        for f in st.session_state.favs:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="player-card fav-active" style="padding:10px; margin-bottom:5px;"><b>{f["oyuncu_adi"]}</b> - {f["kulup"]} | PA: {f["pa"]}</div>', unsafe_allow_html=True)
            if c2.button("🗑️ Sil", key=f"del_{f['oyuncu_adi']}"):
                st.session_state.favs = [p for p in st.session_state.favs if p['oyuncu_adi'] != f['oyuncu_adi']]
                st.rerun()

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        at1, at2 = st.tabs(["✏️ Veri Düzenle", "📢 Duyuru Paneli"])
        with at1:
            e_search = st.text_input("Oyuncu Ara:")
            if e_search:
                e_res = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_search}%").limit(1).execute()
                if e_res.data:
                    curr = e_res.data[0]
                    st.info(f"Düzenlenen: {curr['oyuncu_adi']}")
                    n_pa = st.number_input("Yeni PA:", value=int(curr['pa']))
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", curr['oyuncu_adi']).execute()
                        st.success("PA Güncellendi!")
        with at2:
            new_ann = st.text_area("Duyuru Metni:", value=st.session_state.announcements)
            if st.button("Duyuruyu Yayınla"):
                st.session_state.announcements = new_ann
                st.rerun()
