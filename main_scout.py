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
if 'announcements' not in st.session_state: st.session_state.announcements = ["🔥 SOMEKU SCOUT V81 Yayında!", "💡 470.000 oyuncu arasından seçiminizi yapın."]
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
    .fav-active { border: 2px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242,204,96,0.3); }
    .pa-badge { background: #238636; color: white; padding: 2px 12px; border-radius: 20px; font-weight: bold; float: right; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ (HATA KORUMALI) ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Lütfen Giriş Yapın</p></div>', unsafe_allow_html=True)
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
            except: st.error("Sadece Patron Girişi Aktiftir!")
    if col_b2.button("Kayıt Ol", use_container_width=True):
        try:
            supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
            st.success("Kayıt Başarılı!")
        except: st.error("Kayıt Tablosu Bulunamadı.")
    st.stop()

# --- ANA PANEL ---
st.markdown('<div class="welcome-banner"><h1 style="margin:0;">🕵️ SOMEKU SCOUT</h1><p>Elite Scouting Platform</p></div>', unsafe_allow_html=True)

tabs = st.tabs(["🔍 SCOUT", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT (ANA EKRAN FİLTRELERİ) ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        f_name = st.text_input("Oyuncu Adı:")
        f_team = st.text_input("Takım/Kulüp:")
    with f2:
        f_region = st.selectbox("Bölge:", list(REGIONS.keys()))
        f_pos = st.selectbox("Mevki:", list(POS_TR.keys()))
    with f3:
        f_age = st.slider("Yaş:", 14, 50, (15, 25))
        f_pa = st.slider("PA:", 0, 200, (140, 200))
    with f4:
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        if st.button("FİLTRELEYİ UYGULA", use_container_width=True): st.session_state.page = 0

    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_team: query = query.ilike("kulup", f"%{f_team}%")
    if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    
    res = query.order(sort_by, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            card_class = "player-card fav-active" if is_fav else "player-card"
            with cols[i % 2]:
                st.markdown(f'<div class="{card_class}"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3><p>{p["ulke"]} | {p["kulup"]} | {p["mevki"]}</p></div>', unsafe_allow_html=True)
                if st.button(f"⭐ {'Çıkar' if is_fav else 'Ekle'}", key=f"f_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()

# --- 2. KIYASLA (AKILLI ARAMA) ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Kıyaslama")
    col_c1, col_c2 = st.columns(2)
    p1_in = col_c1.text_input("1. Oyuncu Ara:")
    p1_sel = col_c1.selectbox("Eşleşen (1):", [x['oyuncu_adi'] for x in supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_in}%").limit(5).execute().data]) if p1_in else None
    p2_in = col_c2.text_input("2. Oyuncu Ara:")
    p2_sel = col_c2.selectbox("Eşleşen (2):", [x['oyuncu_adi'] for x in supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_in}%").limit(5).execute().data]) if p2_in else None
    if st.button("KIYASLA") and p1_sel and p2_sel:
        d1 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p1_sel).execute()
        d2 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p2_sel).execute()
        st.table(pd.DataFrame([d1.data[0], d2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR (BLOKLU TASARIM) ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    
    st.markdown('<div class="section-header">🛡️ DEFANS HATTI</div>', unsafe_allow_html=True)
    d_cols = st.columns(5)
    gk = d_cols[0].selectbox("GK:", f_list)
    dl = d_cols[1].selectbox("DL:", f_list)
    dc1 = d_cols[2].selectbox("DC1:", f_list)
    dc2 = d_cols[3].selectbox("DC2:", f_list)
    dr = d_cols[4].selectbox("DR:", f_list)

    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(4)
    mc1 = m_cols[0].selectbox("MC1:", f_list)
    mc2 = m_cols[1].selectbox("MC2:", f_list)
    aml = m_cols[2].selectbox("AML:", f_list)
    amr = m_cols[3].selectbox("AMR:", f_list)

    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(2)
    amc = s_cols[0].selectbox("AMC:", f_list)
    st_p = s_cols[1].selectbox("ST:", f_list)
    
    if st.button("Kadroyu Kaydet"): st.success("Kadro Kaydedildi!")

# --- 4. FAVORİLER (KATEGORİLİ) ---
with tabs[3]:
    st.subheader("⭐ Favorilerin")
    if st.session_state.favs:
        for m_key, m_val in POS_TR.items():
            m_players = [p for p in st.session_state.favs if m_key in p['mevki']]
            if m_players:
                st.write(f"### {m_val}")
                for mp in m_players:
                    c_f1, c_f2 = st.columns([5, 1])
                    c_f1.write(f"**{mp['oyuncu_adi']}** - {mp['kulup']} (PA: {mp['pa']})")
                    if c_f2.button("Sil", key=f"del_{mp['oyuncu_adi']}"):
                        st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != mp['oyuncu_adi']]
                        st.rerun()

# --- 5. ÖNERİLER ---
with tabs[4]:
    st.subheader("💡 Öneri & Bildirim")
    with st.form("suggestion"):
        u_type = st.selectbox("Konu:", ["Veri Hatası", "Yeni Özellik", "Hata Bildirimi"])
        u_msg = st.text_area("Mesajınız:")
        if st.form_submit_button("Gönder"):
            supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": u_type, "mesaj": u_msg}).execute()
            st.success("İletildi!")

# --- 6. ADMIN (FULL KONTROL) ---
with tabs[5]:
    if st.session_state.user == "someku":
        p_count = supabase.table("oyuncular").select("id", count="exact").execute().count
        u_count = supabase.table("users").select("id", count="exact").execute().count
        st.metric("Toplam Oyuncu", p_count)
        st.metric("Toplam Kullanıcı", u_count)
        
        adm_tabs = st.tabs(["✏️ Veri Düzenle", "👥 Kullanıcılar", "📢 Duyurular"])
        with adm_tabs[0]:
            e_name = st.text_input("Düzenlenecek Oyuncu:")
            if e_name:
                e_data = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_name}%").limit(1).execute()
                if e_data.data:
                    new_pa = st.number_input("Yeni PA:", value=int(e_data.data[0]['pa']))
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": new_pa}).eq("oyuncu_adi", e_data.data[0]['oyuncu_adi']).execute()
                        st.success("PA Güncellendi!")
        with adm_tabs[1]:
            users = supabase.table("users").select("*").execute()
            st.table(pd.DataFrame(users.data)) # Kullanıcılar ve Şifreler
        with adm_tabs[2]:
            new_ann = st.text_area("Yeni Duyuru:")
            if st.button("Duyuruyu Değiştir"): st.session_state.announcements = [new_ann]; st.rerun()
    else: st.error("Yetki Yok.")
