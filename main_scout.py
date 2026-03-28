import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU MASTER SCOUT", layout="wide", page_icon="🏆")

# --- SESSION STATE (Favoriler ve Kadro İçin) ---
if 'favs' not in st.session_state: st.session_state.favs = []
if 'squad' not in st.session_state: st.session_state.squad = []

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .player-card {
        background: #161b22; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; border: 1px solid #30363d;
    }
    .pa-badge { background: #238636; color: white; padding: 2px 10px; border-radius: 10px; font-weight: bold; }
    .stat-box { background: #21262d; padding: 5px 10px; border-radius: 5px; font-size: 13px; color: #8b949e; }
    </style>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔍 GENİŞ SCOUT", "⚖️ KARŞILAŞTIR", "📋 KADROM", "⭐ FAVORİLER", "🛠️ ADMIN PANEL"])

# --- 1. GENİŞ SCOUT SEKİMESİ ---
with tabs[0]:
    st.subheader("🔎 Detaylı Oyuncu Arama")
    c1, c2, c3, c4 = st.columns(4)
    f_name = c1.text_input("Oyuncu Adı:")
    f_nation = c2.text_input("Ülke:")
    f_club = c3.text_input("Kulüp:")
    f_pos = c4.selectbox("Mevki:", ["Hepsi", "GK", "D C", "D RL", "DM", "M C", "AM C", "AM RL", "ST"])

    s1, s2, s3 = st.columns(3)
    f_age = s1.slider("Yaş Aralığı:", 14, 45, (15, 25))
    f_pa = s2.slider("Min - Max PA:", 0, 200, (140, 200))
    sort_by = s3.selectbox("Sıralama Ölçütü:", ["pa", "ca", "yas", "actual_rating"])

    if st.button("VERİLERİ GETİR"):
        query = supabase.table("oyuncular").select("*")
        query = query.gte("yas", f_age[0]).lte("yas", f_age[1])
        query = query.gte("pa", f_pa[0]).lte("pa", f_pa[1])
        
        if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
        if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
        if f_club: query = query.ilike("kulup", f"%{f_club}%")
        if f_pos != "Hepsi": query = query.ilike("mevki", f"%{f_pos}%")
        
        res = query.order(sort_by, desc=True).limit(40).execute()
        
        if res.data:
            for p in res.data:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"""
                        <div class="player-card">
                            <span class="pa-badge">PA: {p['pa']}</span>
                            <h4 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h4>
                            <div class="info-text">📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_b:
                    if st.button(f"⭐ Fav", key=f"fav_{p['oyuncu_adi']}"):
                        st.session_state.favs.append(p)
                    if st.button(f"➕ Kadro", key=f"sq_{p['oyuncu_adi']}"):
                        st.session_state.squad.append(p)
        else:
            st.warning("Sonuç bulunamadı.")

# --- 2. KARŞILAŞTIRMA SEKİMESİ ---
with tabs[1]:
    st.subheader("⚖️ İki Oyuncuyu Kıyasla")
    col1, col2 = st.columns(2)
    p1_name = col1.text_input("1. Oyuncu:")
    p2_name = col2.text_input("2. Oyuncu:")
    
    if st.button("KIYASLA"):
        res1 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p1_name}%").limit(1).execute()
        res2 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p2_name}%").limit(1).execute()
        
        if res1.data and res2.data:
            p1, p2 = res1.data[0], res2.data[0]
            compare_df = pd.DataFrame({
                "Özellik": ["Yaş", "PA", "CA", "Rating", "Mevki"],
                p1['oyuncu_adi']: [p1['yas'], p1['pa'], p1['ca'], p1['actual_rating'], p1['mevki']],
                p2['oyuncu_adi']: [p2['yas'], p2['pa'], p2['ca'], p2['actual_rating'], p2['mevki']]
            })
            st.table(compare_df)

# --- 3. KADROM SEKİMESİ ---
with tabs[2]:
    st.subheader("📋 Transfer Hedef Listem")
    if st.session_state.squad:
        st.table(pd.DataFrame(st.session_state.squad)[['oyuncu_adi', 'kulup', 'mevki', 'pa']])
        if st.button("Kadroyu Temizle"):
            st.session_state.squad = []
            st.rerun()
    else:
        st.info("Kadroya henüz oyuncu eklemedin.")

# --- 4. FAVORİLER SEKİMESİ ---
with tabs[3]:
    st.subheader("⭐ Takip Listem")
    if st.session_state.favs:
        for f in st.session_state.favs:
            st.write(f"✅ **{f['oyuncu_adi']}** - {f['kulup']} ({f['pa']} PA)")
    else:
        st.info("Henüz favori oyuncun yok.")

# --- 5. DETAYLI ADMIN PANELİ ---
with tabs[4]:
    st.subheader("🛠️ Veritabanı Yönetimi")
    col_adm1, col_adm2 = st.columns(2)
    
    with col_adm1:
        st.write("📊 **Veri İstatistikleri**")
        total_count = supabase.table("oyuncular").select("*", count="exact").limit(1).execute()
        st.metric("Toplam Kayıtlı Oyuncu", "469.694") # Statik veya exact count ile
        st.write("Veritabanı Durumu: **Aktif / Sağlıklı**")
    
    with col_adm2:
        st.write("⚙️ **Hızlı İşlemler**")
        new_name = st.text_input("Yeni Oyuncu Adı:")
        new_pa = st.number_input("PA Değeri:", 0, 200, 150)
        if st.button("Hızlı Oyuncu Ekle"):
            supabase.table("oyuncular").insert({"oyuncu_adi": new_name, "pa": new_pa}).execute()
            st.success("Oyuncu veritabanına eklendi!")
