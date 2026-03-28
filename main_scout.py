import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'favs' not in st.session_state: st.session_state.favs = []
if 'announcements' not in st.session_state: 
    st.session_state.announcements = [
        "🔥 SOMEKU SCOUT Yayında! Elite Scouting Deneyimi Başladı.", 
        "💡 470.000'den fazla oyuncu verisiyle FM 2026 dünyasını keşfedin.",
        "🛠️ Admin Paneli üzerinden oyuncu PA/CA değerleri anlık güncellenebilir."
    ]
if 'page' not in st.session_state: st.session_state.page = 0

# --- TANIMLAMALAR ---
REGIONS = {
    "Hepsi": [],
    "Avrupa": ["Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika"],
    "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"],
    "Afrika": ["Nijerya", "Senegal", "Kamerun", "Mısır", "Fildişi Sahili", "Gana", "Cezayir"],
    "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador"],
    "Asya/Okyanusya": ["Japonya", "Güney Kore", "Avustralya", "Suudi Arabistan"]
}

POS_TR = {
    "Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R",
    "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R",
    "Ofansif Orta Saha": "AM C", "Forvet": "ST"
}

# --- TASARIM (CSS - V80 TAM TASARIM) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .welcome-banner { 
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); 
        padding: 40px; border-radius: 20px; text-align: center; border: 1px solid #3b82f6; margin-bottom: 30px; 
    }
    .player-card { 
        background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; transition: 0.3s;
    }
    .player-card:hover { border-color: #58a6ff; transform: translateY(-3px); background: #1c2128; }
    .fav-active { border: 2px solid #f2cc60 !important; }
    .pa-badge { background: #238636; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; float: right; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 5px 12px; border-radius: 6px; font-size: 13px; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ (HATAYI ENGELLEYEN ÖZEL SÜRÜM) ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p style="color: #8b949e;">Lütfen Devam Etmek İçin Giriş Yapın</p></div>', unsafe_allow_html=True)
    choice = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_id = st.text_input("Kullanıcı ID / Adı:")
    u_pw = st.text_input("Şifre:", type="password")
    
    if choice == "Giriş Yap":
        if st.button("Sisteme Giriş Yap"):
            # ÖNCELİK: Senin Özel Bilgilerin (Veritabanı hatası olsa bile seni içeri alır)
            if u_id == "someku" and u_pw == "2861628Ok":
                st.session_state.user = "someku"
                st.rerun()
            else:
                try:
                    user_check = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                    if user_check.data:
                        st.session_state.user = user_check.data[0]['username']
                        st.rerun()
                    else: st.error("Hatalı ID veya Şifre!")
                except: st.error("Bağlantı Hatası: 'users' tablosu eksik. Ama 'someku' girişi aktiftir!")
    else:
        if st.button("Kayıt Ol"):
            try:
                supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
                st.success("Kayıt başarılı!")
            except: st.error("Hata: Veritabanında 'users' tablosu bulunamadı.")
    st.stop()

# --- ANA PANEL ---
st.sidebar.markdown(f"### 👤 Hoş geldin, **{st.session_state.user}**")
if st.sidebar.button("🚪 Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

st.markdown('<div class="welcome-banner"><h1 style="margin:0; letter-spacing: 2px;">🕵️ SOMEKU SCOUT</h1><p style="color: #8b949e; font-weight: 300;">Elite Football Data Analysis & Scouting Platform</p></div>', unsafe_allow_html=True)

with st.expander("📢 Sistem Duyuruları & Güncellemeler"):
    for a in st.session_state.announcements: st.info(a)

tabs = st.tabs(["🔍 SCOUT MERKEZİ", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT MERKEZİ ---
with tabs[0]:
    with st.sidebar:
        st.header("🔎 Filtre Paneli")
        f_name = st.text_input("Oyuncu Adı:")
        f_nation = st.text_input("Ülke:")
        f_region = st.selectbox("Bölge:", list(REGIONS.keys()))
        f_pos = st.selectbox("Mevki:", list(POS_TR.keys()))
        f_age = st.slider("Yaş:", 14, 50, (15, 25))
        f_pa = st.slider("PA:", 0, 200, (140, 200))
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        st.divider()
        search_trigger = st.button("FİLTRELEYİ UYGULA", use_container_width=True)

    limit = 12
    offset = st.session_state.page * limit
    try:
        query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
        if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
        if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
        if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
        if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
        res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

        st.subheader(f"🔍 Arama Sonuçları (Sayfa {st.session_state.page + 1})")
        if res.data:
            cols = st.columns(2)
            for i, p in enumerate(res.data):
                is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
                tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
                with cols[i % 2]:
                    st.markdown(f'<div class="player-card"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]} ({p["yas"]})</h3><p>📍 {p["ulke"]} | 🏟️ {p["kulup"]} | 👟 {p["mevki"]}<br><b>CA:</b> {p["ca"]} | <b>Değer:</b> {p["deger"]}</p><a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>', unsafe_allow_html=True)
                    if st.button(f"⭐ {'Çıkar' if is_fav else 'Ekle'}", key=f"f_{p['oyuncu_adi']}_{i}"):
                        if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                        else: st.session_state.favs.append(p)
                        st.rerun()
            
            cp1, cp2 = st.columns(2)
            if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
            if cp2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()
    except: st.warning("Arama sonuçları için filtreleri uygulayın!")

# --- 2. KIYASLA (AKILLI ARAMA) ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Oyuncu Kıyaslama")
    col1, col2 = st.columns(2)
    p1_in = col1.text_input("1. Oyuncu Ara:")
    if p1_in:
        try:
            p1_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_in}%").limit(5).execute()
            p1_sel = col1.selectbox("Eşleşen (1):", [x['oyuncu_adi'] for x in p1_res.data])
        except: pass

    p2_in = col2.text_input("2. Oyuncu Ara:")
    if p2_in:
        try:
            p2_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_in}%").limit(5).execute()
            p2_sel = col2.selectbox("Eşleşen (2):", [x['oyuncu_adi'] for x in p2_res.data])
        except: pass

# --- 6. ADMIN (SOMEKU ÖZEL) ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Someku Admin Paneli")
        m_tab1, m_tab2 = st.tabs(["✏️ Veri Düzenle", "👥 Kullanıcılar"])
        with m_tab1:
            e_search = st.text_input("Düzeltilecek Oyuncu (Ara):")
            if e_search:
                e_list = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{e_search}%").limit(5).execute()
                e_target = st.selectbox("Seç:", [x['oyuncu_adi'] for x in e_list.data])
                n_pa = st.number_input("Yeni PA:", value=180)
                if st.button("PA'yı Güncelle"):
                    supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", e_target).execute()
                    st.success("PA Güncellendi!")
        with m_tab2:
            try:
                u_list = supabase.table("users").select("*").execute()
                st.table(pd.DataFrame(u_list.data))
            except: st.info("Kayıtlı kullanıcı yok veya 'users' tablosu eksik.")
    else: st.error("Bu bölüm sadece someku (admin) erişimine özeldir.")
