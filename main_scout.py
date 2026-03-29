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

# --- TASARIM (CSS & ANIMASYON) ---
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
    .fav-active { border-left: 5px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; font-weight: 500; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- YÜKLEME EKRANI ---
if 'lottie_shown' not in st.session_state:
    st.markdown('<div class="loader-container"><div class="magnifier">🕵️‍♂️🔍</div><h2 style="color: #58a6ff; margin-top: 20px;">Someku Elite Veritabanı Hazırlanıyor...</h2></div>', unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.lottie_shown = True
    st.rerun()

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'favs' not in st.session_state: st.session_state.favs = []
if 'announcements' not in st.session_state: st.session_state.announcements = "🔥 SOMEKU SCOUT V83 Yayında!"
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- TANIMLAMALAR ---
POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
REGIONS = {"Hepsi": [], "Avrupa": ["Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Afrika": ["Nijerya", "Senegal", "Kamerun", "Mısır", "Fildişi Sahili", "Gana", "Cezayir"], "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador"], "Asya/Okyanusya": ["Japonya", "Güney Kore", "Avustralya"]}

# --- GİRİŞ SİSTEMİ ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Giriş Yaparak Veritabanına Erişin</p></div>', unsafe_allow_html=True)
    u_id = st.text_input("Kullanıcı Adı:")
    u_pw = st.text_input("Şifre:", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if u_id == "someku" and u_pw == "28616128Ok":
            st.session_state.user = "someku"
            st.rerun()
        else:
            try:
                res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                if res.data: st.session_state.user = res.data[0]['username']; st.rerun()
                else: st.error("Hatalı Giriş!")
            except: st.error("Sadece 'someku' girişi aktiftir!")
    st.stop()

# --- PANEL VE ÇIKIŞ ---
st.markdown(f'<div class="ann-box">{st.session_state.announcements}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("👤 Profil")
    st.write(f"Üye: **{st.session_state.user}**")
    if st.button("🚪 Çıkış Yap"):
        st.session_state.user = None
        st.session_state.pop('lottie_shown', None)
        st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT (BÖLGELER VE SAYFALAMA) ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    with f1: f_name = st.text_input("Oyuncu/Takım:"); f_team = st.text_input("Lig/Kulüp:")
    with f2: f_pos = st.selectbox("Mevki Seçin:", list(POS_TR.keys())); f_reg = st.selectbox("Bölge Seçin:", list(REGIONS.keys()))
    with f3: f_age = st.slider("Yaş:", 14, 50, (14, 25)); f_pa = st.slider("PA:", 0, 200, (140, 200))
    with f4: 
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        if st.button("🔍 UYGULA", use_container_width=True): st.session_state.page = 0

    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_team: query = query.ilike("kulup", f"%{f_team}%")
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    if f_reg != "Hepsi": query = query.in_("ulke", REGIONS[f_reg])
    
    res = query.order(sort_by, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'<div class="player-card {"fav-active" if is_fav else ""}"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3><p>🏟️ {p["kulup"]} | 👟 {p["mevki"]}<br><b>CA:</b> {p[ "ca"]} | <b>Yaş:</b> {p["yas"]}</p><a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>', unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"s_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()
        
        c_p1, c_p2 = st.columns(2)
        if c_p1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c_p2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET (FAV TUŞU EKLENDİ) ---
with tabs[1]:
    st.subheader("🎰 Wonderkid Ruleti")
    if st.button("🎰 ŞANSLI YILDIZI BUL!", use_container_width=True):
        lucky = supabase.table("oyuncular").select("*").gte("pa", 145).lte("yas", 21).limit(100).execute()
        if lucky.data: st.session_state.roulette_player = random.choice(lucky.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
        st.markdown(f'<div class="player-card fav-active"><h2>🌟 {p["oyuncu_adi"]}</h2><p>Kulüp: {p["kulup"]} | Yaş: {p["yas"]} | PA: {p["pa"]}</p></div>', unsafe_allow_html=True)
        if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Favoriye Ekle'}", key="roulette_fav"):
            if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
            else: st.session_state.favs.append(p)
            st.rerun()

# --- 3. 11 KUR (ZENGİN DİZİLİŞ) ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    form = st.selectbox("Diziliş Seçin:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2"])
    f_names = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    
    st.markdown('<div class="section-header">🧤 KALECİ</div>', unsafe_allow_html=True)
    gk = st.selectbox("Kaleci Seç:", f_names, key="gk_sel")
    
    st.markdown('<div class="section-header">🛡️ DEFANS</div>', unsafe_allow_html=True)
    d_cols = st.columns(4)
    d1 = d_cols[0].selectbox("Sol Bek:", f_names); d2 = d_cols[1].selectbox("Stoper 1:", f_names)
    d3 = d_cols[2].selectbox("Stoper 2:", f_names); d4 = d_cols[3].selectbox("Sağ Bek:", f_names)
    
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(3)
    m1 = m_cols[0].selectbox("Sol Kanat:", f_names); m2 = m_cols[1].selectbox("Merkez:", f_names); m3 = m_cols[2].selectbox("Sağ Kanat:", f_names)
    
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(3)
    s1 = s_cols[0].selectbox("Forvet 1:", f_names); s2 = s_cols[1].selectbox("Forvet 2:", f_names); s3 = s_cols[2].selectbox("Forvet 3:", f_names)
    
    if st.button("Kadroyu Kaydet"): st.success("Elite Kadro Kaydedildi!")

# --- 4. FAVORİLER (ÇÖP ÖZELLİĞİ) ---
with tabs[3]:
    st.subheader("⭐ Favori Listen")
    if st.session_state.favs:
        for f in st.session_state.favs:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f["oyuncu_adi"]}</b> ({f["kulup"]}) - PA: {f["pa"]}</div>', unsafe_allow_html=True)
            if c2.button("🗑️ SİL", key=f"del_{f['oyuncu_adi']}"):
                st.session_state.favs = [p for p in st.session_state.favs if p['oyuncu_adi'] != f['oyuncu_adi']]
                st.rerun()
    else: st.info("Favori listeniz boş. Scout kısmından oyuncu ekleyin.")

# --- 5. ÖNERİLER ---
with tabs[4]:
    st.subheader("💡 Geliştirme & Hata Bildirimi")
    with st.form("suggestion_form"):
        s_type = st.selectbox("Konu:", ["Veri Hatası", "Tasarım Hatası", "Yeni Özellik İsteği", "Giriş Sorunu"])
        s_msg = st.text_area("Mesajınız:")
        if st.form_submit_button("Gönder"):
            supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": s_type, "mesaj": s_msg}).execute()
            st.success("Talebiniz iletildi!")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        p_count = supabase.table("oyuncular").select("id", count="exact").execute().count
        st.metric("Toplam Oyuncu Sayısı", p_count)
        
        adm1, adm2, adm3 = st.tabs(["✏️ Veri Düzenle", "📢 Duyuru", "👥 Kullanıcılar"])
        with adm1:
            e_search = st.text_input("Düzenlenecek Oyuncuyu Ara (Enter):")
            if e_search:
                e_res = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_search}%").limit(5).execute()
                if e_res.data:
                    e_target = st.selectbox("Tam İsmi Seç:", [x['oyuncu_adi'] for x in e_res.data])
                    n_pa = st.number_input("Yeni PA:", value=180)
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", e_target).execute()
                        st.success("Başarıyla Güncellendi!")
        with adm2:
            new_ann = st.text_area("Duyuru:", value=st.session_state.announcements)
            if st.button("Yayınla"): st.session_state.announcements = new_ann; st.rerun()
        with adm3:
            u_list = supabase.table("users").select("*").execute()
            if u_list.data: st.table(pd.DataFrame(u_list.data))
    else: st.error("Admin Yetkisi Yok.")
