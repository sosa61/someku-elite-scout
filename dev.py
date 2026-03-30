import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re
import streamlit.components.v1 as components
import datetime
import unicodedata

# --- BAĞLANTI AYARLARI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

# --- SAYFA AYARLARI --
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- 🔄 VIP TAZELEME MOTORU (KESİN ÇÖZÜM) ---
if "user" in st.session_state and st.session_state.user:
    try:
        import datetime # Burada tanımlı olduğundan emin oluyoruz
        v_res = supabase.table("users").select("is_vip, last_barrow_date").eq("username", st.session_state.user).execute()
        if v_res.data:
            u_info = v_res.data[0]
            db_date_str = u_info.get('last_barrow_date')
            
            # VIP durumu veritabanından alınıyor
            is_vip_db = u_info.get('is_vip', False)
            
            if db_date_str and is_vip_db:
                clean_date_str = str(db_date_str).split(" ")[0]
                bitis_dt = datetime.datetime.strptime(clean_date_str, "%Y-%m-%d").date()
                bugun = datetime.date.today()
                
                if bugun <= bitis_dt:
                    st.session_state['is_vip'] = True
                    st.session_state['vip_kalan_gun'] = (bitis_dt - bugun).days
                else:
                    # Süresi dolmuşsa otomatik kapat
                    supabase.table("users").update({"is_vip": False}).eq("username", st.session_state.user).execute()
                    st.session_state['is_vip'] = False
                    st.session_state['vip_kalan_gun'] = 0
            else:
                st.session_state['is_vip'] = is_vip_db
                st.session_state['vip_kalan_gun'] = 0
    except Exception as e:
        st.session_state['is_vip'] = False


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

# --- OTURUM AYARLARI ---
if 'page' not in st.session_state: st.session_state.page = 0
if 'user' not in st.session_state: st.session_state.user = None
if 'is_vip' not in st.session_state: st.session_state.is_vip = False
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

query_user = st.query_params.get("user", None)
if query_user and st.session_state.user is None:
    st.session_state.user = query_user

# --- GİRİŞ VE KAYIT ---
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
                    data = {"username": new_user, "email": new_email, "password": new_pw, "is_vip": False, "puan": 0}
                    supabase.table("users").insert(data).execute()
                    st.success("✅ Kayıt başarılı! Yukarıdan giriş yapabilirsin.")
            else:
                st.warning("⚠️ Lütfen tüm alanları doldur!")
    st.stop()

# --- YAN MENÜ ---
with st.sidebar:
    st.markdown(f"### 👤 Hoş geldin, {st.session_state.user}")
    if st.session_state.get('is_vip'):
        kalan_gun = st.session_state.get('vip_kalan_gun', 0)
        st.success(f"🌟 VIP SCOUT ÜYESİ\n\n💎 Kalan: {kalan_gun} Gün")
    else:
        st.warning("🔴 STANDART ÜYE")
        st.info("Kilitli mermileri görmek için VIP üyeliğe geç!")
    st.markdown("---")
    if st.button("🚪 Güvenli Çıkış Yap", use_container_width=True):
        st.session_state.user = None
        st.session_state.is_vip = False
        st.query_params.clear()
        st.rerun()

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

# --- 2. RULET ---
with tabs[1]:
    import json
    st.markdown('<h2 style="text-align:center;">🎰 SCOUT RULETİ</h2>', unsafe_allow_html=True)
    user_is_vip = st.session_state.get('is_vip', False)
    if user_is_vip:
        st.markdown('<div style="text-align:center; padding:10px; background:#f2cc60; color:black; border-radius:15px; font-weight:bold; margin-bottom:15px;">🌟 ALTIN RULET MODU AKTİF (PA 155-200)</div>', unsafe_allow_html=True)
        min_pa, max_pa, slot_border = 155, 200, "#f2cc60"
    else:
        st.markdown('<div style="text-align:center; padding:10px; background:#30363d; color:white; border-radius:15px; margin-bottom:15px;">🎰 STANDART RULET (PA 130-150)</div>', unsafe_allow_html=True)
        min_pa, max_pa, slot_border = 130, 150, "#30363d"
    
    if 'rulet_winner' not in st.session_state: st.session_state.rulet_winner = None
    if 'animasyon_tamam' not in st.session_state: st.session_state.animasyon_tamam = False

    try:
        r_offset = random.randint(0, 150) 
        res = supabase.table("oyuncular").select("*").gte("pa", min_pa).lte("pa", max_pa).range(r_offset, r_offset + 80).execute()
        player_pool = res.data if res.data else []
        if player_pool: random.shuffle(player_pool)
    except: player_pool = []

    if player_pool:
        if st.button("🎰 RULETİ ÇEVİR", key="rulet_spin_btn", use_container_width=True):
            strip_players = [random.choice(player_pool) for _ in range(30)]
            winner = random.choice(player_pool)
            st.session_state.rulet_winner, st.session_state.animasyon_tamam = winner, False
            strip_players[25] = winner
            players_json = json.dumps(strip_players)
            roulette_html = f"""<div style="position:relative; width:100%; height:160px; background:#0d1117; border:3px solid {slot_border}; border-radius:15px; overflow:hidden; display:flex; justify-content:center; align-items:center;"><div style="position:absolute; width:100%; height:60px; border-top:2px solid {slot_border}; border-bottom:2px solid {slot_border}; background:rgba(242, 204, 96, 0.05); z-index:10;"></div><div id="slot-track" style="display:flex; flex-direction:column; position:absolute; top:0; transition: top 4s cubic-bezier(0.1, 0, 0.1, 1); width:100%;"></div></div><script>(function() {{ const players = {players_json}; const track = document.getElementById('slot-track'); const itemH = 60; const contH = 160; const winI = 25; track.innerHTML = players.map((p, i) => `<div style="height:${{itemH}}px; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center;"><small style="color:#8b949e; font-size:10px;">${{p.kulup || 'Scout Agent'}}</small><b style="color:white; font-size:13px;">${{p.oyuncu_adi}}</b></div>`).join(''); setTimeout(() => {{ track.style.top = "-" + ((winI * itemH) - (contH / 2 - itemH / 2)) + "px"; }}, 100); }})();</script>"""
            components.html(roulette_html, height=180)
            time.sleep(4.5)
            st.session_state.animasyon_tamam = True
            st.rerun()

        if st.session_state.rulet_winner and st.session_state.animasyon_tamam:
            p = st.session_state.rulet_winner
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            card_color = "#f2cc60" if user_is_vip else "#238636"
            st.markdown(f'<div style="background: rgba(255,255,255,0.03); border: 2px solid {card_color}; border-radius: 20px; padding: 20px; text-align:center;"><h3 style="margin:0; font-size:20px;">{p["oyuncu_adi"]}</h3><p style="color:{card_color}; font-weight:bold;">{p["mevki"]} | PA: {p["pa"]}</p><a href="{tm_url}" target="_blank" style="text-decoration:none; color:#58a6ff; font-size:12px;">Transfermarkt Profili ➔</a></div>', unsafe_allow_html=True)
            if st.button("⭐ FAVORİLERİME EKLE", key=f"fav_btn_rulet_{p['oyuncu_adi']}", use_container_width=True):
                supabase.table("favoriler").insert({"oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup','Serbest'), "pa": p['pa'], "mevki": p['mevki'], "kullanici_adi": st.session_state.user}).execute()
                st.success("✅ Mermi listeye eklendi!")

# --- 3. İLK 11 ---
with tabs[2]:
    st.markdown('<h2 style="text-align:center;">🏟️ ELITE ARENA - TAKTİK TAHTASI</h2>', unsafe_allow_html=True)
    res_fav = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).order("pa", desc=True).execute()
    f_n = [f"{p['oyuncu_adi']} ({p['pa']})" for p in res_fav.data] if res_fav.data else ["Favori Mermi Yok"]
    tactic = st.selectbox("🏟️ Ana Diziliş Seç:", ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2"], key="tactic_sel")
    
    st.markdown('<div style="color:#58a6ff; font-weight:bold; font-size:12px;">🛡️ DEFANS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    gk, lb, cb1, cb2, rb = c1.selectbox("GK", f_n), c2.selectbox("LB", f_n), c3.selectbox("CB1", f_n), c4.selectbox("CB2", f_n), c5.selectbox("RB", f_n)
    
    if tactic == "4-4-2":
        m1, m2, m3, m4 = st.columns(4); lm, cm1, cm2, rm = m1.selectbox("LM", f_n), m2.selectbox("CM1", f_n), m3.selectbox("CM2", f_n), m4.selectbox("RM", f_n)
        f1, f2 = st.columns(2); st1, st2 = f1.selectbox("ST1", f_n), f2.selectbox("ST2", f_n)
        positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("LM",lm,40,2), ("CM",cm1,40,26), ("CM",cm2,40,51), ("RM",rm,40,75), ("ST",st1,13,26), ("ST",st2,13,51)]
    elif tactic == "4-2-3-1":
        m1, m2, m3, m4, m5 = st.columns(5); dm1, dm2, aml, amc, amr = m1.selectbox("CDM1", f_n), m2.selectbox("CDM2", f_n), m3.selectbox("LAM", f_n), m4.selectbox("CAM", f_n), m5.selectbox("RAM", f_n)
        st1 = st.selectbox("ST", f_n); positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("DM",dm1,52,26), ("DM",dm2,52,51), ("AM",aml,28,5), ("AM",amc,25,39), ("AM",amr,28,72), ("ST",st1,8,39)]
    else: # 4-3-3
        m1, m2, m3 = st.columns(3); cm1, cm2, cm3 = m1.selectbox("LCM", f_n), m2.selectbox("CM", f_n), m3.selectbox("RCM", f_n)
        f1, f2, f3 = st.columns(3); lw, st_p, rw = f1.selectbox("LW", f_n), f2.selectbox("ST", f_n), f3.selectbox("RW", f_n)
        positions = [("GK",gk,82,39), ("LB",lb,65,2), ("CB",cb1,65,26), ("CB",cb2,65,51), ("RB",rb,65,75), ("CM",cm1,43,10), ("CM",cm2,43,38), ("CM",cm3,43,66), ("LW",lw,14,5), ("ST",st_p,11,38), ("RW",rw,14,71)]

    players_divs = "".join([f'<div class="player draggable" style="top:{y}%; left:{x}%;" onmousedown="startDrag(event)" ontouchstart="startDrag(event)"><div class="pos">{p}</div><div class="name">{n}</div></div>' for p, n, y, x in positions])
    tahta_html = f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script><div id="capture" style="position:relative; background:#1e4620; border:4px solid #ffffff; border-radius:15px; width:360px; height:540px; margin:auto; overflow:hidden;"><div style="position:absolute; top:50%; left:0; width:100%; border-top:2px solid rgba(255,255,255,0.4);"></div>{players_divs}</div><button onclick="downloadImage()" style="width:100%; padding:12px; background:#238636; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:15px;">📸 PNG KAYDET</button><script>let activeEl = null; function startDrag(e) {{ activeEl = e.target.closest('.draggable'); document.onmousemove = drag; document.ontouchmove = drag; document.onmouseup = endDrag; document.ontouchend = endDrag; }} function drag(e) {{ if (!activeEl) return; e.preventDefault(); let clientX = e.clientX || e.touches[0].clientX; let clientY = e.clientY || e.touches[0].clientY; let rect = document.getElementById('capture').getBoundingClientRect(); let x = ((clientX - rect.left - 39) / rect.width) * 100; let y = ((clientY - rect.top - 20) / rect.height) * 100; activeEl.style.left = x + "%"; activeEl.style.top = y + "%"; }} function endDrag() {{ activeEl = null; }} function downloadImage() {{ html2canvas(document.querySelector("#capture")).then(canvas => {{ let link = document.createElement('a'); link.download = 'mermi-kadro.png'; link.href = canvas.toDataURL(); link.click(); }}); }}</script><style>.player {{ position:absolute; background:rgba(13,17,23,0.9); border:1.5px solid #58a6ff; border-radius:8px; color:white; width:78px; padding:4px; text-align:center; cursor:grab; z-index:100; user-select:none; touch-action:none; }} .pos {{ font-size:9px; color:#58a6ff; font-weight:bold; pointer-events:none; }} .name {{ font-size:10px; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; pointer-events:none; }}</style>"""
    components.html(tahta_html, height=630)

# --- 4. FAVORİLER ---
with tabs[3]:
    st.markdown('<h2 style="text-align:center;">⭐ KALICI FAVORİLERİN</h2>', unsafe_allow_html=True)
    res = supabase.table("favoriler").select("*").eq("kullanici_adi", st.session_state.user).order("created_at", desc=True).execute()
    if res.data:
        for p in res.data:
            st.markdown(f'<div style="background: rgba(255,255,255,0.05); border-left: 5px solid #238636; border-radius: 10px; padding: 15px; margin-bottom: 10px;"><div style="display: flex; justify-content: space-between; align-items: center;"><div><h4 style="margin:0; color: white;">{p["oyuncu_adi"]}</h4><small style="color: #8b949e;">🏟️ {p.get("kulup", "Serbest")} | 📍 {p.get("mevki", "-")}</small></div><div style="text-align: right;"><span style="background: #238636; color: white; padding: 2px 8px; border-radius: 5px; font-size: 12px;">PA: {p["pa"]}</span></div></div></div>', unsafe_allow_html=True)
            if st.button(f"🗑️ Sil: {p['oyuncu_adi']}", key=f"del_{p['id']}"):
                supabase.table("favoriler").delete().eq("id", p['id']).execute(); st.rerun()
    else: st.info("Henüz favori mermin yok.")

# --- 5. GİZLİ YETENEK AVI ---
with tabs[4]:
    st.markdown('<h2 style="text-align:center; color:#f2cc60;">🕵️ GİZLİ YETENEK AVI</h2>', unsafe_allow_html=True)
    def metin_temizle(metin):
        if not metin: return ""
        metin = str(metin).lower().replace('ı', 'i').replace('İ', 'i')
        return "".join([c for c in unicodedata.normalize('NFKD', metin) if not unicodedata.combining(c)])

    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'target_p' not in st.session_state: st.session_state.target_p = None

    if st.button("🚀 YENİ AV BAŞLAT", use_container_width=True):
        res_g = supabase.table("oyuncular").select("*").not_.eq("kulup", "None").gte("pa", 165).limit(500).execute()
        if res_g.data:
            st.session_state.target_p, st.session_state.game_active, st.session_state.game_start_time = random.choice(res_g.data), True, time.time()
            st.rerun()

    if st.session_state.game_active and st.session_state.target_p:
        p, kalan = st.session_state.target_p, max(0, int(30 - (time.time() - st.session_state.game_start_time)))
        if kalan > 0:
            st.markdown(f'<div style="background:#161b22; padding:20px; border-radius:15px; text-align:center;"><h3>⏳ {kalan}s</h3><p>{p["yas"]} Yaş | {p["kulup"]}</p></div>', unsafe_allow_html=True)
            tahmin = st.text_input("Tahmin:", key="scout_input").strip()
            if tahmin and metin_temizle(tahmin) in metin_temizle(p['oyuncu_adi']):
                st.session_state.game_active = False; st.balloons(); st.success(f"🎯 BİLDİN! {p['oyuncu_adi']}"); st.rerun()
            time.sleep(1); st.rerun()
        else: st.error(f"⌛ SÜRE BİTTİ! {p['oyuncu_adi']}"); st.session_state.game_active = False

# --- 6. BARROW AI ---
with tabs[5]:
    st.markdown('<h1 style="color:#ef4444; text-align:center;">🤵 BARROW AI</h1>', unsafe_allow_html=True)
    can_ask = True
    if not st.session_state.is_vip:
        u_data = supabase.table("users").select("barrow_count, last_barrow_date").eq("username", st.session_state.user).execute()
        if u_data.data:
            if u_data.data[0].get('barrow_count', 0) >= 3 and u_data.data[0].get('last_barrow_date') == str(datetime.date.today()): can_ask = False
    
    b_in = st.text_input("Barrow'a emir ver:", disabled=not can_ask)
    if st.button("BARROWA SOR", disabled=not can_ask) and b_in:
        res_b = supabase.table("oyuncular").select("*").gte("pa", 140).limit(100).execute()
        if res_b.data:
            p = random.choice(res_b.data)
            st.markdown(f'<div style="background:#000; border:2px solid #ef4444; padding:20px; border-radius:15px;"><h2>{p["oyuncu_adi"]}</h2><p>PA: {p["pa"]} | {p["mevki"]}</p></div>', unsafe_allow_html=True)
            if not st.session_state.is_vip: supabase.table("users").update({"barrow_count": u_data.data[0]['barrow_count']+1, "last_barrow_date": str(datetime.date.today())}).eq("username", st.session_state.user).execute()

# --- 7. ADMIN ---
with tabs[6]:
    if st.session_state.user == "someku":
        st.write("### 👥 VIP Yönetimi")
        u_list = supabase.table("users").select("*").execute()
        for u in u_list.data:
            c1, c2, c3 = st.columns([2,2,1])
            c1.write(u['username'])
            t_date = c2.date_input("Bitiş:", key=f"adm_{u['username']}")
            if c3.button("YETKİ VER", key=f"btn_{u['username']}"):
                supabase.table("users").update({"is_vip": True, "last_barrow_date": str(t_date)}).eq("username", u['username']).execute(); st.rerun()
    else: st.warning("Yetkiniz yok.")
