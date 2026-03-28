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
if 'announcements' not in st.session_state: st.session_state.announcements = ["🔥 SOMEKU SCOUT V81 Yayında!"]
if 'squads' not in st.session_state: st.session_state.squads = {}
if 'page' not in st.session_state: st.session_state.page = 0

# --- TANIMLAMALAR ---
POS_TR = {"Hepsi": "Hepsi", "GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Merkez Orta Saha", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "AM C": "Ofansif Orta Saha", "ST": "Forvet"}

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .welcome-banner { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 30px; border-radius: 15px; text-align: center; border: 1px solid #3b82f6; margin-bottom: 20px; }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; transition: 0.3s; position: relative; }
    .fav-active { border: 2px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242, 204, 96, 0.4); }
    .pa-badge { background: #238636; color: white; padding: 2px 12px; border-radius: 20px; font-weight: bold; float: right; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ SİSTEMİ (HATA KORUMALI) ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Giriş Yaparak Veritabanına Erişin</p></div>', unsafe_allow_html=True)
    u_id = st.text_input("Kullanıcı ID:")
    u_pw = st.text_input("Şifre:", type="password")
    if st.button("Sisteme Giriş Yap"):
        if u_id == "someku" and u_pw == "2861628Ok":
            st.session_state.user = "someku"
            st.rerun()
        else:
            try:
                user_check = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                if user_check.data: st.session_state.user = user_check.data[0]['username']; st.rerun()
                else: st.error("Hatalı Giriş!")
            except: st.error("Sadece 'someku' girişi aktiftir.")
    st.stop()

# --- ANA PANEL ---
tabs = st.tabs(["🔍 SCOUT", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT (TAKIM EKLENDİ, FAV DÜZELTİLDİ) ---
with tabs[0]:
    with st.sidebar:
        st.header("🔎 Filtreler")
        f_name = st.text_input("Oyuncu Adı:")
        f_team = st.text_input("Takım/Kulüp:")
        f_pos = st.selectbox("Mevki:", list(POS_TR.keys()))
        f_pa = st.slider("PA:", 100, 200, (140, 200))
        st.divider()
        if st.button("Filtreyi Uygula"): st.session_state.page = 0

    query = supabase.table("oyuncular").select("*").gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_team: query = query.ilike("kulup", f"%{f_team}%")
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{f_pos}%")
    res = query.order("pa", desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()

    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            card_style = "player-card fav-active" if is_fav else "player-card"
            with cols[i % 2]:
                st.markdown(f'<div class="{card_style}"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3><p>{p["kulup"]} | {p["mevki"]}</p></div>', unsafe_allow_html=True)
                if st.button(f"⭐ {'Favoriden Çıkar' if is_fav else 'Favoriye Ekle'}", key=f"f_{p['oyuncu_adi']}_{i}"):
                    if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                    else: st.session_state.favs.append(p)
                    st.rerun()

# --- 2. KIYASLA (DÜZELTİLDİ) ---
with tabs[1]:
    st.subheader("⚖️ Oyuncu Kıyaslama")
    c1, c2 = st.columns(2)
    p1_in = c1.text_input("1. Oyuncu Ara:")
    p2_in = c2.text_input("2. Oyuncu Ara:")
    
    p1_sel = None
    if p1_in:
        r1 = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_in}%").limit(5).execute()
        p1_sel = c1.selectbox("Eşleşen (1):", [x['oyuncu_adi'] for x in r1.data])
    
    p2_sel = None
    if p2_in:
        r2 = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_in}%").limit(5).execute()
        p2_sel = c2.selectbox("Eşleşen (2):", [x['oyuncu_adi'] for x in r2.data])

    if st.button("KIYASLA") and p1_sel and p2_sel:
        d1 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p1_sel).execute()
        d2 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p2_sel).execute()
        st.table(pd.DataFrame([d1.data[0], d2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR (YENİDEN İNŞA EDİLDİ) ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    formasyon = st.selectbox("Diziliş Seçin:", ["4-3-3", "4-4-2", "3-5-2", "4-2-3-1"])
    f_names = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    
    # Mevkilere göre ayrılmış seçim
    current_squad = {}
    k_cols = st.columns(4)
    positions = ["GK", "DL", "DC1", "DC2", "DR", "MC1", "MC2", "AML", "AMR", "AMC", "ST"]
    for i, pos in enumerate(positions):
        current_squad[pos] = k_cols[i % 4].selectbox(f"{pos}:", f_names, key=f"sq_{pos}")
    
    s_col1, s_col2 = st.columns(2)
    if s_col1.button("Kadroyu Kaydet"): 
        st.session_state.squads[f"Kadro {len(st.session_state.squads)+1}"] = current_squad
        st.success("Kaydedildi!")
    if s_col2.button("Kadro Sil"): st.session_state.squads = {}; st.rerun()

# --- 4. FAVORİLER (KATEGORİ VE SİLME) ---
with tabs[3]:
    st.subheader("⭐ Favori Listen")
    if st.session_state.favs:
        for m in POS_TR.keys():
            m_players = [p for p in st.session_state.favs if p['mevki'] == m or m in p['mevki']]
            if m_players:
                st.write(f"### {POS_TR[m]}")
                for mp in m_players:
                    c_f1, c_f2 = st.columns([4, 1])
                    c_f1.write(f"{mp['oyuncu_adi']} ({mp['kulup']}) - PA: {mp['pa']}")
                    if c_f2.button("Sil", key=f"del_{mp['oyuncu_adi']}"):
                        st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != mp['oyuncu_adi']]
                        st.rerun()

# --- 5. ÖNERİLER (DETAYLANDIRILDI) ---
with tabs[4]:
    st.subheader("💡 Öneri Merkezi")
    with st.form("suggestion_v81"):
        type_o = st.selectbox("Öneri Türü:", ["Oyuncu Verisi Yanlış", "Yeni Özellik İsteği", "Tasarım Hatası", "Diğer"])
        p_name_o = st.text_input("Hangi Oyuncu? (Opsiyonel):")
        msg_o = st.text_area("Detaylı Açıklamanız:")
        if st.form_submit_button("Gönder"):
            supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": type_o, "mesaj": f"Oyuncu: {p_name_o} | {msg_o}"}).execute()
            st.success("Admin'e iletildi!")

# --- 6. ADMIN (DUYURU VE İSTATİSTİK) ---
with tabs[5]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Someku Admin")
        a_col1, a_col2 = st.columns(2)
        all_p_count = supabase.table("oyuncular").select("id", count="exact").execute()
        all_u_count = supabase.table("users").select("id", count="exact").execute()
        a_col1.metric("Toplam Oyuncu", all_p_count.count)
        a_col2.metric("Toplam Kullanıcı", all_u_count.count)
        
        adm_tabs = st.tabs(["✏️ Veri Düzenle", "📢 Duyurular", "📨 Gelen Öneriler"])
        with adm_tabs[0]:
            e_name = st.text_input("Düzenlenecek Oyuncu:")
            if e_name:
                p_data = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_name}%").limit(1).execute()
                if p_data.data:
                    new_pa = st.number_input("Yeni PA:", value=int(p_data.data[0]['pa']))
                    if st.button("PA Güncelle"):
                        supabase.table("oyuncular").update({"pa": new_pa}).eq("oyuncu_adi", p_data.data[0]['oyuncu_adi']).execute()
                        st.success("Güncellendi!")
        with adm_tabs[1]:
            new_ann = st.text_area("Yeni Duyuru Yaz:")
            if st.button("Duyuruyu Değiştir"): st.session_state.announcements = [new_ann]; st.rerun()
        with adm_tabs[2]:
            oneri_data = supabase.table("oneriler").select("*").execute()
            if oneri_data.data: st.table(pd.DataFrame(oneri_data.data))
    else: st.error("Yetki Yok.")
