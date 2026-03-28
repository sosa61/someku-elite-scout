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
    st.session_state.announcements = "🔥 SOMEKU SCOUT V81 Yayında! | 💡 470.000 oyuncu arasından seçiminizi yapın."
if 'page' not in st.session_state: st.session_state.page = 0

# --- TANIMLAMALAR ---
REGIONS = {
    "Hepsi": [], "Avrupa": ["Almanya", "Fransa", "İngiltere", "İtalya", "İspanya"],
    "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka"], "Afrika": ["Nijerya", "Senegal", "Mısır"],
    "Güney Amerika": ["Brezilya", "Arjantin"], "Asya/Okyanusya": ["Japonya", "Güney Kore"]
}

POS_TR = {
    "Hepsi": "Hepsi", "GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek",
    "DM": "Ön Libero", "M C": "Merkez Orta Saha", "AM L": "Sol Kanat", "AM R": "Sağ Kanat",
    "AM C": "Ofansif Orta Saha", "ST": "Forvet"
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
            except: st.error("Sadece Patron Girişi Aktiftir!")
    if col_b2.button("Kayıt Ol", use_container_width=True):
        try:
            supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
            st.success("Kayıt Başarılı!")
        except: st.error("Kayıt Tablosu Bulunamadı.")
    st.stop()

# --- DUYURU VE ÇIKIŞ ---
st.markdown(f'<div class="ann-box">{st.session_state.announcements}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("👤 Profil")
    st.write(f"Hoş geldin, **{st.session_state.user}**")
    if st.button("🚪 Hesaptan Çıkış", use_container_width=True):
        st.session_state.user = None
        st.rerun()

tabs = st.tabs(["🔍 SCOUT", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    with f1: f_name = st.text_input("Oyuncu Adı:"); f_team = st.text_input("Takım/Kulüp:")
    with f2: f_region = st.selectbox("Bölge:", list(REGIONS.keys())); f_pos = st.selectbox("Mevki:", list(POS_TR.keys()))
    with f3: f_age = st.slider("Yaş:", 14, 50, (15, 25)); f_pa = st.slider("PA:", 0, 200, (140, 200))
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
            card_class = "player-card fav-active" if is_fav else "player-card"
            with cols[i % 2]:
                st.markdown(f'''
                    <div class="{card_class}">
                        <span class="pa-badge">PA: {p["pa"]}</span>
                        <h3 style="margin:0;">{p["oyuncu_adi"]}</h3>
                        <p style="color:#8b949e; margin:5px 0;">🏟️ {p["kulup"]} | 📍 {p["ulke"]} | 👟 {p["mevki"]}</p>
                        <p style="font-size:0.9rem;"><b>CA:</b> {p["ca"]} | <b>Yaş:</b> {p["yas"]} | <b>Değer:</b> {p["deger"]}</p>
                    </div>
                ''', unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"sc_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()
        
        st.markdown(f'<p style="text-align:center;">Sayfa {st.session_state.page + 1}</p>', unsafe_allow_html=True)
        cp1, cp2 = st.columns(2)
        if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if cp2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. KIYASLA (FIXED) ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Kıyaslama")
    col1, col2 = st.columns(2)
    p1_search = col1.text_input("1. Oyuncu Ara:")
    p2_search = col2.text_input("2. Oyuncu Ara:")
    
    p1_final = None
    if p1_search:
        r1 = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_search}%").limit(5).execute()
        p1_final = col1.selectbox("Eşleşen (1):", [x['oyuncu_adi'] for x in r1.data])
    
    p2_final = None
    if p2_search:
        r2 = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_search}%").limit(5).execute()
        p2_final = col2.selectbox("Eşleşen (2):", [x['oyuncu_adi'] for x in r2.data])

    if st.button("KIYASLA") and p1_final and p2_final:
        d1 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p1_final).execute()
        d2 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p2_final).execute()
        if d1.data and d2.data:
            st.table(pd.DataFrame([d1.data[0], d2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    formasyon = st.selectbox("Diziliş:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2", "4-1-2-1-2"])
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Favori Listesi Boş"]
    
    st.markdown('<div class="section-header">🛡️ DEFANS</div>', unsafe_allow_html=True)
    d_cols = st.columns(5)
    gk = d_cols[0].selectbox("GK", f_list); dl = d_cols[1].selectbox("DL", f_list); dr = d_cols[4].selectbox("DR", f_list)
    dc1 = d_cols[2].selectbox("DC1", f_list); dc2 = d_cols[3].selectbox("DC2", f_list)
    
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(4)
    mc1 = m_cols[0].selectbox("MC1", f_list); mc2 = m_cols[1].selectbox("MC2", f_list)
    aml = m_cols[2].selectbox("AML", f_list); amr = m_cols[3].selectbox("AMR", f_list)
    
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(2)
    st1 = s_cols[0].selectbox("ST 1", f_list); st2 = s_cols[1].selectbox("ST 2 / AMC", f_list)
    
    if st.button("Kadroyu Kaydet"): st.success("Kadro Başarıyla Kaydedildi!")

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Favori Listeniz")
    if st.session_state.favs:
        for f in st.session_state.favs:
            with st.container():
                c1, c2 = st.columns([5, 1])
                c1.markdown(f'''<div class="player-card fav-active" style="padding:10px; margin-bottom:5px;"><b>{f['oyuncu_adi']}</b> - {f['kulup']} | PA: {f['pa']} | CA: {f['ca']}</div>''', unsafe_allow_html=True)
                if c2.button("🗑️ Sil", key=f"del_{f['oyuncu_adi']}"):
                    st.session_state.favs = [p for p in st.session_state.favs if p['oyuncu_adi'] != f['oyuncu_adi']]
                    st.rerun()
    else: st.info("Henüz favori eklenmedi.")

# --- 5. ÖNERİLER ---
with tabs[4]:
    st.subheader("💡 Öneri & Bildirim")
    with st.form("suggestion"):
        u_type = st.selectbox("Konu:", ["Veri Hatası", "Yeni Özellik", "Hata Bildirimi"])
        u_msg = st.text_area("Mesajınız:")
        if st.form_submit_button("Gönder"):
            supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": u_type, "mesaj": u_msg}).execute()
            st.success("İletildi!")

# --- 6. ADMIN (FIXED) ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Admin")
        p_c = supabase.table("oyuncular").select("id", count="exact").execute().count
        u_c = supabase.table("users").select("id", count="exact").execute().count
        st.metric("Toplam Oyuncu", p_c); st.metric("Toplam Kullanıcı", u_c)
        
        at1, at2 = st.tabs(["✏️ Veri Düzenle", "📢 Duyuru Paneli"])
        with at1:
            e_search = st.text_input("Düzeltilecek Oyuncuyu Ara:")
            if e_search:
                e_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{e_search}%").limit(5).execute()
                e_target = st.selectbox("Düzenlenecek Oyuncu:", [x['oyuncu_adi'] for x in e_res.data])
                
                if e_target:
                    p_data = supabase.table("oyuncular").select("*").eq("oyuncu_adi", e_target).execute()
                    if p_data.data:
                        curr = p_data.data[0]
                        st.markdown(f'<div class="player-card"><b>{curr["oyuncu_adi"]}</b> - Mevcut PA: {curr["pa"]}</div>', unsafe_allow_html=True)
                        n_pa = st.number_input("Yeni PA:", value=int(curr['pa']))
                        if st.button("PA Güncelle"):
                            supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", curr['oyuncu_adi']).execute()
                            st.success("Güncellendi!")
        with at2:
            new_ann = st.text_area("Duyuru Metni:", value=st.session_state.announcements)
            if st.button("Duyuruyu Güncelle"):
                st.session_state.announcements = new_ann
                st.rerun()
    else: st.error("Admin Yetkisi Gerekli.")
