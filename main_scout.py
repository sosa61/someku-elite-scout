import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import datetime
import os
import subprocess
import threading  # İşte eksik olan mermi bu!
import unicodedata





# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- 🔄 GÜÇLENDİRİLMİŞ VIP TAZELEME MOTORU (V183) ---
if "user" in st.session_state and st.session_state.get('user'):
    try:
        # Veritabanından durumu çekiyoruz
        v_res = supabase.table("users").select("is_vip").eq("username", st.session_state.user).execute()
        
        if v_res.data and len(v_res.data) > 0:
            # VIP bilgisini boolean (True/False) olarak zorla işle
            st.session_state['is_vip'] = bool(v_res.data[0].get('is_vip', False))
    except Exception as e:
        # Hata olursa sistemi kilitleme, sessizce devam et
        pass


# BURADAN SONRA TASARIM CSS KODLARIN DEVAM ETSİN


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

# --- OTURUM AYARLARI (EN ÜSTTE OLMALI) ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'user' not in st.session_state: st.session_state.user = None # Hata almamak için bunu ekle
if 'is_vip' not in st.session_state: st.session_state.is_vip = False # VIP durumunu sıfırla
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# Query Params'tan kullanıcıyı almayı deniyoruz (Sayfa yenilenince giriş kalsın diye)
query_user = st.query_params.get("user", None)
if query_user and st.session_state.user is None:
    st.session_state.user = query_user


# --- GİRİŞ VE KAYIT BÖLÜMÜ ---
if st.session_state.user is None:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    u_id = st.text_input("Kullanıcı Adı:")
    u_pw = st.text_input("Şifre:", type="password")
    
    if st.button("Giriş"):
        res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
        
        if res.data:
            user_data = res.data[0]
            st.session_state.user = u_id
            st.session_state.is_vip = user_data.get("is_vip", False)
            st.query_params["user"] = u_id
            st.rerun()
        elif u_id == "someku" and u_pw == "28616128Ok":
            st.session_state.user = u_id
            st.session_state.is_vip = True
            st.query_params["user"] = u_id
            st.rerun()
        else:
            st.error("❌ Hatalı kullanıcı adı veya şifre!")

    # --- KAYIT OLMA BÖLÜMÜ (Giriş Bloğunun İçinde Ama Butonun Altında) ---
    st.markdown("---")
    with st.expander("✨ Hesabın yok mu? Hemen Kayıt Ol"):
        new_user = st.text_input("Yeni Kullanıcı Adı:", key="reg_user")
        new_email = st.text_input("E-posta Adresi:", key="reg_email")
        new_pw = st.text_input("Yeni Şifre:", type="password", key="reg_pw")
        
        if st.button("Kayıt Ol", use_container_width=True):
            if new_user and new_email and new_pw:
                check = supabase.table("users").select("*").or_(f"username.eq.{new_user},email.eq.{new_email}").execute()
                
                if check.data:
                    st.error("❌ Bu kullanıcı adı veya e-posta zaten kullanılıyor!")
                else:
                    data = {
                        "username": new_user,
                        "email": new_email,
                        "password": new_pw,
                        "is_vip": False,
                        "puan": 0
                    }
                    supabase.table("users").insert(data).execute()
                    st.success("✅ Kayıt başarılı! Yukarıdan giriş yapabilirsin.")
            else:
                st.warning("⚠️ Lütfen tüm alanları doldur!")
                
    # Giriş yapmayan herkesi burada durduruyoruz
    st.stop()
    
    # --- YAN MENÜ (SIDEBAR) AYARLARI ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    
    # VIP Durumunu Göster (Gözüksün ki adam gurur duysun)
    if st.session_state.get('is_vip', False):
        st.success("🌟 VIP SCOUT ÜYESİ")
    else:
        st.info("🆓 STANDART ÜYE")
    
    st.markdown("---")
    
    # --- GÜVENLİ ÇIKIŞ BUTONU ---
    if st.button("🚪 Güvenli Çıkış Yap", use_container_width=True):
        # Session verilerini mermi gibi temizle
        st.session_state.user = None
        st.session_state.is_vip = False
        # URL'deki kullanıcı parametresini sil
        st.query_params.clear()
        st.success("Başarıyla çıkış yapıldı. Yönlendiriliyorsun...")
        st.rerun() # Sayfayı yenileyip giriş ekranına atar


tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🕵️ YETENEK AVI", "🤖 BARROW AI", "🛠️ ADMIN"])

# --- 1. SCOUT ---
with tabs[0]:
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika", "Avusturya", "İsviçre"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan", "Slovenya", "Bosna Hersek", "Romanya"], "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador", "Şili", "Paraguay"], "Afrika": ["Nijerya", "Senegal", "Mısır", "Fildişi Sahili", "Fas", "Cezayir", "Gana", "Kamerun"], "Asya": ["Japonya", "Güney Kore", "Suudi Arabistan", "Katar", "Avustralya", "Çin"]}
    
    curr_user = st.session_state.user
    f1, f2, f3 = st.columns(3)
    with f1: 
        name_f = st.text_input("👤 Oyuncu Ara:")
        team_f = st.text_input("Takım Ara:")
    with f2: 
        reg_f = st.selectbox("🌍 Bölge Seç:", list(REG_TR.keys()))
        country_f = st.text_input("Uyruk (Direkt Ülke):")
    with f3: 
        pos_f = st.selectbox("👟 Mevki Seç:", list(POS_TR.keys()))
        sort_f = st.selectbox("🔃 Sıralama:", ["pa", "ca", "yas", "deger"])
    
    v1, v2 = st.columns(2)
    with v1: age_f = st.slider("🎂 Yaş Aralığı:", 14, 50, (14, 25))
    with v2: pa_f = st.slider("📊 PA Aralığı:", 100, 200, (135, 200))
    
    f_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", curr_user).execute()
    st.session_state.fav_list = [x['oyuncu_adi'] for x in f_res.data] if f_res.data else []

    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if country_f: query = query.ilike("ulke", f"%{country_f}%")
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REG_TR[reg_f])
    
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        user_is_vip = st.session_state.get('is_vip', False)
        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            pa_val, ca_val = p.get("pa", 0), p.get("ca", "-")
            raw_val = str(p.get('deger', ''))
            display_val = "❌ Satılık Değil" if "300.000.000" in raw_val else (raw_val if raw_val not in ["0","£0","None",""] else "💎 Paha Biçilemez")

            with cols[i%2]:
                if pa_val > 150 and not user_is_vip:
                    st.markdown(f'''<div style="padding:15px; border-radius:12px; margin-bottom:10px; border: 2px dashed #f2cc60; background: rgba(242, 204, 96, 0.05); text-align:center;"><span style="background:#f2cc60; color:black; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:bold;">💎 ELİT YETENEK KİLİTLİ</span><h4 style="margin:10px 0; color:#8b949e;">🔒 Gizli Yıldız</h4><p style="font-size:12px; color:#8b949e;">PA: <b>{pa_val}</b> olan bu oyuncunun detayları için VIP üye olmalısın.</p><a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="display:inline-block; background:#238636; color:white; padding:8px 15px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:13px;">KİLİDİ AÇ</a></div>''', unsafe_allow_html=True)
                else:
                    card_border = "#238636" if is_fav else "#30363d"
                    bg_effect = "rgba(35, 134, 54, 0.08)" if is_fav else "rgba(255, 255, 255, 0.02)"
                    st.markdown(f'''<div style="padding:15px; border-radius:15px; margin-bottom:10px; border: 2px solid {card_border}; background: {bg_effect}; position:relative;"><div style="display:flex; justify-content:space-between;"><div><h4 style="margin:0; font-size:16px;">{p["oyuncu_adi"]}</h4><p style="font-size:11px; color:#8b949e; margin:2px 0;">🌍 {p.get("ulke","Bilinmiyor")} | 🎂 {p["yas"]} Yaş</p></div><div style="text-align:right;"><span style="background:#238636; color:white; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:bold;">PA: {p["pa"]}</span><p style="font-size:10px; color:#58a6ff; margin-top:3px;">CA: {ca_val}</p></div></div><div style="border-top:1px solid #30363d; margin-top:10px; padding-top:10px; font-size:12px;"><p style="margin:0;">🏟️ <b>Kulüp:</b> {p.get("kulup","Serbest")}</p><p style="margin:0;">👟 <b>Mevki:</b> {p.get("mevki","--")}</p><p style="margin:0; color:#00ff41;">💰 <b>Değer:</b> {display_val}</p></div><div style="margin-top:10px;"><a href="{tm_url}" target="_blank" style="color:#58a6ff; font-size:11px; text-decoration:none; font-weight:bold;">Transfermarkt Profili ➔</a></div></div>''', unsafe_allow_html=True)
                    btn_txt = "⭐ FAVORİDEN ÇIKAR" if is_fav else "☆ FAVORİLERE EKLE"
                    if st.button(btn_txt, key=f"scout_btn_{p['oyuncu_adi']}_{i}", use_container_width=True):
                        if is_fav: supabase.table("favoriler").delete().eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
                        else: supabase.table("favoriler").insert({"oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup', 'Serbest'), "pa": p['pa'], "mevki": p['mevki'], "ca": p.get('ca', 0), "kullanici_adi": curr_user}).execute()
                        st.rerun()
        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("⬅️ Geri", use_container_width=True) and st.session_state.page > 0: st.session_state.page -= 1; st.rerun()
        with c2: st.markdown(f"<p style='text-align:center;'>Sayfa: {st.session_state.page + 1}</p>", unsafe_allow_html=True)
        if c3.button("İleri ➡️", use_container_width=True): st.session_state.page += 1; st.rerun()

# --- 2. RULET (V187 - HATASIZ VE KİŞİYE ÖZEL) ---
with tabs[1]:
    st.markdown('<h2 style="text-align:center;">🎰 SCOUT RULETİ</h2>', unsafe_allow_html=True)
    
    import random
    import json
    import time
    import urllib.parse

    user_is_vip = st.session_state.get('is_vip', False)
    curr_user = st.session_state.get('user')

    # VIP Durumuna Göre PA Aralığı
    if user_is_vip:
        st.markdown('<div style="text-align:center; padding:10px; background:#f2cc60; color:black; border-radius:15px; font-weight:bold; margin-bottom:15px;">🌟 ALTIN RULET MODU AKTİF (PA 155-200)</div>', unsafe_allow_html=True)
        min_pa, max_pa = 155, 200
        slot_border = "#f2cc60"
    else:
        st.markdown('<div style="text-align:center; padding:10px; background:#30363d; color:white; border-radius:15px; margin-bottom:15px;">🎰 STANDART RULET (PA 130-150)</div>', unsafe_allow_html=True)
        min_pa, max_pa = 130, 150 
        slot_border = "#30363d"

    if 'rulet_winner' not in st.session_state:
        st.session_state.rulet_winner = None
    if 'animasyon_tamam' not in st.session_state:
        st.session_state.animasyon_tamam = False

    # Havuzu Karıştırarak Çek
    try:
        r_offset = random.randint(0, 150) 
        res = supabase.table("oyuncular").select("*").gte("pa", min_pa).lte("pa", max_pa).range(r_offset, r_offset + 80).execute()
        player_pool = res.data if res.data else []
        if player_pool: random.shuffle(player_pool)
    except:
        player_pool = []

    if player_pool:
        btn_label = "🎰 ALTIN RULETİ ÇEVİR" if user_is_vip else "🎰 STANDART RULETİ ÇEVİR"
        if st.button(btn_label, key="rulet_spin_btn", use_container_width=True):
            strip_players = [random.choice(player_pool) for _ in range(30)]
            winner = random.choice(player_pool)
            st.session_state.rulet_winner = winner
            st.session_state.animasyon_tamam = False
            strip_players[25] = winner
            players_json = json.dumps(strip_players)
            
            roulette_html = f"""
            <div style="position:relative; width:100%; height:160px; background:#0d1117; border:3px solid {slot_border}; border-radius:15px; overflow:hidden; display:flex; justify-content:center; align-items:center;">
                <div style="position:absolute; width:100%; height:60px; border-top:2px solid {slot_border}; border-bottom:2px solid {slot_border}; background:rgba(242, 204, 96, 0.05); z-index:10;"></div>
                <div id="slot-track" style="display:flex; flex-direction:column; position:absolute; top:0; transition: top 4s cubic-bezier(0.1, 0, 0.1, 1); width:100%;"></div>
            </div>
            <script>
                (function() {{
                    const players = {players_json};
                    const track = document.getElementById('slot-track');
                    const itemH = 60; const contH = 160; const winI = 25;
                    track.innerHTML = players.map((p, i) => `<div style="height:${{itemH}}px; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center;"><small style="color:#8b949e; font-size:10px;">${{p.kulup || 'Scout Agent'}}</small><b style="color:white; font-size:13px;">${{p.oyuncu_adi}}</b></div>`).join('');
                    setTimeout(() => {{ track.style.top = "-" + ((winI * itemH) - (contH / 2 - itemH / 2)) + "px"; }}, 100);
                }})();
            </script>
            """
            st.components.v1.html(roulette_html, height=180)
            time.sleep(4.5)
            st.session_state.animasyon_tamam = True
            st.rerun()

        if st.session_state.rulet_winner and st.session_state.animasyon_tamam:
            p = st.session_state.rulet_winner
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            
            st.markdown("---")
            card_color = "#f2cc60" if user_is_vip else "#238636"
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.03); border: 2px solid {card_color}; border-radius: 20px; padding: 20px; text-align:center;">
                <h3 style="margin:0; font-size:20px;">{p['oyuncu_adi']}</h3>
                <p style="color:{card_color}; font-weight:bold;">{p['mevki']} | PA: {p['pa']}</p>
                <a href="{tm_url}" target="_blank" style="text-decoration:none; color:#58a6ff; font-size:12px;">Transfermarkt Profili ➔</a>
            </div>
            """, unsafe_allow_html=True)

            if st.button("⭐ FAVORİLERİME EKLE", key=f"fav_btn_rulet_{p['oyuncu_adi']}", use_container_width=True):
                supabase.table("favoriler").insert({"oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup','Serbest'), "pa": p['pa'], "mevki": p['mevki'], "kullanici_adi": curr_user}).execute()
                st.success("✅ Mermi listeye eklendi!")
    else:
        st.warning("Mermi bulunamadı hıyarto!")
        
# --- 3. İLK 11 (V165 - SÜRÜKLE BIRAK FIX) ---
with tabs[2]:
    st.markdown('<h2 style="text-align:center;">🏟️ ELITE ARENA - TAKTİK TAHTASI</h2>', unsafe_allow_html=True)
    
    curr_user = st.session_state.get('user')
    try:
        res_fav = supabase.table("favoriler").select("*").eq("kullanici_adi", curr_user).order("pa", desc=True).execute()
        f_n = [f"{p['oyuncu_adi']} ({p['pa']})" for p in res_fav.data] if res_fav.data else ["Favori Mermi Yok"]
    except:
        f_n = ["Bağlantı Hatası"]

    tactic = st.selectbox("🏟️ Ana Diziliş Seç:", 
                         ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "5-3-2", "4-1-2-1-2"], key="tactic_sel")
    
    st.info("💡 İpucu: Oyuncuları farenizle veya parmağınızla saha üzerinde özgürce hareket ettirebilirsiniz!")

    st.markdown('<div style="color:#58a6ff; font-weight:bold; font-size:12px;">🛡️ DEFANS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    gk = c1.selectbox("GK", f_n, key="sl_gk"); lb = c2.selectbox("LB", f_n, key="sl_lb")
    cb1 = c3.selectbox("CB1", f_n, key="sl_cb1"); cb2 = c4.selectbox("CB2", f_n, key="sl_cb2"); rb = c5.selectbox("RB", f_n, key="sl_rb")

    st.markdown('<div style="color:#238636; font-weight:bold; font-size:12px;">⚡ HÜCUM</div>', unsafe_allow_html=True)
    
    # Mevki koordinatlarını mermi gibi ayarlıyoruz
    if tactic == "4-4-2":
        m1, m2, m3, m4 = st.columns(4)
        lm = m1.selectbox("LM", f_n); cm1 = m2.selectbox("CM1", f_n); cm2 = m3.selectbox("CM2", f_n); rm = m4.selectbox("RM", f_n)
        f1, f2 = st.columns(2)
        st1 = f1.selectbox("ST1", f_n); st2 = f2.selectbox("ST2", f_n)
        positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("LM",lm,40,2), ("CM",cm1,40,26), ("CM",cm2,40,51), ("RM",rm,40,75), ("ST",st1,13,26), ("ST",st2,13,51)]
    
    elif tactic == "4-2-3-1":
        m1, m2, m3, m4, m5 = st.columns(5)
        dm1 = m1.selectbox("CDM1", f_n); dm2 = m2.selectbox("CDM2", f_n); aml = m3.selectbox("LAM", f_n); amc = m4.selectbox("CAM", f_n); amr = m5.selectbox("RAM", f_n)
        st1 = st.selectbox("ST", f_n)
        positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("DM",dm1,52,26), ("DM",dm2,52,51), ("AM",aml,28,5), ("AM",amc,25,39), ("AM",amr,28,72), ("ST",st1,8,39)]

    elif tactic == "3-5-2":
        m1, m2, m3, m4, m5 = st.columns(5)
        lwb = m1.selectbox("LWB", f_n); cm1 = m2.selectbox("CM1", f_n); cdm = m3.selectbox("CDM", f_n); cm2 = m4.selectbox("CM2", f_n); rwb = m5.selectbox("RWB", f_n)
        f1, f2 = st.columns(2)
        st1 = f1.selectbox("ST1", f_n); st2 = f2.selectbox("ST2", f_n)
        positions = [("GK",gk,82,39), ("CB",lb,70,12), ("CB",cb1,70,39), ("CB",cb2,70,66), ("LWB",lwb,45,2), ("DM",cdm,52,39), ("CM",cm1,43,23), ("CM",cm2,43,55), ("RWB",rwb,45,75), ("ST",st1,13,26), ("ST",st2,13,51)]

    else: # Default 4-3-3
        m1, m2, m3 = st.columns(3)
        cm1 = m1.selectbox("LCM", f_n); cm2 = m2.selectbox("CM", f_n); cm3 = m3.selectbox("RCM", f_n)
        f1, f2, f3 = st.columns(3)
        lw = f1.selectbox("LW", f_n); st_p = f2.selectbox("ST", f_n); rw = f3.selectbox("RW", f_n)
        positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("CM",cm1,43,10), ("CM",cm2,43,38), ("CM",cm3,43,66), ("LW",lw,14,5), ("ST",st_p,11,38), ("RW",rw,14,71)]

    # --- HTML & SÜRÜKLEME MOTORU ---
    players_divs = "".join([f'<div class="player draggable" style="top:{y}%; left:{x}%;" onmousedown="startDrag(event)" ontouchstart="startDrag(event)"><div class="pos">{p}</div><div class="name">{n}</div></div>' for p, n, y, x in positions])

    tahta_html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <div id="capture" style="position:relative; background:#1e4620; border:4px solid #ffffff; border-radius:15px; width:360px; height:540px; margin:auto; overflow:hidden;">
        <div style="position:absolute; top:50%; left:0; width:100%; border-top:2px solid rgba(255,255,255,0.4);"></div>
        <div style="position:absolute; top:40%; left:30%; width:40%; height:20%; border:2px solid rgba(255,255,255,0.4); border-radius:50%;"></div>
        {players_divs}
        <div style="position:absolute; bottom:5px; right:10px; color:rgba(255,255,255,0.3); font-size:9px;">SOMEKU ELITE SCOUT</div>
    </div>
    
    <button onclick="downloadImage()" style="width:100%; padding:12px; background:#238636; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:15px;">📸 KADROYU PNG KAYDET</button>

    <script>
        let activeEl = null;
        function startDrag(e) {{
            activeEl = e.target.closest('.draggable');
            document.onmousemove = drag;
            document.ontouchmove = drag;
            document.onmouseup = endDrag;
            document.ontouchend = endDrag;
        }}
        function drag(e) {{
            if (!activeEl) return;
            e.preventDefault();
            let clientX = e.clientX || e.touches[0].clientX;
            let clientY = e.clientY || e.touches[0].clientY;
            let rect = document.getElementById('capture').getBoundingClientRect();
            let x = ((clientX - rect.left - 39) / rect.width) * 100;
            let y = ((clientY - rect.top - 20) / rect.height) * 100;
            activeEl.style.left = x + "%";
            activeEl.style.top = y + "%";
        }}
        function endDrag() {{ activeEl = null; }}
        function downloadImage() {{
            html2canvas(document.querySelector("#capture")).then(canvas => {{
                let link = document.createElement('a');
                link.download = 'mermi-kadro.png';
                link.href = canvas.toDataURL();
                link.click();
            }});
        }}
    </script>
    <style>
        .player {{ position:absolute; background:rgba(13,17,23,0.9); border:1.5px solid #58a6ff; border-radius:8px; color:white; width:78px; padding:4px; text-align:center; cursor:grab; z-index:100; user-select:none; touch-action:none; }}
        .player:active {{ cursor:grabbing; border-color:#f2cc60; transform: scale(1.05); }}
        .pos {{ font-size:9px; color:#58a6ff; font-weight:bold; pointer-events:none; }}
        .name {{ font-size:10px; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; pointer-events:none; }}
    </style>
    """
    st.components.v1.html(tahta_html, height=630)

    kadro_txt = f"Diziliş: {tactic}\n" + "\n".join([f"{p[0]}: {p[1]}" for p in positions])
    st.download_button(label="📄 TXT İNDİR", data=kadro_txt, file_name="mermi-kadro.txt", use_container_width=True)

# --- 4. FAVORİLER (V149 - GÜNCEL TABLO UYUMLU) ---
with tabs[3]:
    st.markdown('<h2 style="text-align:center;">⭐ KALICI FAVORİLERİN</h2>', unsafe_allow_html=True)
    
    # Yeni tablo yapısına göre verileri çekiyoruz
    res = supabase.table("favoriler").select("*").order("created_at", desc=True).execute()
    
    if res.data:
        # Favorileri şık kartlar halinde gösterelim
        for p in res.data:
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); border-left: 5px solid #238636; border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin:0; color: white;">{p['oyuncu_adi']}</h4>
                            <small style="color: #8b949e;">🏟️ {p.get('kulup', 'Serbest')} | 📍 {p.get('mevki', '-')}</small>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: #238636; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px;">PA: {p['pa']}</span>
                            <span style="background: #1a3151; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px; margin-left: 5px;">CA: {p.get('ca', '-')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Silme Butonu (Her oyuncunun altına küçük bir buton)
                if st.button(f"🗑️ Sil: {p['oyuncu_adi']}", key=f"del_{p['id']}"):
                    supabase.table("favoriler").delete().eq("id", p['id']).execute()
                    st.success("Mermi listeden çıkarıldı!")
                    st.rerun()
    else:
        st.info("Henüz favori mermin yok. Rulet kısmından avlanmaya başla! 🕵️‍♂️")
        
# --- 5. GİZLİ YETENEK AVI (V540 - KESKİN KURALLAR & NET BÖLGELER) ---
with tabs[4]:
    import unicodedata
    import time
    import random
    st.markdown('<h2 style="text-align:center; color:#f2cc60;">🕵️ GİZLİ YETENEK AVI</h2>', unsafe_allow_html=True)
    
    # --- OYUN KURALLARI ---
    with st.expander("📖 Oyun Kuralları & Analiz Notları", expanded=True):
        st.markdown("""
        1. **Bölgesel Analiz:** Mevki karmaşasını bitirdik. Oyuncular 4 ana bölgede (Hücum, Orta Saha, Savunma, Kaleci) analiz edilir.
        2. **Bonservis Kuralı:** Oyuncu kiralıksa, kiralık gittiği yer değil **asıl ait olduğu kulüp** görünür.
        3. **İpucu Akışı:** Son 10s PA (Potansiyel), son 5s CA (Yetenek) verileri sistemden şak diye açılır.
        4. **Akıllı Tespit:** Harf yazdığın an elit adaylar aşağıya dizilir. Seçtiğin an sistem kutuyu temizler ve teşhisi koyar.
        5. **⚠️ Önemli:** Sistem yapay zeka destekli olduğu için nadiren veri sapmaları olabilir; gerçek bir scout her zaman tetiktedir!
        """)

    # --- YARDIMCI FONKSİYONLAR ---
    def metin_temizle(metin):
        if not metin: return ""
        metin = str(metin).lower().replace('ı', 'i').replace('İ', 'i').strip()
        nfkd_form = unicodedata.normalize('NFKD', metin)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def bolgesel_mevki_yap(m):
        m = str(m).upper()
        # 1. KALECİ
        if "GK" in m: return "🧤 KALECİ"
        
        # 2. HÜCUM BÖLGESİ (Forvetler ve Kanatlar)
        if any(x in m for x in ["ST", "CF", "AM R", "AM L", "MR", "ML", "LW", "RW"]): 
            return "🔥 HÜCUM BÖLGESİ"
        
        # 3. SAVUNMA BÖLGESİ (Stoperler, Bekler ve Liberolar)
        if any(x in m for x in ["D C", "DC", "D R", "DR", "D L", "DL", "SW", "WBR", "WBL"]): 
            return "🛡️ SAVUNMA BÖLGESİ"
        
        # 4. ORTA SAHA BÖLGESİ (Diğer tüm orta saha türevleri)
        return "🧠 ORTA SAHA BÖLGESİ"

    # --- DURUM YÖNETİMİ ---
    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'target_p' not in st.session_state: st.session_state.target_p = None
    if 'last_result' not in st.session_state: st.session_state.last_result = None
    if 'input_key' not in st.session_state: st.session_state.input_key = 0

    def yeni_av_tetikle():
        st.session_state.last_result = None
        st.session_state.input_key += 1 # Kutuyu sıfırlamak için anahtarı değiştir
        res_g = supabase.table("oyuncular").select("*").not_.eq("kulup", "None").gte("pa", 165).execute()
        if res_g.data:
            st.session_state.all_player_names = sorted(list(set([r['oyuncu_adi'] for r in res_g.data])))
            st.session_state.target_p = random.choice(res_g.data)
            st.session_state.game_active = True
            st.session_state.game_start_time = time.time()

    # --- BAŞLATMA ---
    if not st.session_state.game_active and st.session_state.last_result is None:
        if st.button("🚀 ANALİZİ BAŞLAT", use_container_width=True):
            yeni_av_tetikle()
            st.rerun()

    # --- OYUN ALANI ---
    if st.session_state.game_active and st.session_state.target_p:
        p = st.session_state.target_p
        kalan = max(0, int(30 - (time.time() - st.session_state.game_start_time)))
        yuzde = (kalan / 30) * 100
        
        if kalan > 0:
            pa_hint = f"🔥 PA: {p['pa']}" if kalan <= 10 else "🔥 PA: ??"
            ca_hint = f"📊 CA: {p.get('ca','?')}" if kalan <= 5 else "📊 CA: ??"
            
            st.markdown(f"""
                <div style="background:#161b22; padding:20px; border-radius:15px; border:2px solid #30363d; text-align:center;">
                    <h2 style="color:#f2cc60; margin:0;">{bolgesel_mevki_yap(p['mevki'])}</h2>
                    <div style="width:100%; background:#333; height:10px; border-radius:10px; margin:10px 0;">
                        <div style="width:{yuzde}%; background:#3b82f6; height:100%; border-radius:10px;"></div>
                    </div>
                    <p style="font-size:20px;">🎂 <b>{p['yas']} Yaş</b> | 🏟️ <b>{p['kulup']}</b></p>
                    <div style="display:flex; justify-content:center; gap:20px; font-weight:bold; font-size:17px;">
                        <span style="color:#f2cc60;">{pa_hint}</span>
                        <span style="color:#58a6ff;">{ca_hint}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            st.write("")
            query = st.text_input("Hedef ismini yazmaya başla...", key=f"input_{st.session_state.input_key}").strip()
            
            if query:
                matches = [name for name in st.session_state.all_player_names if metin_temizle(query) in metin_temizle(name)][:5]
                
                if matches:
                    st.write("🎯 **Potansiyel Hedefler (Analiz Et):**")
                    for match in matches:
                        if st.button(f"📍 {match}", key=f"btn_{match}", use_container_width=True):
                            st.session_state.input_key += 1 # Kutuyu sıfırla
                            if metin_temizle(match) == metin_temizle(p['oyuncu_adi']):
                                st.session_state.last_result = "WIN"
                                st.session_state.game_active = False
                                try:
                                    c = supabase.table("users").select("puan").eq("username", st.session_state.user).execute()
                                    eski = c.data[0].get("puan", 0) if c.data else 0
                                    supabase.table("users").update({"puan": eski + 1}).eq("username", st.session_state.user).execute()
                                except: pass
                            else:
                                st.error("❌ Yanlış Teşhis! Hedef bu değil.")
                            st.rerun()

            time.sleep(0.5)
            st.rerun()
        else:
            st.session_state.last_result = "LOSE"
            st.session_state.game_active = False
            st.rerun()

    # --- SONUÇ VE GERİ SAYIM ---
    if st.session_state.last_result:
        p = st.session_state.target_p
        if st.session_state.last_result == "WIN":
            st.balloons()
            st.success(f"🎯 HEDEF TESPİT EDİLDİ: {p['oyuncu_adi']}")
        else:
            st.error(f"⌛ VERİ ANALİZİ BAŞARISIZ! Aranan Hedef: {p['oyuncu_adi']}")

        if st.button("🚫 Durdur / Vazgeç"):
            st.session_state.last_result = None
            st.session_state.input_key += 1
            st.rerun()

        placeholder = st.empty()
        for i in range(5, 0, -1):
            placeholder.info(f"🔄 {i} saniye içinde yeni hedef belirlenecek...")
            time.sleep(1)
        
        yeni_av_tetikle()
        st.rerun()




    # --- 5. LİDERLİK TABLOSU (SADE VE GÜVENLİ) ---
    st.subheader("🏆 TOP 10 ELITE SCOUTS")
    try:
        leaders = supabase.table("users").select("username, puan").order("puan", desc=True).limit(10).execute()
        if leaders.data:
            import pandas as pd
            df = pd.DataFrame(leaders.data)
            df.columns = ["SCOUT ADI", "PUAN"]
            df.index = df.index + 1
            st.table(df)
    except:
        st.write("Tablo yüklenemedi.")

# --- 5. BARROW AI (V550 - MASTER SCOUT EDITION) ---
with tabs[5]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW AI</h1><p style="color:#8b949e;">Yapay Zeka Destekli Scout Danışmanı</p></div>', unsafe_allow_html=True)
    
    user_is_vip = st.session_state.get('is_vip', False)
    curr_user = st.session_state.get('user')
    
    if "barrow_player" not in st.session_state: st.session_state.barrow_player = None

    # --- VIP VE HAK KONTROLÜ ---
    can_ask = True
    if not user_is_vip:
        u_data = supabase.table("users").select("barrow_count", "last_barrow_date").eq("username", curr_user).execute()
        if u_data.data:
            count = u_data.data[0].get('barrow_count', 0)
            l_date = u_data.data[0].get('last_barrow_date')
            today = str(datetime.date.today())
            if l_date != today:
                supabase.table("users").update({"barrow_count": 0, "last_barrow_date": today}).eq("username", curr_user).execute()
                count = 0
            if count >= 3:
                can_ask = False
                st.warning("🔒 Günlük 3 ücretsiz analiz hakkınız dolmuştur. Daha fazla analiz için VIP paketine geçebilirsiniz.")
                st.markdown(f'''<a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#ef4444; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">SINIRSIZ ANALİZ İÇİN VIP OL</button></a>''', unsafe_allow_html=True)

    # --- BARROW GİRİŞ ALANI ---
    st.info("💡 Not: Ben bir yapay zekayım, bazen verilerde ufak sapmalar yapabilirim. Lütfen analizleri transfermarkt ile teyit etmeyi unutma!")
    b_in = st.text_input("Barrow'a kriterlerini söyle (Örn: '5m euroya kadar 19 yaş Arjantinli sağ bek'):", key="b_v550", disabled=not can_ask)
    
    if st.button("ANALİZİ BAŞLAT", disabled=not can_ask):
        if b_in:
            if not user_is_vip:
                new_count = u_data.data[0].get('barrow_count', 0) + 1
                supabase.table("users").update({"barrow_count": new_count}).eq("username", curr_user).execute()

            st.write("🔍 Veritabanı taranıyor, kriterlerinize en uygun profil seçiliyor...")
            
            bq = supabase.table("oyuncular").select("*").gte("pa", 130)
            low_in = b_in.lower()
            
            # --- 1. PARA / DEĞER ANALİZİ (Milyon ve Bin Euro) ---
            # "5m", "500bin", "1m 5m arası" gibi ifadeleri yakalar
            price_nums = re.findall(r'(\d+)\s*(m|milyon|bin|k)', low_in)
            if price_nums:
                # "1m 5m arası" gibi bir aralık var mı?
                range_price = re.search(r'(\d+)\s*(?:m|milyon)?\s*(?:ile|ve|ila|-|–)\s*(\d+)\s*(m|milyon)', low_in)
                if range_price:
                    p1, p2 = int(range_price.group(1)) * 1_000_000, int(range_price.group(2)) * 1_000_000
                    bq = bq.gte("deger_num", min(p1, p2)).lte("deger_num", max(p1, p2))
                else:
                    val, unit = price_nums[0]
                    total_val = int(val) * 1_000_000 if unit in ["m", "milyon"] else int(val) * 1_000
                    if any(x in low_in for x in ["en fazla", "max", "kadar", "altı"]):
                        bq = bq.lte("deger_num", total_val)
                    elif any(x in low_in for x in ["en az", "min", "üstü"]):
                        bq = bq.gte("deger_num", total_val)
                    else: # Varsayılan: Belirtilen rakama kadar olanları getir
                        bq = bq.lte("deger_num", total_val)

            # --- 2. YAŞ ANALİZİ ---
            age_range = re.search(r'(\d+)\s*(?:ile|ve|ila|-|–)\s*(\d+)\s*yaş', low_in)
            age_nums = re.findall(r'(\d+)\s*yaş', low_in)
            if age_range:
                a1, a2 = int(age_range.group(1)), int(age_range.group(2))
                bq = bq.gte("yas", min(a1, a2)).lte("yas", max(a1, a2))
            elif any(x in low_in for x in ["en fazla", "en çok", "max", "kadar"]) and age_nums:
                bq = bq.lte("yas", int(age_nums[0]))
            elif age_nums:
                bq = bq.eq("yas", int(age_nums[0]))

            # --- 3. MEVKİ ANALİZİ (TÜRKÇE) ---
            m_map = {
                "kaleci": "GK", "sağ bek": "D R", "sol bek": "D L", "stoper": "D C", "defans": "D C",
                "ön libero": "DM", "orta saha": "M C", "on numara": "AM C", "10 numara": "AM C",
                "sağ kanat": "AM R", "sol kanat": "AM L", "forvet": "ST", "santrafor": "ST"
            }
            for k, v in m_map.items():
                if k in low_in:
                    bq = bq.ilike("mevki", f"%{v}%")
                    break

            # --- 4. BÖLGE VE ÜLKE ANALİZİ ---
            regions = {
                "güney amerika": ["Argentina", "Brazil", "Uruguay", "Colombia", "Chile", "Ecuador"],
                "iskandinav": ["Norway", "Sweden", "Denmark", "Finland", "Iceland"],
                "afrika": ["Nigeria", "Senegal", "Ivory Coast", "Ghana", "Cameroon", "Algeria", "Morocco", "Egypt"],
                "balkan": ["Croatia", "Serbia", "Bosnia", "Albania", "Slovenia", "Montenegro", "Bulgaria", "Greece"]
            }
            found_region = False
            for reg, countries in regions.items():
                if reg in low_in:
                    bq = bq.in_("ulke", countries)
                    found_region = True
                    break
            
            if not found_region:
                # Özel ülke araması (Arjantinli, Fransız vb. veya direkt ülke adı)
                tr_to_en_country = {"arjantin": "Argentina", "brezilya": "Brazil", "fransa": "France", "almanya": "Germany", "türkiye": "Turkey", "portekiz": "Portugal"}
                for tr, en in tr_to_en_country.items():
                    if tr in low_in:
                        bq = bq.eq("ulke", en)
                        break

            res_b = bq.limit(50).execute()
            if res_b.data:
                st.session_state.barrow_player = random.choice(res_b.data)
            else:
                st.session_state.barrow_player = "empty"
            st.rerun()

    # --- OYUNCU KARTI ---
    if st.session_state.barrow_player and st.session_state.barrow_player != "empty":
        p = st.session_state.barrow_player
        # Favori kontrolü (Sadece giriş yapan kullanıcıya özel)
        f_check = supabase.table("favoriler").select("oyuncu_adi").eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
        is_f = len(f_check.data) > 0
        
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        
        st.markdown(f'''
        <div style="background:#111; border:2px solid #ef4444; padding:25px; border-radius:20px; margin-top:20px; position:relative; box-shadow: 0 10px 30px rgba(239, 68, 68, 0.2);">
            <div style="position:absolute; top:15px; right:15px; text-align:right;">
                <span style="background:#ef4444; color:white; padding:5px 12px; border-radius:8px; font-weight:bold; font-size:14px;">PA: {p["pa"]}</span><br>
                <span style="color:#8b949e; font-size:12px; display:block; margin-top:5px;">CA: {p.get("ca", "-")}</span>
            </div>
            <h2 style="color:#fff; margin:0; font-size:28px;">{p["oyuncu_adi"]}</h2>
            <hr style="border:0; border-top:1px solid #333; margin:15px 0;">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#ccc; font-size:15px;">
                <div>🌍 <b>Ülke:</b> {p.get("ulke", "-")}</div>
                <div>🏟️ <b>Kulüp:</b> {p.get("kulup", "Serbest")}</div>
                <div>👟 <b>Mevki:</b> {p.get("mevki", "-")}</div>
                <div>🎂 <b>Yaş:</b> {p.get("yas", "-")}</div>
                <div style="grid-column: span 2; color:#238636; font-weight:bold; font-size:18px; margin-top:5px;">💰 Değer: {p.get("deger", "Bilinmiyor")}</div>
            </div>
            <div style="margin-top:20px;">
                <a href="{tm_url}" target="_blank" style="text-decoration:none; color:#58a6ff; font-size:14px; border:1px solid #30363d; padding:8px 15px; border-radius:8px; background:#1a1a1a;">Transfermarkt Profili ➔</a>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("⭐ Favori Listeme Ekle / Çıkar", key="barrow_fav_v550"):
            if is_f:
                supabase.table("favoriler").delete().eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
                st.toast("Oyuncu favorilerinden çıkarıldı.")
            else:
                supabase.table("favoriler").insert({
                    "oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup','Serbest'),
                    "pa": p['pa'], "mevki": p['mevki'], "ca": p.get('ca', 0),
                    "kullanici_adi": curr_user # Sadece bu kullanıcı görecek
                }).execute()
                st.toast("Oyuncu favorilerine eklendi!")
            st.rerun()

    elif st.session_state.barrow_player == "empty":
        st.warning("Aradığınız kriterlere uygun bir profil bulunamadı. Lütfen kriterlerinizi esnetmeyi deneyin.")

# --- 6. ADMIN (V135 - TAM YETKİLİ YÖNETİM MERKEZİ) ---
with tabs[6]: 
    if st.session_state.get('user') == "someku":
        st.markdown('<h1 style="color:#ff4b4b; text-align:center;">🛡️ YÖNETİM MERKEZİ</h1>', unsafe_allow_html=True)
        
        # --- GENEL İSTATİSTİKLER ---
        try:
            # Kullanıcıları çek
            u_res = supabase.table("users").select("*").execute()
            users_list = u_res.data if u_res.data else []
            
            # Oyuncu sayısını çek
            res_count = supabase.table("oyuncular").select("*", count="exact").limit(1).execute()
            total_players = res_count.count
            
            # VIP sayısını hesapla
            vip_count = len([u for u in users_list if u.get('is_vip')])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Toplam Oyuncu", f"{total_players:,}".replace(",", "."))
            c2.metric("Kayıtlı Kullanıcı", len(users_list))
            c3.metric("Aktif VIP", vip_count)
            c4.success("Sistem: Aktif")
        except Exception as e:
            st.error(f"Veri çekme hatası: {e}")
            users_list = []

        st.markdown("---")
        adm_tabs = st.tabs(["👥 Kullanıcı & VIP", "🔍 Oyuncu Denetimi", "🛠️ Sistem Bakımı"])

        # --- A. KULLANICI & VIP YÖNETİMİ ---
        with adm_tabs[0]:
            st.write("### 👥 Kullanıcı Listesi ve Yetkilendirme")
            
            # Arama filtresi (Kullanıcılar arasında)
            search_u = st.text_input("Kullanıcı Ara:", placeholder="Kullanıcı adı yazın...")
            
            for u in users_list:
                # Arama yapılıyorsa filtrele
                if search_u and search_u.lower() not in u['username'].lower():
                    continue
                    
                with st.expander(f"{'🌟' if u.get('is_vip') else '⚪'} {u['username']} - {u.get('email', 'E-posta Yok')}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Şifre:** `{u.get('password')}`")
                        st.write(f"**Puan:** `{u.get('puan', 0)}` SC")
                        st.write(f"**Barrow Hak:** `{u.get('barrow_count', 0)}/3`")
                    
                    with col2:
                        # VIP Tarih Ayarı
                        db_date = u.get('last_barrow_date')
                        try:
                            default_date = datetime.datetime.strptime(db_date, "%Y-%m-%d").date() if db_date else datetime.date.today()
                        except:
                            default_date = datetime.date.today()
                        
                        new_date = st.date_input(f"VIP Bitiş Tarihi:", value=default_date, key=f"date_{u['username']}")
                        is_vip_toggle = st.checkbox("VIP Yetkisi Ver", value=u.get('is_vip', False), key=f"check_{u['username']}")

                    with col3:
                        st.write(" İşlemler")
                        if st.button("💾 GÜNCELLE", key=f"upd_{u['username']}", use_container_width=True):
                            supabase.table("users").update({
                                "is_vip": is_vip_toggle,
                                "last_barrow_date": str(new_date)
                            }).eq("username", u['username']).execute()
                            st.success("Güncellendi!")
                            st.rerun()
                            
                        if u['username'] != "someku":
                            if st.button("🗑️ SİL", key=f"del_{u['username']}", use_container_width=True):
                                supabase.table("users").delete().eq("username", u['username']).execute()
                                st.warning("Kullanıcı silindi.")
                                st.rerun()

        # --- B. OYUNCU DENETİMİ ---
        with adm_tabs[1]:
            st.write("### ✏️ Oyuncu Bilgisi Güncelle")
            target_p_name = st.text_input("Düzenlenecek Oyuncu Adı (Tam Eşleşme):")
            if target_p_name:
                p_data = supabase.table("oyuncular").select("*").eq("oyuncu_adi", target_p_name).execute()
                if p_data.data:
                    p_edit = p_data.data[0]
                    e1, e2, e3 = st.columns(3)
                    new_pa = e1.number_input("PA:", value=int(p_edit['pa']))
                    new_ca = e2.number_input("CA:", value=int(p_edit.get('ca', 0)))
                    new_club = e3.text_input("Kulüp:", value=p_edit.get('kulup', ''))
                    
                    if st.button("DEĞİŞİKLİKLERİ KAYDET"):
                        supabase.table("oyuncular").update({
                            "pa": new_pa, 
                            "ca": new_ca, 
                            "kulup": new_club
                        }).eq("oyuncu_adi", target_p_name).execute()
                        st.success("Oyuncu mermi gibi güncellendi!")
                else:
                    st.error("Oyuncu bulunamadı.")

        # --- C. SİSTEM BAKIMI ---
        with adm_tabs[2]:
            st.write("### 🛠️ Kritik Sistem Araçları")
            
            c_sec1, c_sec2 = st.columns(2)
            
            with c_sec1:
                if st.button("🧹 ÖNBELLEĞİ TEMİZLE", use_container_width=True):
                    st.cache_data.clear()
                    st.success("Streamlit cache temizlendi.")
                
                st.info("Bu işlem sayfanın yavaşlamasını önler.")

            with c_sec2:
                # Toplu Puan Sıfırlama vb. eklenebilir
                if st.button("📉 TÜM BARROW HAKLARINI SIFIRLA", use_container_width=True):
                    supabase.table("users").update({"barrow_count": 0}).execute()
                    st.success("Tüm standart üyelerin günlük hakları sıfırlandı.")

    else:
        st.markdown("""
            <div style="text-align:center; padding:50px;">
                <h1 style="font-size:100px;">🚫</h1>
                <h2>YETKİSİZ ERİŞİM</h2>
                <p>Bu bölgeye sadece ana scout (someku) erişebilir.</p>
            </div>
        """, unsafe_allow_html=True)
        