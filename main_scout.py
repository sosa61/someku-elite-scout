import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI (YENİ İSİM) ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- SESSION STATE ---
if 'favs' not in st.session_state: st.session_state.favs = []
if 'squads' not in st.session_state: st.session_state.squads = {}
if 'announcements' not in st.session_state: st.session_state.announcements = ["🔥 SOMEKU SCOUT Yayında!", "💡 470.000 oyuncu arasından seçimini yap."]
if 'suggestions' not in st.session_state: st.session_state.suggestions = []
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

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .welcome-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px; }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; transition: 0.3s; }
    .player-card:hover { border-color: #58a6ff; transform: translateY(-2px); }
    .fav-active { border: 2px solid #f2cc60 !important; }
    .pa-badge { background: #238636; color: white; padding: 2px 12px; border-radius: 20px; font-weight: bold; float: right; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- HOŞ GELDİN BANNERI ---
st.markdown("""
    <div class="welcome-banner">
        <h1 style="margin:0; letter-spacing: 2px;">🕵️ SOMEKU SCOUT</h1>
        <p style="color: #8b949e; font-weight: 300;">Elite Football Data Analysis & Scouting Platform</p>
    </div>
""", unsafe_allow_html=True)

# --- DUYURULAR ---
with st.expander("📢 Sistem Duyuruları"):
    for a in st.session_state.announcements:
        st.info(a)

tabs = st.tabs(["🔍 SCOUT MERKEZİ", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİ & YENİLİK", "🛠️ ADMIN"])

# --- 1. SCOUT SEKİMESİ ---
with tabs[0]:
    with st.sidebar:
        st.header("🔎 Filtre Paneli")
        f_name = st.text_input("Oyuncu Adı:")
        f_nation = st.text_input("Ülke (Harf Duyarsız):")
        f_region = st.selectbox("Kıta/Bölge:", list(REGIONS.keys()))
        f_pos = st.selectbox("Mevki (TR):", list(POS_TR.keys()))
        f_age = st.slider("Yaş Aralığı:", 14, 50, (15, 25))
        f_pa = st.slider("Potansiyel (PA):", 0, 200, (140, 200))
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        st.divider()
        search_trigger = st.button("FİLTRELEYİ UYGULA", use_container_width=True)

    limit = 12
    offset = st.session_state.page * limit
    
    with st.spinner('🔭 Veritabanı taranıyor...'):
        query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
        if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
        if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
        if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
        if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
        res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

    # Başlık Alanı
    if not f_name and not search_trigger:
        st.subheader("🔥 Keşfet: Günün Öne Çıkan Yıldızları")
    else:
        st.subheader(f"🔍 Arama Sonuçları (Sayfa {st.session_state.page + 1})")

    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            card_class = "player-card fav-active" if is_fav else "player-card"
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            
            with cols[i % 2]:
                st.markdown(f"""
                    <div class="{card_class}">
                        <span class="pa-badge">PA: {p['pa']}</span>
                        <h3 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h3>
                        <div style="font-size:14px; color:#8b949e; margin: 5px 0;">
                            📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']} <br>
                            <b>CA:</b> {p['ca']} | <b>Değer:</b> {p['deger']}
                        </div>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"f_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p); st.toast(f"{p['oyuncu_adi']} Favorilere Eklendi!")
                    st.rerun()

        st.divider()
        cp1, cp2 = st.columns(2)
        if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if cp2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()
    else:
        st.info("Kriterlere uygun oyuncu bulunamadı.")

# --- DİĞER SEKİMELERE (KIYASLA, 11 KUR, ADMIN) DOKUNMADIK, İSİM GÜNCEL ---
with tabs[1]:
    st.subheader("⚖️ Oyuncu Kıyaslama")
    col_c1, col_c2 = st.columns(2)
    p1_n = col_c1.text_input("1. Oyuncu:")
    p2_n = col_c2.text_input("2. Oyuncu:")
    if st.button("KIYASLA"):
        r1 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p1_n}%").limit(1).execute()
        r2 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p2_n}%").limit(1).execute()
        if r1.data and r2.data: st.table(pd.DataFrame([r1.data[0], r2.data[0]]).set_index("oyuncu_adi"))

with tabs[2]:
    st.subheader("📋 11 Kişilik Kadro Planı")
    slots = ["GK", "DL", "DC1", "DC2", "DR", "MC1", "MC2", "AML", "AMR", "AMC", "ST"]
    yeni_kadro = {}
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    k_cols = st.columns(4)
    for i, s in enumerate(slots):
        yeni_kadro[s] = k_cols[i % 4].selectbox(f"{s}:", f_list, key=f"sq_{i}")
    if st.button("Kadroyu Kaydet"): st.success("Someku Scout: Kadro Kaydedildi!")

with tabs[5]:
    st.subheader("🛠️ Someku Admin")
    st.write("👥 **Kullanıcılar**")
    st.table(pd.DataFrame([{"User": "Ramazan", "Pass": "rmzn123", "Role": "Admin"}]))
