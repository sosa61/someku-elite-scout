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
import threading
import unicodedata

# --- 1. BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "sb_publishable_NHESQOd8-v3tYpVPcz88-w_vypIPQ8Z"

try:
    supabase = create_client(URL, KEY)
except Exception as e:
    st.error(f"Bağlantı kurulum hatası: {e}")

# --- 2. OTURUM AYARLARI ---
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user' not in st.session_state: st.session_state.user = None
if 'is_vip' not in st.session_state: st.session_state.is_vip = False
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'page' not in st.session_state: st.session_state.page = 0
# --- 3. 🔄 F5 VE HAFIZA KONTROLÜ (ZIRHLI VERSİYON) ---
query_user = st.query_params.get("user", None)
is_authenticated = st.session_state.get("authenticated", False)

# EĞER GİZLİ SEKMEDEN LİNKLE GELİNİYORSA:
# (Yani URL'de isim var ama bu tarayıcıda henüz şifre girilmemişse)
if query_user and not is_authenticated:
    # Hafızayı zorla boş tut, URL'deki isme inanma!
    st.session_state.user = None 
    st.session_state.authenticated = False

# --- 5. GİRİŞ VE KAYIT EKRANI ---
if not is_authenticated:
    st.markdown('<h1 style="text-align:center;">🕵️ SOMEKU SCOUT</h1>', unsafe_allow_html=True)
    if query_user:
        st.warning("⚠️ Bu profil kilitlidir. Görmek için önce giriş yapmalısın!")

    auth_tabs = st.tabs(["Giriş Yap", "Kayıt Ol"])

    with auth_tabs[0]:
        u_id = st.text_input("Kullanıcı Adı:", key="main_l_user")
        u_pw = st.text_input("Şifre:", type="password", key="main_l_pw")
        if st.button("Sisteme Giriş Yap"):
            try:
                res = supabase.table("users").select("*").eq("username", u_id).eq("password", u_pw).execute()
                if res.data:
                    st.session_state.authenticated = True
                    st.session_state.user = u_id
                    st.session_state.is_vip = bool(res.data[0].get("is_vip", False))
                    st.query_params["user"] = u_id
                    st.rerun()
                elif u_id == "someku" and u_pw == "28616128Ok":
                    st.session_state.authenticated = True
                    st.session_state.user = u_id
                    st.session_state.is_vip = True
                    st.query_params["user"] = u_id
                    st.rerun()
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")
            except Exception as e:
                st.error(f"⚠️ Giriş Hatası: {e}")

    with auth_tabs[1]:
        st.info("✨ Yeni bir hesap oluşturun.")
        new_user = st.text_input("Yeni Kullanıcı Adı:", key="reg_user")
        new_email = st.text_input("E-posta Adresi:", key="reg_email")
        new_pw = st.text_input("Yeni Şifre:", type="password", key="reg_pw")
        if st.button("Hemen Kayıt Ol", use_container_width=True):
            if new_user and new_email and new_pw:
                check = supabase.table("users").select("*").or_(f"username.eq.{new_user},email.eq.{new_email}").execute()
                if check.data:
                    st.error("❌ Bu kullanıcı adı veya e-posta zaten kullanılıyor!")
                else:
                    data = {"username": new_user, "email": new_email, "password": new_pw, "is_vip": False, "puan": 0}
                    supabase.table("users").insert(data).execute()
                    st.success("✅ Kayıt başarılı! Giriş sekmesine dönebilirsin.")
    st.stop()

# --- 6. YAN MENÜ VE ÇIKİŞ BUTONU ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    if st.session_state.is_vip:
        st.success("🌟 VIP SCOUT ÜYESİ")
    else:
        st.info("🆓 STANDART ÜYE")
    
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış Yap", use_container_width=True):
        st.session_state.clear() # Tüm hafızayı boşalt
        st.query_params.clear()  # URL'yi temizle
        st.rerun()

# --- 7. VIP TAZELEME MOTORU ---
try:
    v_res = supabase.table("users").select("is_vip").eq("username", st.session_state.user).execute()
    if v_res.data:
        st.session_state.is_vip = bool(v_res.data[0].get("is_vip", False))
except:
    pass

# Sayfa ayarlarını dükkanın içine girdikten sonra yapıyoruz
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# Buradan aşağısı senin tabs = st.tabs([...]) kodlarınla devam edecek...

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #0d1117; color: white; }
    .player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; transition: 0.3s; }
    </style>
""", unsafe_allow_html=True)

# --- ANA SEKMELER ---
tabs = st.tabs(["🔍 SCOUT", "🎰 RULET", "📋 11 KUR", "⭐ FAVORİLER", "🕵️ YETENEK AVI", "🤖 BARROW AI", "🛠️ ADMIN"])

# (Buradan aşağısı senin gönderdiğin SCOUT, RULET, 11 KUR vb. kodlarınla devam ediyor...)

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
        sort_f = st.selectbox("🔃 Sıralama Ölçütü:", ["pa", "ca", "yas"]) 
        sort_dir = st.selectbox("↕️ Sıralama Yönü:", ["En Yüksek / En Büyük", "En Düşük / En Küçük"])
    
    v1, v2, v3 = st.columns(3)
    with v1: age_f = st.slider("🎂 Yaş Aralığı:", 14, 50, (14, 25))
    with v2: pa_f = st.slider("📊 PA Aralığı:", 100, 200, (135, 200))
    with v3: val_f = st.slider("💰 Bütçe (Milyon £):", 0, 300, (0, 300))
    
    is_descending = True if sort_dir == "En Yüksek / En Büyük" else False

    f_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", curr_user).execute()
    st.session_state.fav_list = [x['oyuncu_adi'] for x in f_res.data] if f_res.data else []

    query = supabase.table("oyuncular").select("*")\
        .gte("yas", age_f[0]).lte("yas", age_f[1])\
        .gte("pa", pa_f[0]).lte("pa", pa_f[1])

    if name_f: query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: query = query.ilike("kulup", f"%{team_f}%")
    if country_f: query = query.ilike("ulke", f"%{country_f}%")
    
    pos_f = st.selectbox("👟 Mevki Seç:", list(POS_TR.keys()))
    if pos_f != "Hepsi": query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi": query = query.in_("ulke", REG_TR[reg_f])
    
    # Bütçe filtresi için daha geniş veri çekiyoruz (Filtreleme kod tarafında kesinleşecek)
    res = query.order(sort_f, desc=is_descending).limit(500).execute()
    
    if res.data:
        def get_numeric_value(val_str):
            try:
                # Sayıyı temizle ve float'a çevir
                s = str(val_str).lower().replace('£','').replace('€','').replace(',','').strip()
                match = re.search(r"(\d+\.?\d*)", s)
                if not match: return 0
                num = float(match.group(1))
                if 'm' in s: return num
                if 'k' in s: return num / 1000
                if num > 1000: return num / 1000000 # Eğer ham sayı gelirse
                return num
            except: return 0

        # --- KESİN FİLTRELEME ---
        filtered_data = [p for p in res.data if val_f[0] <= get_numeric_value(p.get('deger', 0)) <= val_f[1]]
        
        # Sayfalama mantığı (Geniş listeden seçilen sayfa)
        start_idx = st.session_state.page * 12
        display_data = filtered_data[start_idx : start_idx + 12]

        if not display_data and st.session_state.page > 0:
            st.session_state.page = 0
            st.rerun()

        cols = st.columns(2)
        user_is_vip = st.session_state.get('is_vip', False)
        for i, p in enumerate(display_data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            pa_val, ca_val = p.get("pa", 0), p.get("ca", "-")
            
            # --- 300M VE ÜSTÜNÜ SATILAMAZ YAP ---
            current_val_num = get_numeric_value(p.get('deger', 0))
            if current_val_num >= 300:
                display_val = "❌ Satılamaz"
            else:
                display_val = p.get('deger', 'Bilinmiyor')

            with cols[i%2]:
                if pa_val > 150 and not user_is_vip:
                    st.markdown(f'''<div style="padding:15px; border-radius:12px; margin-bottom:10px; border: 2px dashed #f2cc60; background: rgba(242, 204, 96, 0.05); text-align:center;"><span style="background:#f2cc60; color:black; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:bold;">💎 ELİT YETENEK KİLİTLİ</span><h4 style="margin:10px 0; color:#8b949e;">🔒 Gizli Yıldız</h4><p style="font-size:12px; color:#8b949e;">PA: <b>{pa_val}</b> olan bu oyuncunun detayları için VIP üye olmalısın.</p><a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="display:inline-block; background:#238636; color:white; padding:8px 15px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:13px;">KİLİDİ AÇ</a></div>''', unsafe_allow_html=True)
                else:
                    card_border = "#238636" if is_fav else "#30363d"
                    bg_effect = "rgba(35, 134, 54, 0.08)" if is_fav else "rgba(255, 255, 255, 0.02)"
                    st.markdown(f'''<div style="padding:15px; border-radius:15px; margin-bottom:10px; border: 2px solid {card_border}; background: {bg_effect}; position:relative;"><div style="display:flex; justify-content:space-between;"><div><h4 style="margin:0; font-size:16px;">{p["oyuncu_adi"]}</h4><p style="font-size:11px; color:#8b949e; margin:2px 0;">🌍 {p.get("ulke","Bilinmiyor")} | 🎂 {p["yas"]} Yaş</p></div><div style="text-align:right;"><span style="background:#238636; color:white; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:bold;">PA: {p["pa"]}</span><p style="font-size:10px; color:#58a6ff; margin-top:3px;">CA: {ca_val}</p></div></div><div style="border-top:1px solid #30363d; margin-top:10px; padding-top:10px; font-size:12px;"><p style="margin:0;">🏟️ <b>Kulüp:</b> {p.get("kulup","Serbest")}</p><p style="margin:0;">👟 <b>Mevki:</b> {p.get("mevki", "--")}</p><p style="margin:0; color:#00ff41;">💰 <b>Değer:</b> {display_val}</p></div><div style="margin-top:10px;"><a href="{tm_url}" target="_blank" style="color:#58a6ff; font-size:11px; text-decoration:none; font-weight:bold;">Transfermarkt Profili ➔</a></div></div>''', unsafe_allow_html=True)
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

# --- 2. RULET (V196 - ECONOMY MIX) ---
with tabs[1]:
    st.markdown('<div style="text-align:center;"><h2 style="color:#ef4444;">🎰 WONDERKID RULETİ</h2><p style="color:#8b949e;">Maksimum 21 Yaş | Maksimum 30M Değer</p></div>', unsafe_allow_html=True)
    
    import random
    import json
    import time
    import urllib.parse

    user_is_vip = st.session_state.get('is_vip', False)
    curr_user = st.session_state.get('user')

    # --- RULET AYARLARI ---
    if user_is_vip:
        st.markdown('<div style="text-align:center; padding:10px; background:#f2cc60; color:black; border-radius:15px; font-weight:bold; margin-bottom:15px;">🌟 ALTIN VIP RULET (PA 140-200)</div>', unsafe_allow_html=True)
        min_pa, max_pa = 140, 200
        slot_border = "#f2cc60"
    else:
        st.markdown('<div style="text-align:center; padding:10px; background:#30363d; color:white; border-radius:15px; margin-bottom:15px;">🎰 STANDART RULET (PA 125-150)</div>', unsafe_allow_html=True)
        min_pa, max_pa = 125, 150 
        slot_border = "#30363d"

    if 'rulet_winner' not in st.session_state: st.session_state.rulet_winner = None
    if 'animasyon_tamam' not in st.session_state: st.session_state.animasyon_tamam = False

    # --- TAM KARIŞIK VE GÜVENLİ VERİ ÇEKME ---
    player_pool = []
    try:
        def get_price_num(txt):
            try:
                s = str(txt).lower().replace('£','').replace('€','').strip()
                n = float(re.findall(r"(\d+\.?\d*)", s)[0])
                if 'm' in s: return n
                if 'k' in s: return n / 1000
                return n if n < 1000 else n / 1000000
            except: return 0

        # Rastgele bir sayfadan çekerek tam karışıklık sağlıyoruz
        random_offset = random.randint(0, 100)
        res = supabase.table("oyuncular").select("*").gte("pa", min_pa).lte("pa", max_pa).lte("yas", 21).range(random_offset, random_offset + 150).execute()
        
        if res.data:
            # Sadece değeri 30M ve altı olanları ayıkla
            player_pool = [p for p in res.data if get_price_num(p.get('deger', 0)) <= 30]
            random.shuffle(player_pool)
    except Exception as e:
        st.error("⚠️ Bağlantı hatası, lütfen tekrar dene patron!")

    if player_pool:
        btn_label = "🎰 ALTIN RULETİ ÇEVİR" if user_is_vip else "🎰 STANDART RULETİ ÇEVİR"
        if st.button(btn_label, key="rulet_spin_btn_v196", use_container_width=True):
            winner = random.choice(player_pool)
            strip_players = [random.choice(player_pool) for _ in range(30)]
            strip_players[25] = winner
            
            st.session_state.rulet_winner = winner
            st.session_state.animasyon_tamam = False
            
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
                    track.innerHTML = players.map(p => `<div style="height:${{itemH}}px; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center;"><small style="color:#8b949e; font-size:10px;">${{p.kulup || 'Scout Agent'}}</small><b style="color:white; font-size:13px;">${{p.oyuncu_adi}}</b></div>`).join('');
                    setTimeout(() => {{ track.style.top = "-" + ((winI * itemH) - (contH / 2 - itemH / 2)) + "px"; }}, 100);
                }})();
            </script>
            """
            st.components.v1.html(roulette_html, height=180)
            time.sleep(4.5)
            st.session_state.animasyon_tamam = True
            st.rerun()

        # --- OYUNCU KARTI ---
        if st.session_state.rulet_winner and st.session_state.animasyon_tamam:
            p = st.session_state.rulet_winner
            f_check = supabase.table("favoriler").select("oyuncu_adi").eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
            is_fav = len(f_check.data) > 0
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            card_color = "#22c55e" if is_fav else ("#f2cc60" if user_is_vip else "#ef4444")
            
            st.markdown(f"""
            <div style="background: #111; border: 2px solid {card_color}; border-radius: 20px; padding: 25px; margin-top:20px; position:relative; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                <div style="position:absolute; top:15px; right:15px; text-align:right;">
                    <span style="background:{card_color}; color:#000; padding:2px 8px; border-radius:5px; font-weight:bold; font-size:12px;">{"⭐ FAVORİNDE" if is_fav else "🎰 RULET SONUCU"}</span><br>
                    <span style="color:#fff; font-weight:bold; font-size:18px; display:block; margin-top:5px;">PA: {p['pa']}</span>
                </div>
                <h3 style="margin:0; font-size:22px; color:#fff;">{p['oyuncu_adi']}</h3>
                <hr style="border-top:1px solid #333; margin:15px 0;">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; color:#ccc; font-size:14px;">
                    <div>🌍 <b>Ülke:</b> {p.get('ulke','-')}</div>
                    <div>🏟️ <b>Kulüp:</b> {p.get('kulup','Serbest')}</div>
                    <div>👟 <b>Mevki:</b> {p.get('mevki','-')}</div>
                    <div>🎂 <b>Yaş:</b> {p.get('yas','-')}</div>
                    <div style="grid-column: span 2; color:#00ff41; font-weight:bold; font-size:16px; margin-top:5px;">💰 Değer: {p.get('deger','-')}</div>
                </div>
                <div style="margin-top:20px;">
                    <a href="{tm_url}" target="_blank" style="text-decoration:none; color:#58a6ff; font-weight:bold; font-size:13px;">Transfermarkt Profili ➔</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not is_fav:
                if st.button("⭐ FAVORİLERİME EKLE", key=f"fav_btn_rulet_{p['oyuncu_adi']}", use_container_width=True):
                    supabase.table("favoriler").insert({"oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup','Serbest'), "pa": p['pa'], "mevki": p['mevki'], "kullanici_adi": curr_user}).execute()
                    st.toast("Mermi listeye eklendi!")
                    st.rerun()
            else:
                st.info("✅ Bu oyuncu zaten favori listende patron.")
    else:
        st.warning("⚠️ Kriterlere uygun ucuz wonderkid bulunamadı. Tekrar dene!")

# # --- 3. İLK 11 (V180 - UNLIMITED SEARCH ENGINE) ---
with tabs[2]:
    st.markdown('<h2 style="text-align:center;">🏟️ ELITE ARENA - TAKTİK TAHTASI</h2>', unsafe_allow_html=True)
    
    curr_user = st.session_state.get('user')
    
    # --- DİNAMİK ARAMA MOTORU ---
    def get_player_options(label, key):
        # Önce favorileri çekiyoruz
        fav_res = supabase.table("favoriler").select("oyuncu_adi, pa").eq("kullanici_adi", curr_user).execute()
        fav_list = [f"⭐ {p['oyuncu_adi']} ({p['pa']})" for p in fav_res.data] if fav_res.data else []
        
        # Kullanıcı arama kutusuna bir şey yazdıysa veritabanında tüm 469 bin kişi içinde ara
        search_input = st.text_input(f"🔍 {label} Ara:", placeholder="Örn: Uğurcan, Onana...", key=f"search_{key}")
        
        pool = ["Boş Slot"] + fav_list
        
        if search_input and len(search_input) > 1:
            # 469 bin oyuncu içinde ilike araması yap (Limit 50 yeterli, zaten ismi yazınca çıkar)
            search_res = supabase.table("oyuncular").select("oyuncu_adi, pa").ilike("oyuncu_adi", f"%{search_input}%").limit(50).execute()
            if search_res.data:
                pool += [f"{p['oyuncu_adi']} ({p['pa']})" for p in search_res.data]
        
        return st.selectbox(f"📋 {label} Seç:", pool, key=f"tact_{key}")

    tactic = st.selectbox("🏟️ Ana Diziliş Seç:", 
                         ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "5-3-2", "5-4-1", "3-4-3", "4-1-2-1-2"], key="tactic_sel")
    
    st.info("💡 Oyuncuları 'Ara' kutusuna yazıp alttaki listeden seçin. Sahada beliren isimleri özgürce sürükleyebilirsiniz!")

    positions = []
    
    # --- DİZİLİŞ VE KOORDİNAT SİSTEMİ ---
    if tactic == "4-4-2":
        c1, c2, c3, c4, c5 = st.columns(5)
        gk = get_player_options("KL", "gk"); lb = get_player_options("SLB", "lb"); cb1 = get_player_options("STP1", "cb1"); cb2 = get_player_options("STP2", "cb2"); rb = get_player_options("SĞB", "rb")
        m1, m2, m3, m4 = st.columns(4)
        lm = get_player_options("SLK", "lm"); cm1 = get_player_options("MZS1", "cm1"); cm2 = get_player_options("MZS2", "cm2"); rm = get_player_options("SĞK", "rm")
        f1, f2 = st.columns(2)
        st1 = get_player_options("FRV1", "st1"); st2 = get_player_options("FRV2", "st2")
        positions = [("KL",gk,82,39), ("SLB",lb,65,2), ("STP",cb1,65,26), ("STP",cb2,65,51), ("SĞB",rb,65,75), ("SLK",lm,40,2), ("MZS",cm1,40,26), ("MZS",cm2,40,51), ("SĞK",rm,40,75), ("FRV",st1,13,26), ("FRV",st2,13,51)]

    elif tactic == "5-3-2":
        c1, c2, c3, c4, c5 = st.columns(5)
        gk = get_player_options("KL", "gk"); lb = get_player_options("SLB", "lb"); cb1 = get_player_options("STP1", "cb1"); cb2 = get_player_options("STP2", "cb2"); cb3 = get_player_options("STP3", "cb3"); rb = get_player_options("SĞB", "rb")
        m1, m2, m3 = st.columns(3)
        cm1 = get_player_options("MZS1", "cm1"); cdm = get_player_options("ÖNL", "cdm"); cm2 = get_player_options("MZS2", "cm2")
        f1, f2 = st.columns(2)
        st1 = get_player_options("FRV1", "st1"); st2 = get_player_options("FRV2", "st2")
        positions = [("KL",gk,85,39), ("SLB",lb,68,2), ("STP",cb1,70,22), ("STP",cb2,70,39), ("STP",cb3,70,56), ("SĞB",rb,68,75), ("MZS",cm1,45,15), ("ÖNL",cdm,52,39), ("MZS",cm2,45,63), ("FRV",st1,15,26), ("FRV",st2,15,51)]

    elif tactic == "3-4-3":
        c1, c2, c3, c4 = st.columns(4)
        gk = get_player_options("KL", "gk"); cb1 = get_player_options("STP1", "cb1"); cb2 = get_player_options("STP2", "cb2"); cb3 = get_player_options("STP3", "cb3")
        m1, m2, m3, m4 = st.columns(4)
        lm = get_player_options("SLK", "lm"); cm1 = get_player_options("MZS1", "cm1"); cm2 = get_player_options("MZS2", "cm2"); rm = get_player_options("SĞK", "rm")
        f1, f2, f3 = st.columns(3)
        lw = get_player_options("SLFOR", "lw"); st1 = get_player_options("FRV", "st1"); rw = get_player_options("SĞFOR", "rw")
        positions = [("KL",gk,85,39), ("STP",cb1,72,15), ("STP",cb2,72,39), ("STP",cb3,72,63), ("SLK",lm,45,2), ("MZS",cm1,48,26), ("MZS",cm2,48,51), ("SĞK",rm,45,75), ("SLFOR",lw,15,10), ("FRV",st1,12,39), ("SĞFOR",rw,15,68)]

    else: # Default 4-3-3 ve diğerleri
        c1, c2, c3, c4, c5 = st.columns(5)
        gk = get_player_options("KL", "gk"); lb = get_player_options("SLB", "lb"); cb1 = get_player_options("STP1", "cb1"); cb2 = get_player_options("STP2", "cb2"); rb = get_player_options("SĞB", "rb")
        m1, m2, m3 = st.columns(3)
        cm1 = get_player_options("MZS1", "cm1"); cm2 = get_player_options("MZS2", "cm2"); cm3 = get_player_options("MZS3", "cm3")
        f1, f2, f3 = st.columns(3)
        lw = get_player_options("SLFOR", "lw"); st1 = get_player_options("FRV", "st1"); rw = get_player_options("SĞFOR", "rw")
        positions = [("KL",gk,82,39), ("SLB",lb,65,2), ("STP",cb1,65,26), ("STP",cb2,65,51), ("SĞB",rb,65,75), ("MZS",cm1,43,10), ("MZS",cm2,43,38), ("MZS",cm3,43,66), ("SLFOR",lw,14,5), ("FRV",st1,11,38), ("SĞFOR",rw,14,71)]

    # --- HTML & SÜRÜKLEME MOTORU ---
    players_divs = "".join([f'<div class="player draggable" style="top:{y}%; left:{x}%;" onmousedown="startDrag(event)" ontouchstart="startDrag(event)"><div class="pos">{p}</div><div class="name">{n.split(" (")[0].replace("⭐ ", "")}</div></div>' for p, n, y, x in positions])

    tahta_html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <div id="capture" style="position:relative; background:#1e4620; border:4px solid #ffffff; border-radius:15px; width:360px; height:540px; margin:auto; overflow:hidden;">
        <div style="position:absolute; top:50%; left:0; width:100%; border-top:2px solid rgba(255,255,255,0.4);"></div>
        <div style="position:absolute; top:40%; left:30%; width:40%; height:20%; border:2px solid rgba(255,255,255,0.4); border-radius:50%;"></div>
        {players_divs}
        <div style="position:absolute; bottom:5px; right:10px; color:rgba(255,255,255,0.3); font-size:9px; font-weight:bold;">SOMEKU ELITE SCOUT</div>
    </div>
    
    <button onclick="downloadImage()" style="width:100%; padding:14px; background:#238636; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:15px;">📸 KADROYU PNG OLARAK KAYDET</button>

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
            activeEl.style.left = Math.max(0, Math.min(x, 80)) + "%";
            activeEl.style.top = Math.max(0, Math.min(y, 90)) + "%";
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
        .player {{ position:absolute; background:rgba(13,17,23,0.95); border:1.5px solid #58a6ff; border-radius:6px; color:white; width:75px; padding:3px; text-align:center; cursor:grab; z-index:100; user-select:none; touch-action:none; }}
        .pos {{ font-size:8px; color:#58a6ff; font-weight:bold; pointer-events:none; }}
        .name {{ font-size:9px; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; pointer-events:none; }}
    </style>
    """
    st.components.v1.html(tahta_html, height=650)

# --- 4. FAVORİLER (KİŞİYE ÖZEL) ---
with tabs[3]:
    st.markdown('<h2 style="text-align:center;">⭐ SENİN FAVORİLERİN</h2>', unsafe_allow_html=True)
    
    # KRİTİK: Sadece giriş yapan kullanıcıya (st.session_state.user) ait olanları çek!
    res = supabase.table("favoriler")\
        .select("*")\
        .eq("kullanici_adi", st.session_state.user)\
        .order("created_at", desc=True)\
        .execute()
        
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
        
        
# --- 5. BARROW AI (V730 - BAKIM MODU) ---
with tabs[5]:
    st.markdown('<div style="text-align:center; padding:100px 0;">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#ef4444; font-size:60px;">🤵</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#fff;">BARROW AI BAKIMDA</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color:#8b949e; font-size:18px;">Patron sistemi bakıma aldı. Barrow çok yakında mermi gibi filtrelerle geri dönecek!</p>', unsafe_allow_html=True)
    st.markdown('<div style="background:#1a1a1a; color:#facc15; padding:10px; border-radius:10px; display:inline-block; border:1px solid #facc15;">⏳ ÇOK YAKINDA YAYINDA</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)



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
        
