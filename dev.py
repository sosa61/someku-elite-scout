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
    .section-header { background: #21262d; padding: 10px; border-radius: 8px; margin: 20px 0 10px 0; border-left: 5px solid #58a6ff; font-weight: bold; }
    .page-indicator { background: #3b82f6; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; margin: 10px 0; display: inline-block; }
    </style>
""", unsafe_allow_html=True)

# --- BARROW ZEKA ---
BARROW_INSULTS = ["Cebinde kuruş yok hala elit oyuncu peşindesin. Al şunu dua et.", "Taktik bilgin zayıf, bari oyuncun düzgün olsun.", "Yine mi geldin? Barrow senin için mermiyi buldu.", "Bak buraya hıyarto, bütçene göre en mermisi budur."]
BARROW_KNOWLEDGE = {
    "messi": ["AM R", "ST", "AM C"], "mbappe": ["ST", "AM L"], "ronaldo": ["ST", "AM L"], "van dijk": ["D C"],
    "kaleci": ["GK"], "stoper": ["D C"], "sol bek": ["D L"], "sağ bek": ["D R"], "bek": ["D L", "D R"],
    "orta saha": ["M C", "DM", "AM C"], "forvet": ["ST"], "golcü": ["ST"], "kanat": ["AM L", "AM R"]
}

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

tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🤖 BARROW AI", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan", "Slovenya", "Bosna Hersek"], "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador"], "Afrika": ["Nijerya", "Senegal", "Mısır", "Fildişi Sahili", "Fas", "Cezayir"], "Asya": ["Japonya", "Güney Kore", "Suudi Arabistan", "Katar", "Avustralya", "Çin"]}
    f1, f2, f3 = st.columns(3)
    with f1: name_f = st.text_input("👤 Oyuncu:"); team_f = st.text_input("Takım Ara:")
    with f2: reg_f = st.selectbox("🌍 Bölge:", list(REG_TR.keys())); country_f = st.text_input("Uyruk:")
    with f3: pos_f = st.selectbox("👟 Mevki:", list(POS_TR.keys())); sort_f = st.selectbox("🔃 Sıralama:", ["pa", "ca", "yas", "deger"])
    v1, v2 = st.columns(2)
    with v1: age_f = st.slider("🎂 Yaş:", 14, 50, (14, 25))
    with v2: pa_f = st.slider("📊 PA:", 0, 200, (140, 200))
    
    cur_f = f"{name_f}{team_f}{reg_f}{country_f}{pos_f}{age_f}{pa_f}{sort_f}"
    if "last_f" not in st.session_state: st.session_state.last_f = cur_f
    if st.session_state.last_f != cur_f: st.session_state.page = 0; st.session_state.last_f = cur_f

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
        is_f = p['oyuncu_adi'] in st.session_state.get('fav_list', [])
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}">
            <span class="pa-badge">PA: {p["pa"]}</span><h2>🌟 {p["oyuncu_adi"]}</h2>
            <p>{p["kulup"]} | {p["mevki"]} | Yaş: {p["yas"]} | 💰 {p.get("deger","-")}</p>
            <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
        if st.button(f"{'⭐ Favoriden Çıkar' if is_f else '⭐ Favorilere Ekle'}", key="roul_fav_v114"):
            if is_f: supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute(); st.session_state.fav_list.remove(p['oyuncu_adi'])
            else: supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute(); st.session_state.fav_list.append(p['oyuncu_adi'])
            st.rerun()

# --- 3. 11 KUR ---
with tabs[2]:
    f_n = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    k1, k2, k3, k4, k5 = st.columns(5)
    gk = k1.selectbox("GK:", f_n, key="gk_v"); lb = k2.selectbox("LB:", f_n, key="lb_v"); cb1 = k3.selectbox("CB1:", f_n, key="cb1_v"); cb2 = k4.selectbox("CB2:", f_n, key="cb2_v"); rb = k5.selectbox("RB:", f_n, key="rb_v")
    m1, m2, m3 = st.columns(3); dm = m1.selectbox("DM:", f_n, key="dm_v"); cm = m2.selectbox("CM:", f_n, key="cm_v"); amc = m3.selectbox("AMC:", f_n, key="amc_v")
    s1, s2, s3 = st.columns(3); lw = s1.selectbox("LW:", f_n, key="lw_v"); rw = s2.selectbox("RW:", f_n, key="rw_v"); stp = s3.selectbox("ST:", f_n, key="stp_v")

# --- 4. FAVORİLER ---
with tabs[3]:
    st.subheader("⭐ Kalıcı Favorilerin")
    for f in get_user_favs(st.session_state.user):
        c1, c2 = st.columns([5, 1]); c1.markdown(f'<div class="player-card fav-active" style="padding:10px;"><b>{f}</b></div>', unsafe_allow_html=True)
        if c2.button("🗑️", key=f"del_{f}"): supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", f).execute(); st.rerun()
            
# --- 5. BARROW AI (GÜNCEL FİYAT VE MEVKİ FİLTRESİ) ---
with tabs[4]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW AI</h1></div>', unsafe_allow_html=True)
    b_in = st.text_input("Barrow'a emir ver (Örn: '3m defans', '17 yaş forvet'):", key="b_in_v116")
    
    if st.button("BARROWA SOR"):
        if b_in:
            st.markdown(f'<div class="barrow-box"><p class="barrow-text">{random.choice(BARROW_INSULTS)}</p></div>', unsafe_allow_html=True)
            
            # Yazıdan tüm sayıları ayıkla
            nums = re.findall(r'\d+', b_in)
            req_p = float(nums[0]) if nums and ("m" in b_in.lower() or "euro" in b_in.lower() or "para" in b_in.lower()) else None
            
            # PA 135+ olan tüm geniş havuzu çekiyoruz (Hep aynı adam gelmesin diye)
            bq = supabase.table("oyuncular").select("*").gte("pa", 135)
            
            # --- GELİŞMİŞ MEVKİ ZEKA ANALİZİ ---
            t_m_list = []
            # Kullanıcının yazdığı cümlede anahtar kelime ara
            low_in = b_in.lower()
            if "defans" in low_in or "stoper" in low_in or "bek" in low_in:
                t_m_list.extend(["D C", "D L", "D R"])
            elif "forvet" in low_in or "golcü" in low_in or "santrafor" in low_in:
                t_m_list.append("ST")
            elif "orta saha" in low_in or "merkez" in low_in:
                t_m_list.extend(["M C", "DM", "AM C"])
            elif "kanat" in low_in:
                t_m_list.extend(["AM L", "AM R"])
            elif "kaleci" in low_in:
                t_m_list.append("GK")

            # Eğer yukarıdaki kelimeler yoksa BARROW_KNOWLEDGE sözlüğüne bak
            for k, v in BARROW_KNOWLEDGE.items():
                if k in low_in:
                    t_m_list.extend(v)
            
            if t_m_list:
                or_filters = ",".join([f'mevki.ilike.%{m}%' for m in set(t_m_list)])
                bq = bq.or_(or_filters)
            
            res_b = bq.order("pa", desc=True).limit(600).execute()
            
            if res_b.data:
                # Kesin Fiyat Temizleme (Para birimi ne olursa olsun sadece rakamı alır)
                def get_clean_value(x):
                    val_str = str(x.get("deger", "0")).replace(",", ".")
                    val_nums = re.findall(r"[-+]?\d*\.\d+|\d+", val_str)
                    if val_nums:
                        # Eğer değer 'K' (bin) ise 0.5M gibi düşün, 'M' (milyon) ise direkt al
                        raw_val = float(val_nums[0])
                        if "K" in val_str.upper(): return raw_val / 1000
                        return raw_val
                    return 9999.0
                
                # Bütçeye göre filtrele
                final_b = res_b.data
                if req_p is not None:
                    final_b = [x for x in res_b.data if get_clean_value(x) <= req_p]
                
                if final_b:
                    p_b = random.choice(final_b)
                    is_f = p_b['oyuncu_adi'] in st.session_state.get('fav_list', [])
                    tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p_b['oyuncu_adi'])}"
                    
                    st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}" style="border-left-color:#ff0000; background:#000;">
                        <h3 style="color:#ff0000;">🔥 {p_b["oyuncu_adi"]}</h3>
                        <p style="font-family:'JetBrains Mono'; color:#00ff41;">🏟️ {p_b["kulup"]} | 👟 {p_b["mevki"]} | 📊 PA: {p_b["pa"]} | 🎂 YAŞ: {p_b["yas"]} | 💰 {p_b.get("deger","-")}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
                    
                    if st.button(f"{'⭐ Listeden At' if is_f else '⭐ Listeye Al'}", key=f"bf_v116_{p_b['oyuncu_adi']}"):
                        if is_f:
                            supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p_b['oyuncu_adi']).execute()
                            st.session_state.fav_list.remove(p_b['oyuncu_adi'])
                        else:
                            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_b['oyuncu_adi']}).execute()
                            st.session_state.fav_list.append(p_b['oyuncu_adi'])
                        st.rerun()
                else:
                    st.error(f"Barrow: '{req_p}M bütçeye defans mı olur hıyar? Git pazar gez belki bulursun. (Veya bütçeni artır!)'")
            else:
                st.warning("Barrow: 'O kriterlerde mermi gibi birini bulamadım.'")

# --- 6. ADMIN ---
with tabs[5]:
    if st.session_state.user == "someku":
        u_l = supabase.table("users").select("*").execute()
        if u_l.data: st.table(pd.DataFrame(u_l.data))
