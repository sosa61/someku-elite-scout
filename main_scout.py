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

# --- SESSION STATE (HESAP SİSTEMİ) ---
if 'user' not in st.session_state: st.session_state.user = None
if 'favs' not in st.session_state: st.session_state.favs = []
if 'announcements' not in st.session_state: st.session_state.announcements = ["🔥 SOMEKU SCOUT Yayında!", "💡 470.000 oyuncu arasından seçimini yap."]
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
    .pa-badge { background: #238636; color: white; padding: 2px 12px; border-radius: 20px; font-weight: bold; float: right; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- GİRİŞ / KAYIT SİSTEMİ ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Lütfen Devam Etmek İçin Giriş Yapın</p></div>', unsafe_allow_html=True)
    choice = st.radio("İşlem Seçin:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    
    u_id = st.text_input("Kullanıcı ID / Adı:")
    u_pw = st.text_input("Şifre:", type="password")
    
    if choice == "Kayıt Ol":
        if st.button("Kayıt İşlemini Tamamla"):
            supabase.table("users").insert({"username": u_id, "password": u_pw}).execute()
            st.success("Başarıyla kayıt oldunuz! Şimdi giriş yapabilirsiniz.")
    else:
        if st.button("Sisteme Giriş Yap"):
            user_check = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if user_check.data:
                st.session_state.user = user_check.data[0]['username']
                st.rerun()
            else:
                st.error("Hatalı ID veya Şifre!")
    st.stop()

# --- ANA PANEL ---
st.sidebar.write(f"👤 Hoş geldin, **{st.session_state.user}**")
if st.sidebar.button("Güvenli Çıkış"):
    st.session_state.user = None
    st.rerun()

st.markdown('<div class="welcome-banner"><h1 style="margin:0;">🕵️ SOMEKU SCOUT</h1><p style="color: #8b949e;">Elite Scouting Platform</p></div>', unsafe_allow_html=True)

tabs = st.tabs(["🔍 SCOUT", "⚖️ KIYASLA", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT SEKİMESİ ---
with tabs[0]:
    with st.sidebar:
        st.header("🔎 Filtre Paneli")
        f_name = st.text_input("Oyuncu Adı:")
        f_nation = st.text_input("Ülke:")
        f_region = st.selectbox("Kıta/Bölge:", list(REGIONS.keys()))
        f_pos = st.selectbox("Mevki (TR):", list(POS_TR.keys()))
        f_age = st.slider("Yaş Aralığı:", 14, 50, (15, 25))
        f_pa = st.slider("Potansiyel (PA):", 0, 200, (140, 200))
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        st.divider()
        search_trigger = st.button("FİLTRELEYİ UYGULA", use_container_width=True)

    limit = 12
    offset = st.session_state.page * limit
    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
    if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f"""<div class="player-card"><span class="pa-badge">PA: {p['pa']}</span><h3 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h3><div style="font-size:14px; color:#8b949e; margin: 5px 0;">📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']} <br><b>CA:</b> {p['ca']} | <b>Değer:</b> {p['deger']}</div><a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>""", unsafe_allow_html=True)
                if st.button(f"⭐ Favori", key=f"f_{p['oyuncu_adi']}_{i}"):
                    if not any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs):
                        st.session_state.favs.append(p)
                        st.toast("Favorilere Eklendi!")
        
        cp1, cp2 = st.columns(2)
        if cp1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if cp2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. KIYASLA (DÜZELTİLDİ: SEÇENEKLİ ARAMA) ---
with tabs[1]:
    st.subheader("⚖️ Akıllı Oyuncu Kıyaslama")
    col_c1, col_c2 = st.columns(2)
    
    p1_in = col_c1.text_input("1. Oyuncu Ara:")
    p1_final = None
    if p1_in:
        p1_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p1_in}%").limit(5).execute()
        p1_final = col_c1.selectbox("Eşleşen Oyuncular (1):", [x['oyuncu_adi'] for x in p1_res.data], key="c1_sel")

    p2_in = col_c2.text_input("2. Oyuncu Ara:")
    p2_final = None
    if p2_in:
        p2_res = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{p2_in}%").limit(5).execute()
        p2_final = col_c2.selectbox("Eşleşen Oyuncular (2):", [x['oyuncu_adi'] for x in p2_res.data], key="c2_sel")

    if st.button("KIYASLA"):
        if p1_final and p2_final:
            r1 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p1_final).limit(1).execute()
            r2 = supabase.table("oyuncular").select("*").eq("oyuncu_adi", p2_final).limit(1).execute()
            st.table(pd.DataFrame([r1.data[0], r2.data[0]]).set_index("oyuncu_adi"))

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Kadro Planlayıcı")
    slots = ["GK", "DL", "DC1", "DC2", "DR", "MC1", "MC2", "AML", "AMR", "AMC", "ST"]
    f_list = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Boş"]
    k_cols = st.columns(4)
    for i, s in enumerate(slots):
        k_cols[i % 4].selectbox(f"{s}:", f_list, key=f"sq_{i}")

# --- 4. ÖNERİLER ---
with tabs[4]:
    st.subheader("💡 Öneri & Geri Bildirim")
    with st.form("suggestion"):
        u_msg = st.text_area("Mesajınız:")
        if st.form_submit_button("Gönder"):
            supabase.table("oneriler").insert({"ad": st.session_state.user, "mesaj": u_msg}).execute()
            st.success("Öneriniz iletildi!")

# --- 5. ADMIN (SADECE SOMEKU 2861628Ok GİREBİLİR) ---
with tabs[5]:
    if st.session_state.user == "someku": # Senin belirttiğin özel admin hesabı
        st.subheader("🛠️ Someku Admin Paneli")
        m_tab1, m_tab2, m_tab3 = st.tabs(["📊 İstatistik", "✏️ Veri Düzenle", "📢 Duyurular"])
        
        with m_tab1:
            all_p = supabase.table("oyuncular").select("id", count="exact").execute()
            st.metric("Veritabanı Oyuncu Sayısı", all_p.count)
            users = supabase.table("users").select("*").execute()
            st.write("👥 **Kayıtlı Kullanıcılar ve Şifreleri**")
            st.table(pd.DataFrame(users.data))

        with m_tab2:
            st.write("✏️ **Oyuncu Verisi Düzelt (Akıllı Seçim)**")
            edit_search = st.text_input("Düzenlenecek Oyuncuyu Ara:")
            if edit_search:
                edit_list = supabase.table("oyuncular").select("oyuncu_adi").ilike("oyuncu_adi", f"%{edit_search}%").limit(5).execute()
                edit_target = st.selectbox("Düzenlemek için oyuncuyu seçin:", [x['oyuncu_adi'] for x in edit_list.data])
                
                if edit_target:
                    p_data = supabase.table("oyuncular").select("*").eq("oyuncu_adi", edit_target).execute()
                    curr = p_data.data[0]
                    col_e1, col_e2 = st.columns(2)
                    new_pa = col_e1.number_input("Yeni PA:", value=int(curr['pa']))
                    new_ca = col_e2.number_input("Yeni CA:", value=int(curr['ca']))
                    if st.button("VERİYİ KAYDET"):
                        supabase.table("oyuncular").update({"pa": new_pa, "ca": new_ca}).eq("oyuncu_adi", edit_target).execute()
                        st.success("Güncellendi!")

        with m_tab3:
            new_ann = st.text_input("Duyuru Yayınla:")
            if st.button("Yayınla"):
                st.session_state.announcements.insert(0, f"📣 {new_ann}")
                st.rerun()
    else:
        st.error("Bu sekme sadece Admin (someku) erişimine açıktır.")

# --- FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Favorilerin")
    if st.session_state.favs:
        st.table(pd.DataFrame(st.session_state.favs)[["oyuncu_adi", "yas", "ulke", "pa"]])
