import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU MASTER SCOUT", layout="wide", page_icon="🏆")

# --- SESSION STATE YÖNETİMİ ---
if 'favs' not in st.session_state: st.session_state.favs = []
if 'squad' not in st.session_state: st.session_state.squad = []
if 'page' not in st.session_state: st.session_state.page = 0

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .player-card {
        background: #161b22; border-radius: 12px; padding: 15px;
        margin-bottom: 10px; border: 1px solid #30363d;
    }
    .pa-badge { background: #238636; color: white; padding: 2px 10px; border-radius: 10px; font-weight: bold; float: right; }
    .page-info { color: #58a6ff; font-weight: bold; text-align: center; margin: 10px; }
    </style>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔍 GENİŞ SCOUT", "⚖️ KARŞILAŞTIR", "📋 KADROM", "⭐ FAVORİLER", "🛠️ ADMIN PANEL"])

# --- 1. GENİŞ SCOUT (SAYFALAMA EKLENDİ) ---
with tabs[0]:
    st.subheader("🔎 Detaylı Oyuncu Arama")
    
    # Filtreler
    c1, c2, c3, c4 = st.columns(4)
    f_name = c1.text_input("Oyuncu Adı:")
    f_nation = c2.text_input("Ülke:")
    f_club = c3.text_input("Kulüp:")
    f_pos = c4.selectbox("Mevki:", ["Hepsi", "GK", "D C", "D RL", "DM", "M C", "AM C", "AM RL", "ST"])

    s1, s2, s3 = st.columns(3)
    f_age = s1.slider("Yaş Aralığı:", 14, 45, (15, 30))
    f_pa = s2.slider("Min - Max PA:", 0, 200, (140, 200))
    sort_by = s3.selectbox("Sıralama Ölçütü:", ["pa", "ca", "yas", "actual_rating"])

    # Sayfalama Ayarları
    limit = 20
    offset = st.session_state.page * limit

    # Veri Sorgusu
    query = supabase.table("oyuncular").select("*")
    query = query.gte("yas", f_age[0]).lte("yas", f_age[1])
    query = query.gte("pa", f_pa[0]).lte("pa", f_pa[1])
    
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_nation: query = query.ilike("ulke", f"%{f_nation}%")
    if f_club: query = query.ilike("kulup", f"%{f_club}%")
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{f_pos}%")
    
    res = query.order(sort_by, desc=True).range(offset, offset + limit - 1).execute()

    # Sayfa Navigasyonu
    col_prev, col_page, col_next = st.columns([1, 2, 1])
    if col_prev.button("⬅️ Önceki Sayfa") and st.session_state.page > 0:
        st.session_state.page -= 1
        st.rerun()
    
    col_page.markdown(f'<div class="page-info">Sayfa: {st.session_state.page + 1}</div>', unsafe_allow_html=True)
    
    if col_next.button("Sonraki Sayfa ➡️"):
        st.session_state.page += 1
        st.rerun()

    # Oyuncu Listeleme
    if res.data:
        for p in res.data:
            col_card, col_btns = st.columns([5, 1])
            with col_card:
                st.markdown(f"""
                    <div class="player-card">
                        <span class="pa-badge">PA: {p['pa']}</span>
                        <h4 style="margin:0;">{p['oyuncu_adi']} ({p['yas']})</h4>
                        <small style="color:#8b949e;">{p['ulke']} | {p['kulup']} | {p['mevki']}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col_btns:
                if st.button("⭐", key=f"fav_{p['oyuncu_adi']}_{offset}"):
                    st.session_state.favs.append(p)
                if st.button("➕", key=f"sq_{p['oyuncu_adi']}_{offset}"):
                    st.session_state.squad.append(p)
    else:
        st.warning("Bu sayfada gösterilecek oyuncu kalmadı veya arama sonucu bulunamadı.")

# --- DİĞER SEKİMELERE DOKUNMADIK (KODUN DEVAMI AYNIDIR) ---
with tabs[1]: # Karşılaştırma
    st.subheader("⚖️ İki Oyuncuyu Kıyasla")
    cp1, cp2 = st.columns(2)
    p1_search = cp1.text_input("1. Oyuncu İsmi:")
    p2_search = cp2.text_input("2. Oyuncu İsmi:")
    if st.button("KARŞILAŞTIR"):
        r1 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p1_search}%").limit(1).execute()
        r2 = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{p2_search}%").limit(1).execute()
        if r1.data and r2.data:
            st.table(pd.DataFrame([r1.data[0], r2.data[0]]))

with tabs[2]: # Kadro
    st.subheader("📋 Transfer Hedef Listem")
    if st.session_state.squad:
        st.dataframe(pd.DataFrame(st.session_state.squad))
        if st.button("Listeyi Boşalt"):
            st.session_state.squad = []
            st.rerun()

with tabs[3]: # Favoriler
    st.subheader("⭐ Favori Oyuncularım")
    if st.session_state.favs:
        for f in st.session_state.favs:
            st.write(f"- {f['oyuncu_adi']} ({f['kulup']})")

with tabs[4]: # Admin
    st.subheader("🛠️ Admin Paneli")
    st.metric("Sistemdeki Toplam Oyuncu", "469.694")
    if st.button("Sayfa Sayacını Sıfırla"):
        st.session_state.page = 0
        st.rerun()
