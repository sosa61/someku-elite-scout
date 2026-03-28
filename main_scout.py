import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU CLUB MANAGER", layout="wide", page_icon="🏟️")

# --- SESSION STATE (VERİ SAKLAMA) ---
if 'favs' not in st.session_state: st.session_state.favs = []
if 'squads' not in st.session_state: st.session_state.squads = {}
if 'announcements' not in st.session_state: st.session_state.announcements = ["Hoş geldiniz! Veritabanı 470.000 oyuncuya güncellendi."]
if 'suggestions' not in st.session_state: st.session_state.suggestions = []
if 'page' not in st.session_state: st.session_state.page = 0

# --- BÖLGESEL VE MEVKİ TANIMLARI ---
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
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 15px; margin-bottom: 10px; }
    .fav-active { border: 2px solid #f2cc60 !important; box-shadow: 0 0 10px rgba(242, 204, 96, 0.3); }
    .pa-badge { background: #238636; color: white; padding: 2px 12px; border-radius: 20px; font-weight: bold; float: right; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; }
    .announcement-box { background: #1c2128; border-left: 5px solid #58a6ff; padding: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- ANA SAYFA DUYURULARI ---
with st.expander("📢 Son Duyurular", expanded=True):
    for a in st.session_state.announcements:
        st.markdown(f'<div class="announcement-box">{a}</div>', unsafe_allow_html=True)

tabs = st.tabs(["🔍 SCOUT", "⚖️ KARŞILAŞTIR", "📋 KADRO PLANLAMA", "⭐ FAVORİLER", "💡 ÖNERİ/YENİLİK", "🛠️ ADMIN"])

# --- 1. GENİŞ SCOUT ---
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    f_name = c1.text_input("Oyuncu Adı (Harf Duyarsız):")
    f_nation = c2.text_input("Ülke (İspanya, ispanya vb.):")
    f_region = c3.selectbox("Kıtasal/Bölgesel Filtre:", list(REGIONS.keys()))

    s1, s2, s3, s4 = st.columns(4)
    f_pos = s1.selectbox("Mevki (TR):", list(POS_TR.keys()))
    f_age = s2.slider("Yaş Aralığı:", 14, 50, (15, 25))
    f_pa = s3.slider("Potansiyel (PA):", 0, 200, (140, 200))
    sort_by = s4.selectbox("Sıralama:", ["pa", "ca", "yas"])

    limit = 12
    offset = st.session_state.page * limit

    # Supabase Query
    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
    if f_region != "Hepsi": query = query.in_("ulke", REGIONS[f_region])
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    
    res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

    # Sayfa Kontrolü
    st.markdown(f'<p style="text-align:center; color:#58a6ff;"><b>Şu an {st.session_state.page + 1}. sayfadasınız</b></p>', unsafe_allow_html=True)
    cp1, cp2 = st.columns(2)
    if cp1.button("⬅️ Önceki Sayfa") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
    if cp2.button("Sonraki Sayfa ➡️"): st.session_state.page += 1; st.rerun()

    if res.data:
        for p in res.data:
            is_fav = any(f['oyuncu_adi'] == p['oyuncu_adi'] for f in st.session_state.favs)
            card_class = "player-card fav-active" if is_fav else "player-card"
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            
            st.markdown(f"""
                <div class="{card_class}">
                    <span class="pa-badge">PA: {p['pa']}</span>
                    <h3 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h3>
                    <div style="font-size:14px; color:#8b949e; margin: 5px 0;">
                        📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']} <br>
                        <b>Mevcut Yetenek (CA):</b> {p['ca']} | <b>Bonservis:</b> {p['deger']}
                    </div>
                    <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt Profili ➔</a>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"{'⭐ Favorilerden Çıkar' if is_fav else '⭐ Favoriye Ekle'}", key=f"f_{p['oyuncu_adi']}_{offset}"):
                if is_fav: st.session_state.favs = [f for f in st.session_state.favs if f['oyuncu_adi'] != p['oyuncu_adi']]
                else: st.session_state.favs.append(p)
                st.rerun()

# --- 2. KARŞILAŞTIRMA ---
with tabs[1]:
    st.subheader("⚖️ Oyuncu Karşılaştırma Merkezi")
    col1, col2 = st.columns(2)
    p1_s = col1.text_input("1. Oyuncu İsmi (Tam yazınız):")
    p2_s = col2.text_input("2. Oyuncu İsmi (Tam yazınız):")
    if st.button("VERİLERİ KIYASLA"):
        r1 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p1_s}%").limit(1).execute()
        r2 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p2_s}%").limit(1).execute()
        if r1.data and r2.data:
            st.table(pd.DataFrame([r1.data[0], r2.data[0]]).set_index("oyuncu_adi"))
        else: st.error("Oyuncular bulunamadı.")

# --- 3. KADRO PLANLAMA (11 KİŞİLİK) ---
with tabs[2]:
    st.subheader("📋 11 Kişilik Taktik Planlama")
    dizilis = st.selectbox("Diziliş Seç:", ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "5-3-2", "3-4-3"])
    k_isim = st.text_input("Kadronun Adı:", "Altın Kadrom")
    
    st.info("💡 Not: Oyuncuları önce Favorilere (⭐) ekle, sonra buradan kadrona yerleştir.")
    fav_names = [f['oyuncu_adi'] for f in st.session_state.favs] if st.session_state.favs else ["Favori Yok"]
    
    slots = ["Kaleci", "Sol Bek", "Stoper 1", "Stoper 2", "Sağ Bek", "Orta Saha 1", "Orta Saha 2", "Orta Saha 3", "Sol Kanat", "Sağ Kanat", "Forvet"]
    yeni_kadro = {}
    cols = st.columns(4)
    for i, s in enumerate(slots):
        yeni_kadro[s] = cols[i % 4].selectbox(f"{s}:", fav_names, key=f"slot_{i}")

    if st.button("KADROYU SİSTEME KAYDET"):
        st.session_state.squads[k_isim] = {"dizilis": dizilis, "oyuncular": yeni_kadro}
        st.success(f"{k_isim} başarıyla kaydedildi!")

    if st.session_state.squads:
        st.divider()
        for ad, veri in st.session_state.squads.items():
            with st.expander(f"📂 {ad} ({veri['dizilis']})"):
                st.write(veri['oyuncular'])
                if st.button(f"{ad} Kadrosunu Sil", key=f"del_sq_{ad}"):
                    del st.session_state.squads[ad]; st.rerun()

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Takip Altındaki Oyuncular")
    if st.session_state.favs:
        for f in st.session_state.favs:
            col_f1, col_f2 = st.columns([5,1])
            col_f1.success(f"**{f['oyuncu_adi']}** | {f['kulup']} | PA: {f['pa']}")
            if col_f2.button("Listeden Sil", key=f"del_fav_{f['oyuncu_adi']}"):
                st.session_state.favs.remove(f); st.rerun()
    else: st.info("Henüz favori oyuncu eklenmedi.")

# --- 5. ÖNERİ VE YENİLİK ---
with tabs[4]:
    st.subheader("💡 Siteyi Geliştirelim")
    o_tip = st.selectbox("Öneri Tipi:", ["Yeni Özellik", "Hata Bildirimi", "Oyuncu Verisi Hatası", "Tasarım Önerisi"])
    o_mesaj = st.text_area("Mesajın:")
    if st.button("Admin'e İlet"):
        st.session_state.suggestions.append({"tip": o_tip, "mesaj": o_mesaj})
        st.success("Teşekkürler! Önerin Admin paneline düştü.")

# --- 6. ADMIN PANELİ ---
with tabs[5]:
    st.subheader("🛠️ Master Admin Paneli")
    c_a1, c_a2 = st.columns(2)
    with c_a1:
        st.write("📢 **Yeni Duyuru Yayınla**")
        d_text = st.text_input("Duyuru Metni:")
        if st.button("Yayınla"):
            st.session_state.announcements.insert(0, d_text)
            st.rerun()
        if st.button("Tüm Duyuruları Temizle"):
            st.session_state.announcements = []; st.rerun()

    with c_a2:
        st.write("👥 **Kullanıcı Veritabanı**")
        users_df = pd.DataFrame([
            {"Kullanıcı": "Ramazan", "Şifre": "rmzn123", "Yetki": "Admin"},
            {"Kullanıcı": "Scout_Omer", "Şifre": "omerfm24", "Yetki": "Editör"}
        ])
        st.table(users_df)
    
    st.divider()
    st.write("📥 **Gelen Öneriler & Yenilikler**")
    if st.session_state.suggestions:
        st.write(pd.DataFrame(st.session_state.suggestions))
    else: st.info("Henüz bir öneri gelmedi.")
