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
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; transition: 0.3s; border-left: 5px solid #3b82f6; }
    .fav-active { border-left: 5px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; font-weight: 500; text-align: center; margin-bottom: 20px; }
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
    if col_b2.button("Kayıt Ol", use_container_width=True):
        try:
            supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
            st.success("Kayıt Başarılı!")
        except: st.error("Hata!")
    st.stop()

# --- ÜST PANEL & ÇIKIŞ ---
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
    f1, f2, f3 = st.columns([2, 1, 1])
    with f1: f_name = st.text_input("🔍 Oyuncu veya Takım Ara:")
    with f2: f_pos = st.selectbox("👟 Mevki:", list(POS_TR.keys()))
    with f3: f_pa = st.slider("📊 Minimum PA:", 0, 200, 140)
    
    query = supabase.table("oyuncular").select("*").gte("pa", f_pa)
    if f_name: query = query.or_(f"oyuncu_adi.ilike.%{f_name}%,kulup.ilike.%{f_name}%")
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{f_pos}%")
    
    res = query.order("pa", desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
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
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"btn_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()
        
        c_p1, c_p2 = st.columns(2)
        if c_p1.button("⬅️ Geri"): st.session_state.page -= 1; st.rerun()
        if c_p2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. KIYASLA ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Kıyaslama")
    col1, col2 = st.columns(2)
    p1_in = col1.text_input("1. Oyuncu:")
    p2_in = col2.text_input("2. Oyuncu:")
    if st.button("Verileri Getir"):
        r1 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p1_in}%").limit(1).execute()
        r2 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p2_in}%").limit(1).execute()
        if r1.data and r2.data:
            st.table(pd.DataFrame([r1.data[0], r2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR (BOLCA DİZİLİŞ) ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    formasyon = st.selectbox("Formasyon Seçin:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1", "5-3-2", "4-1-2-1-2"])
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Favori Listesi Boş"]
    
    st.markdown('<div class="section-header">🛡️ DEFANS HATTI</div>', unsafe_allow_html=True)
    d_cols = st.columns(5)
    gk = d_cols[0].selectbox("GK", f_list); dl = d_cols[1].selectbox("DL", f_list); dr = d_cols[4].selectbox("DR", f_list)
    dc1 = d_cols[2].selectbox("DC1", f_list); dc2 = d_cols[3].selectbox("DC2", f_list)
    
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(4)
    mc1 = m_cols[0].selectbox("MC1", f_list); mc2 = m_cols[1].selectbox("MC2", f_list)
    aml = m_cols[2].selectbox("Kanat/AML", f_list); amr = m_cols[3].selectbox("Kanat/AMR", f_list)
    
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(2)
    st1 = s_cols[0].selectbox("Forvet 1", f_list); st2 = s_cols[1].selectbox("Forvet 2 / AMC", f_list)
    
    if st.button("Kadroyu Kaydet"): st.success(f"{formasyon} düzenindeki kadronuz kaydedildi!")

# --- 4. FAVORİLER (FIXED) ---
with tabs[3]:
    st.subheader("⭐ Favori Oyuncularınız")
    if st.session_state.favs:
        for f in st.session_state.favs:
            with st.container():
                c1, c2 = st.columns([5, 1])
                c1.markdown(f"**{f['oyuncu_adi']}** ({f['kulup']}) - PA: {f['pa']}")
                if c2.button("🗑️ Sil", key=f"del_{f['oyuncu_adi']}"):
                    st.session_state.favs = [p for p in st.session_state.favs if p['oyuncu_adi'] != f['oyuncu_adi']]
                    st.rerun()
    else:
        st.info("Henüz favori eklenmedi. Scout sekmesinden yıldızları seçin!")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Admin Paneli")
        t1, t2 = st.tabs(["✏️ Veri Düzenle", "📢 Duyuru Ayarları"])
        with t1:
            e_name = st.text_input("Oyuncu Ara:")
            if e_name:
                e_res = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_name}%").limit(1).execute()
                if e_res.data:
                    curr = e_res.data[0]
                    st.info(f"Düzenlenen: {curr['oyuncu_adi']} ({curr['kulup']})")
                    n_pa = st.number_input("Yeni PA:", value=int(curr['pa']))
                    if st.button("Güncelle"):
                        supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", curr['oyuncu_adi']).execute()
                        st.success("PA Güncellendi!")
        with t2:
            new_msg = st.text_area("Yeni Duyuru Metni:", value=st.session_state.announcements)
            if st.button("Duyuruyu Yayınla"):
                st.session_state.announcements = new_msg
                st.rerun()
