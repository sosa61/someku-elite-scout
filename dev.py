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
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #0d1117; color: white; }
    .loader-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh; }
    .magnifier { font-size: 80px; animation: bounce 2s infinite ease-in-out; }
    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; transition: 0.3s; }
    .fav-active { border: 2px solid #f2cc60 !important; border-left: 10px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; font-weight: bold; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .barrow-box { background: #000000; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 15px 0; border-left: 5px solid #ef4444; position: relative; }
    .barrow-text { font-family: 'JetBrains Mono', monospace; color: #00ff41; font-size: 1.05rem; line-height: 1.5; }
    .barrow-name { color: #ef4444; font-weight: bold; margin-bottom: 10px; display: block; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 2px; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    .page-indicator { background: #3b82f6; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin: 10px 0; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

# --- BARROW BEYİN VE SÖZLÜK ---
BARROW_KNOWLEDGE = {
    "messi": ["AM R", "ST", "AM C"],
    "mbappe": ["ST", "AM L"],
    "ronaldo": ["ST", "AM L"],
    "neymar": ["AM L", "AM C"],
    "de bruyne": ["M C", "AM C"],
    "van dijk": ["D C"],
    "haaland": ["ST"],
    "modric": ["M C"],
    "kante": ["DM", "M C"]
}

BARROW_QUOTES = [
    "Lan hıyarto, cebinde 3 kuruş para var hala Mbappe peşinde koşuyorsun. Al sana şunu, hadi yine iyisin...",
    "Ulan senin taktik anlayışınla mahalle maçına bile gidilmez ama neyse, al şu topçuyu da biraz kalite gör.",
    "Bana bak evlat, o mevkide senin oynattığın adamı görsem kramponumla kovalarım. Al şu mermiyi koy oraya.",
    "2 milyona stoper arıyorsun, pazarda domates mi alıyorsun lan hıyar? Al şu çocuğu, 2 sene sonra elini öperler.",
    "Yine mi sen? FM'yi sil de bir nefes alalım amk. Al şu listeyi, git kadronu düzelt.",
    "Bak buraya, bu çocuk topu ayağına aldığında statta elektrikler kesilir. Senin vizyonun yetmez ama al bi dene.",
    "Şu oyuncuyu ben buldum diye demiyorum, 19 yaşında ama sahadaki 35 yaşındaki abilerine ders verir.",
    "Cebinde akrep mi var? Ucuz diye çöp toplama, al şu gerçek yeteneği gör."
]

def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V102 Yayında!"
    except: return "🔥 SOMEKU SCOUT V102 Yayında!"

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data]
    except: return []

# --- OTURUM ---
if 'user' not in st.session_state: st.session_state.user = st.query_params.get("user", None)
if st.session_state.user and 'fav_list' not in st.session_state: st.session_state.fav_list = get_user_favs(st.session_state.user)
if 'lottie_shown' not in st.session_state:
    st.markdown('<div class="loader-container"><div class="magnifier">🕵️‍♂️</div><h2 style="color: #58a6ff;">Elite Veritabanı Hazırlanıyor...</h2></div>', unsafe_allow_html=True)
    time.sleep(1.2); st.session_state.lottie_shown = True; st.rerun()

if 'page' not in st.session_state: st.session_state.page = 0
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        u_id = st.text_input("Kullanıcı Adı:", key="l_u")
        u_pw = st.text_input("Şifre:", type="password", key="l_p")
        remember = st.checkbox("Beni Hatırla", value=True)
        if st.button("Giriş", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
                st.session_state.user = u_id
                st.session_state.fav_list = get_user_favs(u_id); 
                if remember: st.query_params["user"] = u_id
                st.rerun()
            else: st.error("Hatalı Giriş!")
    with t2:
        n_u = st.text_input("Yeni Kullanıcı:", key="r_u"); n_p = st.text_input("Yeni Şifre:", type="password", key="r_p")
        if st.button("Kayıt Ol", use_container_width=True):
            try: supabase.table("users").insert({"username": n_u, "password": n_p}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Hata!")
    st.stop()

# --- ÜST ---
st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
with st.sidebar:
    st.write(f"👤 **{st.session_state.user}**")
    if st.button("🚪 Çıkış"): st.session_state.user = None; st.query_params.clear(); st.session_state.clear(); st.rerun()

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🤖 BARROW AI", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan", "Slovenya", "Bosna Hersek"], "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador"], "Afrika": ["Nijerya", "Senegal", "Mısır", "Fildişi Sahili", "Fas", "Cezayir"], "Asya": ["Japonya", "Güney Kore", "Suudi Arabistan", "Katar", "Avustralya", "Çin"]}
    f1, f2, f3 = st.columns(3)
    with f1: name_f = st.text_input("👤 Oyuncu Ara:"); team_f = st.text_input("🏟️ Takım Ara:")
    with f2: reg_f = st.selectbox("🌍 Bölge:", list(REG_TR.keys())); country_f = st.text_input("🏳️ Uyruk Ara:")
    with f3: pos_f = st.selectbox("👟 Mevki:", list(POS_TR.keys())); sort_f = st.selectbox("🔃 Sıralama:", ["pa", "ca", "yas", "deger"])
    v1, v2 = st.columns(2)
    with v1: age_f = st.slider("🎂 Yaş:", 14, 50, (14, 25))
    with v2: pa_f = st.slider("📊 PA Aralığı:", 0, 200, (140, 200))
    current_filter = f"{name_f}-{team_f}-{reg_f}-{country_f}-{pos_f}-{age_f}-{pa_f}-{sort_f}"
    if "last_filter" not in st.session_state: st.session_state.last_filter = current_filter
    if st.session_state.last_filter != current_filter: st.session_state.page = 0; st.session_state.last_filter = current_filter
    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if country_f: query = query.ilike("ulke", f"%{country_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REG_TR[reg_f])
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    st.markdown(f'<div class="page-indicator">Sayfa: {st.session_state.page + 1}</div>', unsafe_allow_html=True)
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.get('fav_list', [])
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i % 2]:
                st.markdown(f'''<div class="player-card {"fav-active" if is_fav else ""}">
                    <span class="pa-badge">PA: {p["pa"]}</span><h3 style="margin:0;">{p["oyuncu_adi"]}</h3>
                    <p style="color:#8b949e; font-size:0.9rem; margin:5px 0;">📍 {p.get("ulke","")} | 🏟️ {p["kulup"]} | 👟 {p["mevki"]}</p>
                    <p style="font-size:0.95rem;">📊 CA: {p["ca"]} | 🎂 Yaş: {p["yas"]} | 💰 Değer: {p.get("deger", "-")}</p>
                    <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
                ck1, ck2 = st.columns([3, 1]); ck1.code(p['oyuncu_adi'])
                if ck2.button(f"{'⭐' if is_fav else '☆'}", key=f"btn_{p['oyuncu_adi']}"):
                    if is_fav: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET ---
with tabs[1]:
    if st.button("🎰 ÇEVİR!", use_container_width=True):
        lucky_res = supabase.table("oyuncular").select("*").gte("pa", 150).lte("yas", 21).limit(100).execute()
        if lucky_res.data: st.session_state.roulette_player = random.choice(lucky_res.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_fav = p['oyuncu_adi'] in st.session_state.get('fav_list', [])
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        st.markdown(f'''<div class="player-card {"fav-active" if is_fav else ""}">
            <span class="pa-badge">PA: {p["pa"]}</span><h2 style="margin:0;">🌟 {p["oyuncu_adi"]}</h2>
            <p style="color:#8b949e;">📍 {p.get("ulke","")} | 🏟️ {p["kulup"]} | 👟 {p["mevki"]}</p>
            <p>📊 CA: {p["ca"]} | 🎂 Yaş: {p["yas"]} | 💰 Değer: {p.get("deger", "-")}</p>
            <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
        if st.button(f"{'⭐ Favoriden Çıkar' if is_fav else '⭐ Favorilere Ekle'}", key="roul_fav"):
            if is_fav: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p['oyuncu_adi'])
            else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p['oyuncu_adi'])
            st.rerun()

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Taktik Tahtası")
    f_names = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    st.markdown('<div class="section-header">🧤 KALECİ</div>', unsafe_allow_html=True); gk = st.selectbox("GK:", f_names, key="k_gk")
    st.markdown('<div class="section-header">🛡️ DEFANS</div>', unsafe_allow_html=True)
    d_cols = st.columns(4); d1 = d_cols[0].selectbox("LB:", f_names); d2 = d_cols[1].selectbox("CB1:", f_names); d3 = d_cols[2].selectbox("CB2:", f_names); d4 = d_cols[3].selectbox("RB:", f_names)
    st.markdown('<div class="section-header">⚙️ ORTA SAHA</div>', unsafe_allow_html=True)
    m_cols = st.columns(3); m1 = m_cols[0].selectbox("LM/LW:", f_names); m2 = m_cols[1].selectbox("CM/DM:", f_names); m3 = m_cols[2].selectbox("RM/RW:", f_names)
    st.markdown('<div class="section-header">🎯 FORVET</div>', unsafe_allow_html=True)
    s_cols = st.columns(3); s1 = s_cols[0].selectbox("ST1:", f_names); s2 = s_cols[1].selectbox("ST2:", f_names); s3 = s_cols[2].selectbox("ST3:", f_names)
    if st.button("Kadro Savaşçılarını Kaydet"): st.success("Elite 11 Hazır!")

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Kalıcı Favorilerin")
    db_favs = get_user_favs(st.session_state.user)
    if db_favs:
        for f_name in db_favs:
            c1, c2 = st.columns([5, 1]); c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f_name}</b></div>', unsafe_allow_html=True)
            if c2.button("🗑️", key=f"del_{f_name}"): supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", f_name).execute(); st.session_state.fav_list.remove(f_name); st.rerun()

# --- 5. BARROW AI ---
with tabs[4]:
    st.markdown('<div style="text-align:center; padding: 20px;"><h1 style="color:#ef4444; margin:0;">🤵 BARROW AI</h1><p style="color:#9ca3af;">Zeki, huysuz ve tam bir futbol hıyarı.</p></div>', unsafe_allow_html=True)
    chat_input = st.text_input("Barrow'a emir ver (Örn: 'Genç Messi', 'Sert Stoper', 'Ucuz Mbappe'):", key="barrow_chat")
    if st.button("Barrow'u Uyandır"):
        if chat_input:
            st.markdown(f'<div class="barrow-box"><span class="barrow-name">Barrow Mesajı</span><p class="barrow-text">{random.choice(BARROW_QUOTES)}</p></div>', unsafe_allow_html=True)
            b_query = supabase.table("oyuncular").select("*").lte("yas", 22).gte("pa", 150)
            
            # Zeki Mevki Sorgulama
            target_mevki = None
            for key, mevkiler in BARROW_KNOWLEDGE.items():
                if key in chat_input.lower(): target_mevki = mevkiler; break
            
            if target_mevki:
                # Efsane ismine göre mevki eşlemesi
                b_query = supabase.table("oyuncular").select("*").lte("yas", 22).gte("pa", 155)
                or_query = ",".join([f'mevki.ilike.%{m}%' for m in target_mevki])
                res_b = b_query.or_(or_query).execute()
            elif "stoper" in chat_input.lower() or "defans" in chat_input.lower():
                res_b = b_query.ilike("mevki", "%D C%").execute()
            elif "forvet" in chat_input.lower():
                res_b = b_query.ilike("mevki", "%ST%").execute()
            else:
                res_b = b_query.limit(50).execute()
            
            if res_b.data:
                clean_list = [x for x in res_b.data if x["pa"] < 195] # Çok bilindik isimleri bazen elemek için
                p_b = random.choice(clean_list if clean_list else res_b.data)
                tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p_b['oyuncu_adi'])}"
                st.markdown(f'''<div class="player-card fav-active" style="border-left: 10px solid #ef4444; background: #000;">
                    <span class="pa-badge" style="background:#ef4444;">BARROW ANALİZİ</span>
                    <h3 style="color:#ef4444;">🔥 {p_b["oyuncu_adi"]}</h3>
                    <p style="font-family: 'JetBrains Mono'; color:#00ff41;">🏟️ {p_b["kulup"]} | 📊 PA: {p_b["pa"]} | 🎂 YAŞ: {p_b["yas"]} | 👟 {p_b["mevki"]}</p>
                    <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
            else: st.warning("Barrow: 'O kadar iyi adam yok piyasada, git kendin bul hıyar!'")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        adm1, adm2, adm3 = st.tabs(["✏️ Veri", "📢 Duyuru", "👥 Üyeler"])
        with adm1:
            e_s = st.text_input("Oyuncu Ara:"); e_r = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{e_s}%").limit(5).execute()
            if e_r.data:
                target = st.selectbox("Seç:", [x['oyuncu_adi'] for x in e_r.data]); n_pa = st.number_input("Yeni PA:", value=180)
                if st.button("Güncelle"): supabase.table("oyuncular").update({"pa": n_pa}).eq("oyuncu_adi", target).execute(); st.success("Güncellendi!")
        with adm2:
            n_msg = st.text_area("Yeni Duyuru:", value=get_announcement())
            if st.button("Duyuruyu Yayınla"): supabase.table("sistem").update({"duyuru": n_msg}).eq("id", 1).execute(); st.rerun()
        with adm3:
            u_l = supabase.table("users").select("*").execute()
            if u_l.data: st.table(pd.DataFrame(u_l.data))
    else: st.error("Admin Yetkisi Yok.")
