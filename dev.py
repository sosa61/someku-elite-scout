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
    .barrow-box { background: #000000; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin: 15px 0; }
    .barrow-text { font-family: 'JetBrains Mono', monospace; color: #ff0000; font-size: 1.1rem; font-weight: bold; }
    .tm-link { color: #58a6ff !important; text-decoration: none; border: 1px solid #58a6ff; padding: 3px 10px; border-radius: 5px; font-size: 12px; display: inline-block; margin-top: 10px; }
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .page-indicator { background: #3b82f6; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin: 10px 0; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

# --- BARROW SÖZLÜĞÜ (KÜFÜRSÜZ KABA) ---
BARROW_INSULTS = [
    "Cebinde kuruş yok hala elit oyuncu peşindesin. Al şu bütçene uygun adamı, dua et.",
    "Taktik bilgin zayıf, bari oyuncun düzgün olsun. Bak şu listeye.",
    "Yine mi geldin? İstediğin kriterlerde adam bulmak çölde iğne aramak gibi ama Barrow bulur.",
    "Bak buraya, bu çocuk bütçene göre alabileceğin en mermi adamdır. Beğenmezsen git başımdan.",
    "Sana oyuncu değil, futbol vizyonu lazım ama elimizde sadece bu var. Al ve kullan.",
    "Bütçen kısıtlı, hayallerin geniş. Al şu oyuncuyu da gerçek dünyaya dön hıyarto."
]

BARROW_KNOWLEDGE = {
    "messi": ["AM R", "ST", "AM C"], "mbappe": ["ST", "AM L"], "ronaldo": ["ST", "AM L"],
    "neymar": ["AM L", "AM C"], "van dijk": ["D C"], "haaland": ["ST"]
}

def get_announcement():
    try:
        res = supabase.table("sistem").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "🔥 SOMEKU SCOUT V109 Yayında!"
    except: return "🔥 SOMEKU SCOUT V109 Yayında!"

def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data]
    except: return []

# --- OTURUM ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'user' not in st.session_state: st.session_state.user = st.query_params.get("user", None)
if st.session_state.user and 'fav_list' not in st.session_state: st.session_state.fav_list = get_user_favs(st.session_state.user)
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- GİRİŞ ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    u_id = st.text_input("Kullanıcı Adı:"); u_pw = st.text_input("Şifre:", type="password")
    if st.button("Giriş"):
        res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
        if res.data or (u_id == "someku" and u_pw == "28616128Ok"):
            st.session_state.user = u_id
            st.query_params["user"] = u_id; st.rerun()
    st.stop()

st.markdown(f'<div class="ann-box">{get_announcement()}</div>', unsafe_allow_html=True)
tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🤖 BARROW AI", "🛠️ ADMIN"])

# --- 1. SCOUT (SAYFALAMA & FİLTRE SIFIRLAMA) ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    f1, f2, f3 = st.columns(3)
    with f1: name_f = st.text_input("👤 Oyuncu:"); team_f = st.text_input("Takım:")
    with f2: country_f = st.text_input("Uyruk:"); pos_f = st.selectbox("Mevki:", list(POS_TR.keys()))
    with f3: sort_f = st.selectbox("Sıralama:", ["pa", "ca", "yas", "deger"]); age_f = st.slider("Yaş:", 14, 50, (14, 25))
    pa_f = st.slider("PA Aralığı:", 0, 200, (140, 200))
    
    # Otomatik Sayfa Sıfırlama
    cur_f = f"{name_f}{team_f}{country_f}{pos_f}{age_f}{pa_f}{sort_f}"
    if "last_f" not in st.session_state: st.session_state.last_f = cur_f
    if st.session_state.last_f != cur_f: st.session_state.page = 0; st.session_state.last_f = cur_f

    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if country_f: query = query.ilike("ulke", f"%{country_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    st.markdown(f'<div class="page-indicator">Sayfa: {st.session_state.page + 1}</div>', unsafe_allow_html=True)
    
    if res.data:
        cols = st.columns(2)
        for i, p in enumerate(res.data):
            is_f = p['oyuncu_adi'] in st.session_state.get('fav_list', [])
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            with cols[i%2]:
                st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}">
                <span class="pa-badge">PA: {p["pa"]}</span><h3>{p["oyuncu_adi"]}</h3>
                <p>🏟️ {p["kulup"]} | 👟 {p["mevki"]} | 🎂 {p["yas"]} | 💰 {p.get("deger","-")}</p>
                <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
                if st.button(f"{'⭐' if is_f else '☆'}", key=f"sc_{p['oyuncu_adi']}"):
                    if is_f: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p['oyuncu_adi'])
                    else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p['oyuncu_adi'])
                    st.rerun()
        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri") and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️"): st.session_state.page += 1; st.rerun()

# --- 2. RULET ---
with tabs[1]:
    if st.button("🎰 ÇEVİR!"):
        l = supabase.table("oyuncular").select("*").gte("pa", 150).lte("yas", 21).limit(100).execute()
        if l.data: st.session_state.roulette_player = random.choice(l.data); st.balloons()
    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        st.markdown(f'''<div class="player-card"><h2>🌟 {p["oyuncu_adi"]}</h2><p>{p["kulup"]} | {p["mevki"]} | Yaş: {p["yas"]} | PA: {p["pa"]}</p><a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)

# --- 3. 11 KUR ---
with tabs[2]:
    st.subheader("📋 Elite 11")
    f_n = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    st.selectbox("GK:", f_n); c1, c2 = st.columns(2); c1.selectbox("CB1:", f_n); c2.selectbox("CB2:", f_n)

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Listen")
    for f in get_user_favs(st.session_state.user):
        c1, c2 = st.columns([5, 1]); c1.write(f)
        if c2.button("🗑️", key=f"del_{f}"): supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", f).execute(); st.rerun()

# --- 5. BARROW AI (HASAS FİYAT) ---
with tabs[4]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW AI</h1></div>', unsafe_allow_html=True)
    b_in = st.text_input("Emir ver (Örn: '5m stoper', '10m mbappe'):", key="b_in")
    if st.button("BARROWA SOR"):
        if b_in:
            st.markdown(f'<div class="barrow-box"><p class="barrow-text">{random.choice(BARROW_INSULTS)}</p></div>', unsafe_allow_html=True)
            # Fiyat ve Yaş Analizi
            nums = re.findall(r'\d+', b_in)
            req_p = float(nums[0]) if nums and ("m" in b_in.lower() or "euro" in b_in.lower()) else None
            
            bq = supabase.table("oyuncular").select("*").lte("yas", 23).gte("pa", 150)
            
            # Mevki Zekası
            t_m = None
            for k, v in BARROW_KNOWLEDGE.items():
                if k in b_in.lower(): t_m = v; break
            if t_m: bq = bq.or_(",".join([f'mevki.ilike.%{m}%' for m in t_m]))
            elif "stoper" in b_in.lower(): bq = bq.ilike("mevki", "%D C%")
            elif "forvet" in b_in.lower(): bq = bq.ilike("mevki", "%ST%")
            
            res_b = bq.order("pa", desc=True).limit(200).execute()
            
            if res_b.data:
                def get_v(x):
                    d = str(x.get("deger","0")).replace("£","").replace("M","").replace(",","")
                    try: return float(re.findall(r"[-+]?\d*\.\d+|\d+", d)[0])
                    except: return 999.0
                
                final_b = res_b.data
                if req_p: final_b = [x for x in res_b.data if get_v(x) <= req_p]
                
                if final_b:
                    p_b = random.choice(final_b)
                    tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p_b['oyuncu_adi'])}"
                    st.markdown(f'''<div class="player-card" style="border-left-color:#ff0000; background:#000;">
                        <h3 style="color:#ff0000;">🔥 {p_b["oyuncu_adi"]}</h3>
                        <p style="font-family:'JetBrains Mono'; color:#00ff41;">🏟️ {p_b["kulup"]} | 👟 {p_b["mevki"]} | 📊 PA: {p_b["pa"]} | 💰 {p_b.get("deger","-")}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
                    if st.button("⭐ Favorile", key=f"bf_{p_b['oyuncu_adi']}"):
                        supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_b['oyuncu_adi']}).execute(); st.rerun()
                else: st.error(f"Barrow: '{req_p}M bütçeye oyuncu yok. Bütçeni artır ya da kriteri değiştir.'")
            else: st.warning("İstediğin kriterde oyuncu bulamadım.")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        u_l = supabase.table("users").select("*").execute()
        if u_l.data: st.table(pd.DataFrame(u_l.data))
