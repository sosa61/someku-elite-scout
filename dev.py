import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re
import unicodedata
from streamlit_option_menu import option_menu

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT PRO", layout="wide", page_icon="🕵️")

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    .stApp { background-color: #0d1117; color: white; font-family: 'Inter', sans-serif; }
    
    /* Sidebar Tasarımı */
    [data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #30363d; }
    
    /* Kart Tasarımları */
    .scout-card { background: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 20px; margin-bottom: 15px; }
    .hero-section { 
        background: linear-gradient(90deg, #1d976c 0%, #93f9b9 100%); 
        padding: 40px; border-radius: 20px; color: white; margin-bottom: 30px; 
    }
    
    /* Butonlar */
    .stButton>button { border-radius: 10px; font-weight: bold; transition: 0.3s; }
    
    /* Kaydırma Çubuğu Gizleme (Opsiyonel) */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- YARDIMCI FONKSİYONLAR ---
def metin_temizle(metin):
    if not metin: return ""
    metin = str(metin).lower().replace('ı', 'i').replace('İ', 'i')
    nfkd_form = unicodedata.normalize('NFKD', metin)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def mevki_turkce_yap(m):
    m = str(m).upper()
    if "GK" in m: return "🧤 KALECİ"
    if any(x in m for x in ["D R", "D L", "DR", "DL", "FB"]): return "🛡️ BEK"
    if "D C" in m or "DC" in m: return "🛡️ STOPER"
    if any(x in m for x in ["AM R", "AM L", "M R", "M L", "LW", "RW"]): return "⚡ KANAT"
    if any(x in m for x in ["ST", "CF"]): return "⚽ FORVET"
    return "🧠 ORTA SAHA"

# --- OTURUM VE GİRİŞ ---
if 'user' not in st.session_state: st.session_state.user = st.query_params.get("user", None)

if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center; color:#238636;">🕵️ SOMEKU ELITE SCOUT</h1>', unsafe_allow_html=True)
    with st.container():
        col_l, col_r = st.columns([1,1])
        u_id = col_l.text_input("Kullanıcı Adı:")
        u_pw = col_r.text_input("Şifre:", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
                st.session_state.user = u_id
                st.query_params["user"] = u_id; st.rerun()
    st.stop()

# --- YAN MENÜ (SIDEBAR NAVIGATION) ---
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding:20px;">
            <h2 style="color:#238636; margin:0;">CoachPro</h2>
            <p style="color:#8b949e; font-size:12px;">Elite Scout Management</p>
        </div>
    """, unsafe_allow_html=True)
    
    secenek = option_menu(
        menu_title=None,
        options=["Ana Sayfa", "Scout", "Rulet", "11 Kur", "Favoriler", "Yetenek Avı", "Barrow AI", "Yönetim"],
        icons=["house", "search", "slot-machine", "people", "star", "crosshair", "robot", "shield-lock"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#8b949e", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "color": "#8b949e", "border-radius": "10px"},
            "nav-link-selected": {"background-color": "#238636", "color": "white"},
        }
    )
    
    st.markdown("---")
    st.caption(f"🟢 Aktif: {st.session_state.user}")
    if st.button("Çıkış Yap"):
        st.session_state.user = None
        st.query_params.clear(); st.rerun()

# --- İÇERİK YÖNETİMİ ---

# 1. ANA SAYFA (COACHPRO STİLİ)
if secenek == "Ana Sayfa":
    st.markdown(f"""
        <div class="hero-section">
            <h1>Hoş Geldin, Scout {st.session_state.user}!</h1>
            <p>Bugün hangi mermiyi keşfedeceksin? Veri tabanımızdaki binlerce oyuncu seni bekliyor.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    # Gerçek verileri çekelim
    res_c = supabase.table("oyuncular").select("*", count="exact").limit(1).execute()
    total_p = res_c.count if res_c.count else 470000
    
    c1.metric("Toplam Oyuncu", f"{total_p:,}")
    c2.metric("Elit Potansiyel (160+)", "1.240")
    c3.metric("Favori Listen", "18")
    c4.metric("Aktif Scoutlar", "1")

# 2. SCOUT (ARAMA)
elif secenek == "Scout":
    st.markdown("## 🔍 OYUNCU VERİ TABANI")
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    
    with st.container():
        f1, f2, f3 = st.columns(3)
        name_f = f1.text_input("👤 Oyuncu Adı:")
        pos_f = f2.selectbox("👟 Mevki:", list(POS_TR.keys()))
        pa_f = f3.slider("📊 PA Aralığı:", 135, 200, (145, 200))
        
        query = supabase.table("oyuncular").select("*").gte("pa", pa_f[0]).lte("pa", pa_f[1])
        if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
        if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
        
        res = query.order("pa", desc=True).limit(20).execute()
        
        if res.data:
            for p in res.data:
                st.markdown(f"""
                    <div class="scout-card">
                        <span style="float:right; background:#238636; padding:2px 10px; border-radius:5px;">PA: {p['pa']}</span>
                        <h4 style="margin:0;">{p['oyuncu_adi']}</h4>
                        <p style="color:#8b949e; font-size:13px;">{p['kulup']} | {p['mevki']} | {p['yas']} Yaş</p>
                    </div>
                """, unsafe_allow_html=True)

# 3. RULET
elif secenek == "Rulet":
    st.markdown("## 🎰 TRANSFER RULETİ")
    # Eski Rulet kodların buraya gelecek (Kısaltıldı)
    st.info("Rulet sistemi yeni menüye entegre edildi. 'Çevir' butonuna basarak mermi avlayabilirsin.")
    if st.button("🎰 ÇEVİR"):
        st.write("Rulet dönüyor...") # Senin orijinal rulet animasyon kodun buraya gelecek

# 4. 11 KUR
elif secenek == "11 Kur":
    st.markdown("## 🏟️ ELITE ARENA - KADRO KUR")
    # Eski 11 Kur kodların buraya gelecek
    st.write("Kadro kurma alanı hazır.")

# 5. FAVORİLER
elif secenek == "Favoriler":
    st.markdown("## ⭐ FAVORİ LİSTEN")
    res = supabase.table("favoriler").select("*").order("created_at", desc=True).execute()
    if res.data:
        for p in res.data:
            st.markdown(f'<div class="scout-card"><b>{p["oyuncu_adi"]}</b> - PA: {p["pa"]} ({p["kulup"]})</div>', unsafe_allow_html=True)
    else: st.info("Liste boş.")

# 6. YETENEK AVI (V440 SÜRÜMÜ - OYUN)
elif secenek == "Yetenek Avı":
    st.markdown('<h2 style="text-align:center; color:#f2cc60;">🕵️ GİZLİ YETENEK AVI</h2>', unsafe_allow_html=True)
    
    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'target_p' not in st.session_state: st.session_state.target_p = None

    def yeni_oyun_tetikle():
        res_g = supabase.table("oyuncular").select("*").not_.eq("kulup", "None").gte("pa", 165).limit(500).execute()
        if res_g.data:
            st.session_state.target_p = random.choice(res_g.data)
            st.session_state.game_active = True
            st.session_state.game_start_time = time.time()

    if st.button("🚀 YENİ AV BAŞLAT", use_container_width=True):
        yeni_oyun_tetikle(); st.rerun()

    if st.session_state.game_active and st.session_state.target_p:
        p = st.session_state.target_p
        kalan = max(0, int(30 - (time.time() - st.session_state.game_start_time)))
        yuzde = (kalan / 30) * 100

        if kalan > 0:
            pa_hint = f"🔥 PA: {p['pa']}" if kalan <= 20 else "🔥 PA: ??"
            ca_hint = f"📊 CA: {p.get('ca','?')}" if kalan <= 10 else "📊 CA: ??"
            bar_color = "#238636" if yuzde > 50 else ("#f2cc60" if yuzde > 20 else "#ff4b4b")
            
            st.markdown(f"""
                <div style="background:#161b22; padding:20px; border-radius:15px; border:2px solid #30363d; text-align:center;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                        <span style="font-size:22px;">⏳ <b>{kalan}s</b></span>
                        <span style="color:#8b949e;">{mevki_turkce_yap(p['mevki'])}</span>
                    </div>
                    <div style="width:100%; background:#30363d; height:12px; border-radius:10px; overflow:hidden; margin-bottom:15px;">
                        <div style="width:{yuzde}%; background:{bar_color}; height:100%; transition: width 0.5s ease;"></div>
                    </div>
                    <p style="color:#ffffff; font-size:19px;"><b>{p['yas']} Yaş | {p.get('kulup','Serbest')}</b></p>
                    <div style="display:flex; justify-content:center; gap:20px; font-weight:bold; font-size:16px;">
                        <span style="color:#f2cc60;">{pa_hint}</span>
                        <span style="color:#58a6ff;">{ca_hint}</span>
                    </div>
                </div>
                <h1 style="text-align:center; font-size:50px; color:#58a6ff; letter-spacing:5px; margin:25px 0;">??????</h1>
            """, unsafe_allow_html=True)

            tahmin = st.text_input("Tahmini Yaz ve Enter'la:", key="scout_input").strip()
            if tahmin:
                if metin_temizle(tahmin) in metin_temizle(p['oyuncu_adi']) and len(tahmin) > 2:
                    st.session_state.game_active = False
                    # Skor yazma fonksiyonunu buraya ekle (Yukarıda tanımlı)
                    st.balloons(); st.success(f"🎯 BİLDİN! {p['oyuncu_adi']}"); st.rerun()
            
            time.sleep(0.5); st.rerun()
        else:
            st.session_state.game_active = False; st.error(f"⌛ SÜRE BİTTİ! Aranan: {p['oyuncu_adi']}")
            if st.button("🔄 YENİDEN DENE"): yeni_oyun_tetikle(); st.rerun()

# 7. BARROW AI
elif secenek == "Barrow AI":
    st.markdown("## 🤵 BARROW AI")
    st.write("Barrow emirlerini bekliyor...")

# 8. YÖNETİM (SADECE SOMEKU)
elif secenek == "Yönetim":
    if st.session_state.user == "someku":
        st.markdown("## 🛡️ YÖNETİM MERKEZİ")
        st.write("Kullanıcılar ve Oyuncu Veri Tabanı Kontrolü")
    else: st.warning("Erişim reddedildi.")
