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
        "🛠️ Admin Paneli üzerinden artık oyuncu PA/CA değerleri anlık güncellenebilir."
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
        padding: 40px; 
        border-radius: 20px; 
        text-align: center; 
        border: 1px solid #3b82f6; 
        margin-bottom: 30px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .player-card { 
        background: #161b22; 
        border: 1px solid #30363d; 
        border-radius: 12px; 
        padding: 20px; 
        margin-bottom: 15px; 
        transition: all 0.3s ease;
    }
    .player-card:hover { 
        border-color: #58a6ff; 
        transform: translateY(-3px); 
        background: #1c2128;
    }
    .fav-active { border: 2px solid #f2cc60 !important; }
    .pa-badge { 
        background: linear-gradient(90deg, #238636, #2ea043); 
        color: white; 
        padding: 5px 15px; 
        border-radius: 20px; 
        font-weight: bold; 
        float: right; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .tm-link { 
        color: #58a6ff !important; 
        text-decoration: none; 
        border: 1px solid #58a6ff; 
        padding: 5px 12px; 
        border-radius: 6px; 
        font-size: 13px; 
        font-weight: 500;
    }
    .tm-link:hover { background: #58a6ff; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ (V81 HATA KORUMALI) ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p style="font-size: 1.2em; color: #8b949e;">Elite Football Data Analysis & Scouting Platform</p></div>', unsafe_allow_html=True)
    choice = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u_id = st.text_input("Kullanıcı ID / Adı:")
    u_pw = st.text_input("Şifre:", type="password")
    
    if choice == "Kayıt Ol":
        if st.button("Kayıt İşlemini Tamamla"):
            try:
                supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
                st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
            except: st.error("Kayıt hatası: 'users' tablosu eksik.")
    else:
        if st.button("Sisteme Giriş Yap"):
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
                except: st.error("Bağlantı Hatası: Sadece 'someku' girişi aktiftir.")
    st.stop()

# --- ANA PANEL ---
st.sidebar.markdown(f"### 👤 Hoş geldin, **{st.session_state.user}**")
if st.sidebar.button("🚪 Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

st.markdown('<div class="welcome-banner"><h1 style="margin:0; letter-spacing: 2px;">🕵️ SOMEKU SCOUT</h1><p style="color: #8b949e; font-weight: 300;">Elite Football Data Analysis & Scouting Platform</p></div>', unsafe_allow_html=True)

with st.expander("📢 Sistem Duyuruları & Güncellemeler"):
    for a in st.session_state.announcements:
        st.info(a)

tabs = st.tabs(["🔍 SCOUT MERKEZİ", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİ & YENİLİK", "🛠️ ADMIN"])

# --- 1. SCOUT (V80 FULL METİN VE FİLTRE) ---
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
                card_class = "player-card fav-active" if is_fav else "player-card"
                tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
                with cols[i % 2]:
                    st.markdown(f"""
                        <div class="{card_class}">
                            <span class="pa-badge">PA: {p['pa']}</span>
                            <h3 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h3>
                            <div style="font-size:14px; color:#8b949e; margin: 10px 0;">
                                📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']} <br>
                                <b>CA:</b> {p['ca']} | <b>Değer:</b> {p['deger']}
                            </div>
                            <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"⭐ {'Çıkar' if is_fav else 'Ekle'}", key=f"f_{p['oyuncu_adi']}_{i}"):
                        if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                        else: st.session_state.favs.append(p); st.toast("Eklendi!")
                        st.rerun()
            
            cp1, cp2 = st.columns(2)
            if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
            if cp2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()
    except: st.warning("Veritabanı meşgul, lütfen filtreyi tekrar uygulayın.")

# --- 2. KIYASLA (AKILLI ARAMA) ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Oyuncu Kıyaslama")
    col_c1, col_c2 = st.columns(2)
    p1_in = col_c1.text_input("1. Oyuncu Ara:")
    p1_final = None
    if p1_in:
        p1_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_in}%").limit(5).execute()
        p1_final = col_c1.selectbox("Eşleşen (1):", [x['oyuncu_adi'] for x in p1_res.data])

    p2_in = col_c2.text_input("2. Oyuncu Ara:")
    p2_final = None
    if p2_in:
        p2_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_in}%").limit(5).execute()
        p2_final = col_c2.selectbox("Eşleşen (2):", [x['oyuncu_adi'] for x in p2_res.data])

    if st.button("KIYASLA"):
        if p1_final and p2_final:
            r1 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p1_final).limit(1).execute()
            r2 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p2_final).limit(1).execute()
            st.table(pd.DataFrame([r1.data[0], r2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR VE 5. ÖNERİLER (V80 Metinleri İle) ---
with tabs[2]:
    st.subheader("📋 11 Kişilik Kadro Planı")
    slots = ["GK", "DL", "DC1", "DC2", "DR", "MC1", "MC2", "AML", "AMR", "AMC", "ST"]
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Favori listeniz boş"]
    k_cols = st.columns(4)
    for i, s in enumerate(slots):
        k_cols[i % 4].selectbox(f"{s}:", f_list, key=f"sq_{i}")

with tabs[4]:
    st.subheader("💡 Öneri & Yenilik Bildirimi")
    with st.form("suggest"):
        u_msg = st.text_area("Siteye eklenmesini istediğiniz özellikler veya veri hataları:")
        if st.form_submit_button("Gönder"):
            try:
                supabase.table("oneriler").insert({"ad": st.session_state.user, "mesaj": u_msg}).execute()
                st.success("Talebiniz Someku Admin'e iletildi!")
            except: st.error("Öneri tablosu bulunamadı.")

# --- 6. ADMIN (SOMEKU ÖZEL) ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Someku Kontrol Merkezi")
        a_tab1, a_tab2 = st.tabs(["✏️ Veri Düzenle", "👥 Kullanıcılar"])
        with a_tab1:
            e_search = st.text_input("Düzeltilecek Oyuncu:")
            if e_search:
                e_list = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{e_search}%").limit(5).execute()
                e_target = st.selectbox("Seç:", [x['oyuncu_adi'] for x in e_list.data])
                p_info = supabase.table("oyuncular").select("*").eq("oyuncu_adi", e_target).execute()
                if p_info.data:
                    curr = p_info.data[0]
                    n_pa = st.number_input("Yeni PA:", value=int(curr['pa']))
                    if st.button("KAYDET"):
                        supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", e_target).execute()
                        st.success("Güncellendi!")
        with a_tab2:
            try:
                u_list = supabase.table("users").select("*").execute()
                st.table(pd.DataFrame(u_list.data))
            except: st.error("Kullanıcı listesi çekilemedi.")
    else: st.error("Bu bölüm sadece someku (admin) erişimine özeldir.")
