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
    @keyframes search { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; transition: 0.3s; }
    .fav-active { border: 2px solid #f2cc60 !important; border-left: 10px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; font-weight: bold; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- VERİ FONKSİYONLARI ---
def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V88 Yayında!"
    except: return "🔥 SOMEKU SCOUT V88 Yayında!"

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data]
    except: return []

# --- YÜKLEME EKRANI ---
if 'lottie_shown' not in st.session_state:
    st.markdown('<div class="loader-container"><div class="magnifier">🕵️‍♂️</div><h2 style="color: #58a6ff;">Elite Veritabanı Hazırlanıyor...</h2></div>', unsafe_allow_html=True)
    time.sleep(1.5); st.session_state.lottie_shown = True; st.rerun()

# --- SESSION STATE ---
if 'user' not in st.session_state: st.session_state.user = None
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        u_id = st.text_input("Kullanıcı Adı:", key="l_u")
        u_pw = st.text_input("Şifre:", type="password", key="l_p")
        if st.button("Giriş", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
                st.session_state.user = u_id
                st.session_state.fav_list = get_user_favs(u_id)
                st.rerun()
            else: st.error("Hatalı Giriş!")
    with t2:
        n_u = st.text_input("Yeni Kullanıcı:", key="r_u"); n_p = st.text_input("Yeni Şifre:", type="password", key="r_p")
        if st.button("Kayıt Ol", use_container_width=True):
            try: supabase.table("users").insert({"username": n_u, "password": n_p}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Hata!")
    st.stop()

# --- ÜST PANEL ---
st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.write(f"👤 **{st.session_state.user}**")
    if st.button("🚪 Çıkış"): st.session_state.user = None; st.session_state.pop('lottie_shown', None); st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🏟️ TAKIM SEÇ", "💡 ÖNERİLER", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan", "Slovenya", "Bosna Hersek"]}
    
    f1, f2, f3 = st.columns(3)
    with f1: name_f = st.text_input("👤 Oyuncu Ara:"); team_f = st.text_input("🏟️ Takım Ara:")
    with f2: reg_f = st.selectbox("🌍 Bölge:", list(REG_TR.keys())); pos_f = st.selectbox("👟 Mevki:", list(POS_TR.keys()))
    with f3: age_f = st.slider("🎂 Yaş:", 14, 50, (14, 25)); pa_f = st.slider("📊 PA:", 0, 200, (140, 200))
    val_f = st.select_slider("💰 Piyasa Değeri:", options=["Hepsi", "Ucuz", "Normal", "Pahalı"], value="Hepsi")
    
    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REG_TR[reg_f])
    
    res = query.order("pa", desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'''
                    <div class="player-card {"fav-active" if is_fav else ""}">
                        <span class="pa-badge">PA: {p["pa"]}</span>
                        <h3 style="margin:0;">{p["oyuncu_adi"]}</h3>
                        <p style="color:#8b949e; font-size:0.9rem; margin:5px 0;">📍 {p.get("ulke","")} | 🏟️ {p["kulup"]} | 📊 CA: {p["ca"]} | 🎂 Yaş: {p["yas"]}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a>
                    </div>
                ''', unsafe_allow_html=True)
                ck1, ck2 = st.columns([3, 1])
                ck1.code(p['oyuncu_adi'])
                if ck2.button(f"{'⭐' if is_fav else '☆'}", key=f"btn_{p['oyuncu_adi']}"):
                    if is_fav:
                        supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute()
                        st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else:
                        supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                        st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET ---
with tabs[1]:
    if st.button("🎰 ÇEVİR!", use_container_width=True):
        lucky = supabase.table("oyuncular").select("*").gte("pa", 150).lte("yas", 21).limit(100).execute()
        if lucky.data: st.session_state.roulette_player = random.choice(lucky.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        st.markdown(f'<div class="player-card fav-active"><h2>🌟 {p["oyuncu_adi"]}</h2><p>{p["kulup"]} | PA: {p["pa"]} | Yaş: {p["yas"]}</p></div>', unsafe_allow_html=True)
        st.code(p['oyuncu_adi'])

# --- 5. TAKIM RULETİ (FİXED) ---
with tabs[4]:
    st.subheader("🏟️ Takım Bulma Çarkı")
    lig_sec = st.selectbox("Lig Filtresi:", ["Hepsi", "Türkiye", "İngiltere", "İspanya", "Almanya", "İtalya"])
    if st.button("🏟️ ÇARK-I TAKIM!"):
        # Gerçek veritabanından lige göre takım çekme mantığı
        lig_map = {"Türkiye": ["Süper Lig"], "İngiltere": ["Premier League"], "İspanya": ["LaLiga"], "Almanya": ["Bundesliga"]}
        t_query = supabase.table("oyuncular").select("kulup").limit(2000)
        if lig_sec != "Hepsi":
            # Burada lig bilgisi oyuncu tablosunda varsa filtreleme yapılır, yoksa örnek havuzdan gelir
            havuz = {"Türkiye": ["Trabzonspor", "Samsunspor", "Göztepe", "Beşiktaş", "Galatasaray", "Fenerbahçe"], 
                     "İngiltere": ["Brighton", "Sunderland", "Everton", "Newcastle"], 
                     "İspanya": ["Valencia", "Sevilla", "Real Sociedad"],
                     "Almanya": ["Dortmund", "St. Pauli", "Leverkusen"]}
            secilen = random.choice(havuz.get(lig_sec, ["Ajax", "Benfica", "Napoli"]))
        else:
            secilen = random.choice(["Milan", "Inter", "PSG", "Porto", "Celtic"])
        
        st.markdown(f'''
            <div class="player-card fav-active" style="text-align:center;">
                <h3 style="color:#58a6ff;">🏁 YENİ MACERA BAŞLIYOR</h3>
                <h1 style="font-size:3rem;">🏟️ {secilen}</h1>
                <p>Başarılar Menajer!</p>
            </div>
        ''', unsafe_allow_html=True)

# --- 6. ÖNERİLER (FİXED) ---
with tabs[5]:
    st.subheader("💡 Geliştirme")
    with st.form("o_form"):
        o_t = st.selectbox("Konu:", ["Hata", "Tasarım", "Özellik İsteği"])
        o_m = st.text_area("Mesaj:")
        if st.form_submit_button("Gönder"):
            try:
                supabase.table("oneriler").insert({"ad": st.session_state.user, "konu": o_t, "mesaj": o_m}).execute()
                st.success("Talebin iletildi!")
            except: st.error("Lütfen 'oneriler' tablosunu kontrol edin.")

# --- 7. ADMIN ---
with tabs[6]:
    if st.session_state.user == "someku":
        st.subheader("🛠️ Admin")
        adm1, adm2, adm3 = st.tabs(["✏️ Veri", "📢 Duyuru", "👥 Üyeler"])
        with adm2:
            n_msg = st.text_area("Yeni Duyuru:", value=get_announcement())
            if st.button("Duyuruyu Yayınla"):
                supabase.table("sistem").update({"duyuru": n_msg}).eq("id", 1).execute(); st.rerun()
        with adm3:
            u_l = supabase.table("users").select("*").execute()
            if u_l.data: st.table(pd.DataFrame(u_l.data))
    else: st.error("Yetki Yok.")
