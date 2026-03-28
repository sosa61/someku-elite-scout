import streamlit as st
from supabase import create_client, Client
import urllib.parse

# --- SUPABASE AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide", page_icon="⚽")

# --- GELİŞMİŞ TASARIM (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .stApp { background-color: #0b0e14; }
    .player-card {
        background: #161b22;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #30363d;
        transition: transform 0.3s;
    }
    .player-card:hover { transform: scale(1.01); border-color: #58a6ff; }
    .pa-gold { border-left: 6px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242, 204, 96, 0.2); }
    .pa-silver { border-left: 6px solid #8b949e !important; }
    .pa-badge {
        background: #238636; color: white; padding: 4px 12px;
        border-radius: 20px; font-weight: bold; float: right;
    }
    .info-text { color: #8b949e; font-size: 14px; margin-top: 5px; }
    .tm-link {
        color: #58a6ff !important; text-decoration: none; font-weight: bold;
        display: inline-block; margin-top: 10px; border: 1px solid #58a6ff;
        padding: 5px 15px; border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ SOMEKU ELITE SCOUT")
st.markdown("---")

# --- FİLTRELEME ALANI ---
with st.sidebar:
    st.header("🔍 Scout Filtreleri")
    f_name = st.text_input("Oyuncu İsmi:")
    f_club = st.text_input("Kulüp Ara:")
    f_pos = st.selectbox("Mevki Seç:", ["Hepsi", "GK", "D C", "D RL", "DM", "M C", "AM C", "AM RL", "ST"])
    f_pa = st.slider("Min. Potansiyel (PA):", 0, 200, 150)
    st.info(f"Toplam 470.000 oyuncu taranıyor.")

# --- VERİ ÇEKME ---
query = supabase.table("oyuncular").select("*").gte("pa", f_pa)

if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
if f_club: query = query.ilike("kulup", f"%{f_club}%")
if f_pos != "Hepsi": query = query.ilike("mevki", f"%{f_pos}%")

res = query.order("pa", desc=True).limit(30).execute()

# --- SONUÇLARI GÖSTER ---
if res.data:
    for p in res.data:
        # PA değerine göre çerçeve rengi
        card_class = "pa-gold" if p['pa'] >= 165 else "pa-silver"
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        
        st.markdown(f"""
            <div class="player-card {card_class}">
                <span class="pa-badge">PA: {p['pa']}</span>
                <h2 style="margin:0; color:white;">{p['oyuncu_adi']} <span style="font-size:16px; color:#8b949e;">({p['yas']})</span></h2>
                <div class="info-text">
                    📍 {p['ulke']} | 🏟️ {p['kulup']} | 👟 {p['mevki']}
                </div>
                <div class="info-text" style="color:#238636;">
                    <b>Güncel Yetenek (CA):</b> {p['ca']} | <b>Tahmini Değer:</b> {p['deger']}
                </div>
                <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt Profili ➔</a>
            </div>
        """, unsafe_allow_html=True)
else:
    st.warning("Aradığınız kriterlere uygun oyuncu bulunamadı.")
