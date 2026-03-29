import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re

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
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; transition: 0.3s; }
    .fav-active { border: 2px solid #f2cc60 !important; border-left: 10px solid #f2cc60 !important; box-shadow: 0 0 15px rgba(242,204,96,0.2); }
    .pa-badge { background: #238636; color: white; padding: 4px 12px; border-radius: 8px; font-weight: bold; float: right; font-size: 1.1rem; }
    .ann-box { background: #1c2128; border: 1px solid #30363d; padding: 15px; border-radius: 10px; color: #58a6ff; text-align: center; margin-bottom: 20px; border-bottom: 3px solid #3b82f6; font-weight: bold; }
    .barrow-box { background: #000000; border: 2px solid #ef4444; border-radius: 8px; padding: 20px; margin: 15px 0; }
    .barrow-text { font-family: 'JetBrains Mono', monospace; color: #ff0000; font-size: 1.1rem; font-weight: bold; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- BARROW KÜFÜR VE ZEKA HAVUZU ---
BARROW_INSULTS = [
    "Ulan gavat, 17 yaşında adam istiyorsun, kreş mi işletiyorsun lan pezevenk? Al al hadi bunu al siktir git.",
    "Bak buraya amına koyduğumun evladı, cebinde kuruş yok hala Messi peşindesin. Al şu sümüklüyü, belki adam edersin.",
    "Senin o taktik dehana tüküreyim ben. Al şu mermiyi, kadrona bir nebze haysiyet gelsin amk.",
    "Yine mi geldin baş belası? FM'yi sil de dünya bir nefes alsın. Al şu adamı, beğenmezsen götüne sokarsın.",
    "Ulan şu oyuncuyu ben keşfettim diye demiyorum, topu ayağına aldığında statta elektrikler kesilir hıyar ağası.",
    "Cebinde akrep mi var lan? En ucuzundan en mermisini buldum sana, hadi yine iyisin orospu çocuğu.",
    "Oynattığın adamları görsem kramponun çivisiyle kovalarım seni. Al şu mermiyi koy oraya, futbol gör amk.",
    "Sana oyuncu değil, beyin nakli lazım ama veritabanında o yok. Al şu starı da vizyonun gelişsin.",
    "Bak buraya hıyarto, bu çocuk 2 seneye Real Madrid kapısında yatmazsa gel yüzüme tükür pezevenk."
]

BARROW_KNOWLEDGE = {
    "messi": ["AM R", "ST", "AM C"], "mbappe": ["ST", "AM L"], "ronaldo": ["ST", "AM L"],
    "neymar": ["AM L", "AM C"], "van dijk": ["D C"], "haaland": ["ST"], "kante": ["DM", "M C"]
}

def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V104 Yayında!"
    except: return "🔥 SOMEKU SCOUT V104 Yayında!"

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data]
    except: return []

# --- OTURUM ---
if 'user' not in st.session_state: st.session_state.user = st.query_params.get("user", None)
if st.session_state.user and 'fav_list' not in st.session_state: st.session_state.fav_list = get_user_favs(st.session_state.user)

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
    with t1:
        u_id = st.text_input("Kullanıcı Adı:", key="l_u")
        u_pw = st.text_input("Şifre:", type="password", key="l_p")
        remember = st.checkbox("Beni Hatırla", value=True)
        if st.button("Giriş"):
            res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
            if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
                st.session_state.user = u_id
                st.session_state.fav_list = get_user_favs(u_id)
                if remember: st.query_params["user"] = u_id
                st.rerun()
            else: st.error("Hatalı Giriş!")
    with t2:
        n_u = st.text_input("Yeni Kullanıcı:", key="r_u"); n_p = st.text_input("Yeni Şifre:", type="password", key="r_p")
        if st.button("Kayıt Ol"):
            try: supabase.table("users").insert({"username": n_u, "password": n_p}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Hata!")
    st.stop()

st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
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
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_f = p['oyuncu_adi'] in st.session_state.fav_list
            with cols[i%2]:
                st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}">
                <span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3>
                <p>📍 {p.get("ulke","")} | 🏟️ {p["kulup"]} | 📊 CA: {p["ca"]} | 💰 {p.get("deger", "-")}</p></div>''', unsafe_allow_html=True)
                if st.button(f"{'⭐' if is_f else '☆'}", key=f"s_{p['oyuncu_adi']}"):
                    if is_f: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()

# --- 5. BARROW AI (HARDCORE) ---
with tabs[4]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW THE TOXIC SCOUT</h1><p>Emir ver sığır, düzgün kriter yaz yoksa haşlarım.</p></div>', unsafe_allow_html=True)
    b_input = st.text_input("Örn: '17 yaşında mermi stoper', '19 yaşında genç messi', '1M euro Mbappe':", key="b_in")
    
    if st.button("BARROW'U SİKTİR ET KONUŞTUR"):
        if b_input:
            st.markdown(f'<div class="barrow-box"><p class="barrow-text">{random.choice(BARROW_INSULTS)}</p></div>', unsafe_allow_html=True)
            
            # --- ZEKA VE NUMERİK FİLTRE ---
            nums = re.findall(r'\d+', b_input)
            age_match = int(nums[0]) if nums and int(nums[0]) < 45 else None
            pa_match = int(nums[0]) if nums and 130 <= int(nums[0]) <= 200 else 150
            price_match = int(nums[0]) if nums and int(nums[0]) < 130 and ("m" in b_input.lower() or "euro" in b_input.lower()) else None

            bq = supabase.table("oyuncular").select("*")
            
            # Tam Yaş Eşleşmesi
            if age_match and "yaş" in b_input.lower(): bq = bq.eq("yas", age_match)
            else: bq = bq.lte("yas", 23)
            
            # Mevki Zekası
            t_mevki = None
            for k, v in BARROW_KNOWLEDGE.items():
                if k in b_input.lower(): t_mevki = v; break
            
            if t_mevki: bq = bq.or_(",".join([f'mevki.ilike.%{m}%' for m in t_mevki]))
            elif "stoper" in b_input.lower(): bq = bq.ilike("mevki", "%D C%")
            elif "forvet" in b_input.lower(): bq = bq.ilike("mevki", "%ST%")
            
            res_b = bq.order("pa", desc=True).limit(100).execute()
            
            if res_b.data:
                # Fiyat Temizliği
                def get_p(x):
                    d = str(x.get("deger","0")).replace("£","").replace("M","").replace(",","")
                    try: return float(re.findall(r"[-+]?\d*\.\d+|\d+", d)[0])
                    except: return 999.0
                
                f_list = [x for x in res_b.data if "Mbappé" not in x["oyuncu_adi"]]
                if price_match: f_list = [x for x in f_list if get_p(x) <= price_match]
                
                if f_list:
                    p_b = random.choice(f_list)
                    is_f = p_b['oyuncu_adi'] in st.session_state.fav_list
                    st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}" style="border-left: 10px solid #ff0000; background:#000;">
                        <span class="pa-badge" style="background:#ff0000;">BARROW ÖNERDİ SİKTİR GİT AL</span>
                        <h3 style="color:#ff0000;">{p_b["oyuncu_adi"]}</h3>
                        <p style="font-family:'JetBrains Mono'; color:#00ff41;">🏟️ {p_b["kulup"]} | 📊 PA: {p_b["pa"]} | 🎂 YAŞ: {p_b["yas"]} | 💰 {p_b.get("deger","-")}</p>
                        </div>''', unsafe_allow_html=True)
                    if st.button(f"{'⭐ Favoriden At' if is_f else '⭐ Favoriye Al Bu Mermiyi'}", key=f"b_fav_{p_b['oyuncu_adi']}"):
                        if is_f: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p_b['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p_b['oyuncu_adi'])
                        else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_b['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p_b['oyuncu_adi'])
                        st.rerun()
                else: st.warning("Barrow: 'O paraya anca babayı alırsın, bütçeni sikeyim!'")
            else: st.warning("Barrow: 'İstediğin kriterde adam yok, siktir git kendin ara!'")

# --- DİĞER TABS (DEĞİŞMEDİ) ---
with tabs[1]:
    if st.button("🎰 ÇEVİR!"):
        l = supabase.table("oyuncular").select("*").gte("pa", 150).lte("yas", 21).limit(100).execute()
        if l.data: st.session_state.roulette_player = random.choice(l.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        is_f = p['oyuncu_adi'] in st.session_state.fav_list
        st.markdown(f'<div class="player-card {"fav-active" if is_f else ""}"><h2>🌟 {p["oyuncu_adi"]}</h2><p>{p["kulup"]} | PA: {p["pa"]} | Yaş: {p["yas"]} | {p.get("deger","-")}</p></div>', unsafe_allow_html=True)
        if st.button("⭐ Favorile", key="rfav"):
            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.rerun()

with tabs[2]:
    st.subheader("📋 11 Kur")
    f_n = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    st.selectbox("GK:", f_n); st.columns(4)[0].selectbox("LB:", f_n); st.columns(3)[0].selectbox("CM:", f_n); st.columns(3)[0].selectbox("ST:", f_n)

with tabs[3]:
    st.subheader("⭐ Favoriler")
    for f in get_user_favs(st.session_state.user):
        c1, c2 = st.columns([5, 1]); c1.write(f)
        if c2.button("🗑️", key=f"d_{f}"): supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", f).execute(); st.rerun()

with tabs[5]:
    if st.session_state.user == "someku":
        st.write("🛠️ Admin Paneli"); u_l = supabase.table("users").select("*").execute()
        if u_l.data: st.table(pd.DataFrame(u_l.data))
