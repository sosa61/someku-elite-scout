import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU SUPREME SCOUT", layout="wide", page_icon="🕵️")

# --- SESSION STATE (Favoriler, Kadro ve Öneriler) ---
if 'favs' not in st.session_state: st.session_state.favs = []
if 'squads' not in st.session_state: st.session_state.squads = {}
if 'page' not in st.session_state: st.session_state.page = 0

# --- BÖLGESEL TANIMLAMALAR ---
REGIONS = {
    "Hepsi": [],
    "Afrikalı": ["Nijerya", "Senegal", "Kamerun", "Mısır", "Fildişi Sahili", "Gana", "Fas", "Cezayir"],
    "Kuzey Avrupalı": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"],
    "Güney Amerikalı": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Şili"],
    "Balkan": ["Sırbistan", "Hırvatistan", "Bosna-Hersek", "Arnavutluk", "Yunanistan"]
}

POS_MAP = {
    "Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Bek": "D RL", 
    "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Ofansif Orta Saha": "AM C", 
    "Kanat": "AM RL", "Forvet": "ST"
}

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .player-card { background: #161b22; border-radius: 12px; padding: 15px; margin-bottom: 10px; border: 1px solid #30363d; position: relative; }
    .pa-badge { background: #238636; color: white; padding: 2px 10px; border-radius: 10px; font-weight: bold; float: right; }
    .fav-active { border: 2px solid #f2cc60 !important; }
    .tm-btn { color: #58a6ff !important; border: 1px solid #58a6ff; padding: 2px 8px; border-radius: 5px; text-decoration: none; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔍 GENİŞ SCOUT", "📋 KADRO PLANLAMA", "⭐ FAVORİLER", "💡 ÖNERİ YAP", "🛠️ ADMIN"])

# --- 1. SCOUT SEKİMESİ ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    f_name = c1.text_input("Oyuncu Adı (Harf duyarsız):")
    f_nation = c2.text_input("Ülke (Örn: İspanya veya ispanya):")
    f_region = c3.selectbox("Bölgesel Filtre:", list(REGIONS.keys()))

    s1, s2, s3 = st.columns(3)
    f_pos_tr = s1.selectbox("Mevki (Türkçe):", list(POS_MAP.keys()))
    f_pa = s2.slider("Potansiyel (PA):", 0, 200, (140, 200))
    sort_by = s3.selectbox("Sıralama:", ["pa", "ca", "yas"])

    limit = 15
    offset = st.session_state.page * limit

    # Query İnşası
    query = supabase.table("oyuncular").select("*").gte("pa", f_pa[0]).lte("pa", f_pa[1])
    
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
    if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
    if f_pos_tr != "Hepsi": query = query.ilike("mevki", f"%{POS_MAP[f_pos_tr]}%")

    res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

    # Sayfalama
    cp1, cp2, cp3 = st.columns([1,2,1])
    if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if cp3.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

    if res.data:
        for p in res.data:
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            card_style = "player-card fav-active" if is_fav else "player-card"
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            
            st.markdown(f"""
                <div class="{card_style}">
                    <span class="pa-badge">PA: {p['pa']}</span>
                    <h4 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h4>
                    <div style="font-size:13px; color:#8b949e;">
                        📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']} <br>
                        <b>CA:</b> {p['ca']} | <b>Değer:</b> {p['deger']}
                    </div>
                    <a href="{tm_url}" target="_blank" class="tm-btn">Transfermarkt Profili</a>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"{'⭐ Favorilerden Çıkar' if is_fav else '⭐ Favoriye Ekle'}", key=f"f_{p['oyuncu_adi']}_{offset}"):
                if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                else: st.session_state.favs.append(p)
                st.rerun()

# --- 2. KADRO PLANLAMA (MANUEL VE DİZİLİŞLİ) ---
with tabs[1]:
    st.subheader("📋 Taktik Tahtası")
    taktik = st.selectbox("Diziliş Seç:", ["4-3-3", "4-4-2", "3-5-2"])
    kadro_adi = st.text_input("Kadro İsmi (Kaydetmek için):", "Yeni Taktik")
    
    # Manuel Oyuncu Seçimi (Favorilerden veya aramadan çekebilirsin)
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.write("🏃 Oyuncu Seç")
        secilen_o = st.selectbox("Favorilerden Seç:", [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Favori yok"])
    
    if st.button("Kadroya Kaydet"):
        st.session_state.squads[kadro_adi] = {"taktik": taktik, "oyuncular": st.session_state.favs[:11]}
        st.success("Kadro Taslağı Kaydedildi!")

    if st.session_state.squads:
        for k, v in st.session_state.squads.items():
            with st.expander(f"📂 {k} ({v['taktik']})"):
                st.write(pd.DataFrame(v['oyuncular'])[['oyuncu_adi', 'mevki', 'pa']])
                if st.button("Kadroyu Sil", key=f"del_{k}"):
                    del st.session_state.squads[k]; st.rerun()

# --- 3. FAVORİLER ---
with tabs[2]:
    st.subheader("⭐ Takip Listesi")
    if st.session_state.favs:
        for f in st.session_state.favs:
            c_f1, c_f2 = st.columns([4,1])
            c_f1.write(f"**{f['oyuncu_adi']}** - {f['kulup']} ({f['pa']} PA)")
            if c_f2.button("Sil", key=f"del_fav_{f['oyuncu_adi']}"):
                st.session_state.favs.remove(f); st.rerun()

# --- 4. ÖNERİ SEKİMESİ ---
with tabs[3]:
    st.subheader("💡 Scout Önerisi Gönder")
    oneri_o = st.text_input("Önerdiğin Oyuncu:")
    oneri_n = st.text_area("Neden Alınmalı?")
    if st.button("Admin'e Gönder"):
        # Burada basitçe bir tabloya veya session'a atıyoruz
        st.success("Önerin iletildi!")

# --- 5. ADMIN PANELİ ---
with tabs[4]:
    st.subheader("🛠️ Sistem Yönetimi")
    st.write("👥 **Kullanıcı Listesi (Demo)**")
    # Not: Gerçek kullanıcı sistemi için Supabase Auth tablosu gerekir, burada görsel temsil yapıyoruz
    st.table(pd.DataFrame([{"User": "Ramazan", "Pass": "****123", "Role": "Admin"}]))
    
    st.write("📩 **Gelen Öneriler**")
    st.info("Henüz yeni öneri yok.")
