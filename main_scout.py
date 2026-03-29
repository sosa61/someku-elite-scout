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

# --- TASARIM (CSS) ---
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
    time.sleep(1.5)
    st.session_state.lottie_shown = True
    st.rerun()

# --- VERİTABANI YARDIMCI FONKSİYONLARI ---
def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT Yayında!"
    except: return "Duyuru yüklenemedi."

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("username", username).execute()
        return [item['oyuncu_adi'] for item in res.data]
    except: return []

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'favs' not in st.session_state: st.session_state.favs = []
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ / KAYIT SİSTEMİ ---
if st.session_state.user is None:
    st.markdown('<div class="welcome-banner"><h1>🕵️ SOMEKU SCOUT</h1><p>Giriş Yapın veya Kayıt Olun</p></div>', unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab_login:
        u_id = st.text_input("Kullanıcı Adı:", key="login_user")
        u_pw = st.text_input("Şifre:", type="password", key="login_pw")
        if st.button("Giriş Yap", use_container_width=True):
            if u_id == "someku" and u_pw == "28616128Ok":
                st.session_state.user = "someku"
                st.session_state.favs = get_user_favs("someku")
                st.rerun()
            else:
                res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                if res.data:
                    st.session_state.user = res.data[0]['username']
                    st.session_state.favs = get_user_favs(u_id)
                    st.rerun()
                else: st.error("Hatalı Giriş!")

    with tab_register:
        r_id = st.text_input("Yeni Kullanıcı Adı:", key="reg_user")
        r_pw = st.text_input("Yeni Şifre:", type="password", key="reg_pw")
        if st.button("Hesap Oluştur", use_container_width=True):
            try:
                supabase.table("users").insert({"username": r_id, "password": r_pw}).execute()
                st.success("Kayıt başarılı! Şimdi giriş yapabilirsiniz.")
            except: st.error("Bu kullanıcı adı alınmış olabilir.")
    st.stop()

# --- PANEL VE ÇIKIŞ ---
st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.title("👤 Profil")
    st.write(f"Üye: **{st.session_state.user}**")
    if st.button("🚪 Çıkış Yap"):
        st.session_state.user = None
        st.session_state.pop('lottie_shown', None)
        st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    f1, f2, f3, f4 = st.columns(4)
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    with f1: f_name = st.text_input("Oyuncu/Takım:"); f_team = st.text_input("Lig/Kulüp:")
    with f2: f_pos = st.selectbox("Mevki Seçin:", list(POS_TR.keys()))
    with f3: f_age = st.slider("Yaş:", 14, 50, (14, 25)); f_pa = st.slider("PA:", 0, 200, (140, 200))
    with f4: 
        sort_by = st.selectbox("Sıralama:", ["pa", "ca", "yas"])
        if st.button("🔍 UYGULA", use_container_width=True): st.session_state.page = 0

    query = supabase.table("oyuncular").select("*").gte("yas", f_age[0]).lte("yas", f_age[1]).gte("pa", f_pa[0]).lte("pa", f_pa[1])
    if f_name: query = query.ilike("oyuncu_adi", f"%{f_name}%")
    if f_team: query = query.ilike("kulup", f"%{f_team}%")
    if f_pos != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[f_pos]}%")
    
    res = query.order(sort_by, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.favs
            with cols[i % 2]:
                st.markdown(f'<div class="player-card {"fav-active" if is_fav else ""}"><span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3><p>🏟️ {p["kulup"]} | 👟 {p["mevki"]}<br><b>CA:</b> {p["ca"]}</p></div>', unsafe_allow_html=True)
                if st.button(f"{'⭐ Çıkar' if is_fav else '⭐ Ekle'}", key=f"s_{p['oyuncu_adi']}_{i}"):
                    if is_fav:
                        supabase.table("favoriler").delete().eq("username", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute()
                        st.session_state.favs.remove(p['oyuncu_adi'])
                    else:
                        supabase.table("favoriler").insert({"username": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                        st.session_state.favs.append(p['oyuncu_adi'])
                    st.rerun()
        
        c_p1, c_p2 = st.columns(2)
        if c_p1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c_p2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 4. FAVORİLER (KALICI LİSTE) ---
with tabs[3]:
    st.subheader("⭐ Kalıcı Favori Listen")
    current_fav_names = get_user_favs(st.session_state.user)
    if current_fav_names:
        for f_name in current_fav_names:
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f_name}</b></div>', unsafe_allow_html=True)
            if c2.button("🗑️ SİL", key=f"del_{f_name}"):
                supabase.table("favoriler").delete().eq("username", st.session_state.user).eq("oyuncu_adi", f_name).execute()
                st.session_state.favs.remove(f_name)
                st.rerun()
    else: st.info("Favori listeniz boş.")

# --- 6. ADMIN (KALICI DUYURU) ---
with tabs[5]:
    if st.session_state.user == "someku":
        adm1, adm2 = st.tabs(["✏️ Veri Düzenle", "📢 Kalıcı Duyuru"])
        with adm2:
            new_ann = st.text_area("Duyuru Metni:", value=get_announcement())
            if st.button("Veritabanına Kaydet ve Yayınla"):
                supabase.table("sistem").update({"duyuru": new_ann}).eq("id", 1).execute()
                st.success("Duyuru veritabanına kaydedildi!")
                st.rerun()
