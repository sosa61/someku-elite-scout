import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
import datetime



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
        # Veritabanından tüm bilgileri çekiyoruz
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


# --- 1. SCOUT (V173 - TAM ÇALIŞAN FİLTRE MOTORU) ---
with tabs[0]:
    import urllib.parse
    POS_TR = {"Hepsi": "Hepsi", "Kaleci": "GK", "Stoper": "D C", "Sol Bek": "D L", "Sağ Bek": "D R", "Ön Libero": "DM", "Merkez Orta Saha": "M C", "Sol Kanat": "AM L", "Sağ Kanat": "AM R", "Ofansif Orta Saha": "AM C", "Forvet": "ST"}
    REG_TR = {"Hepsi": [], "Avrupa": ["Türkiye", "Almanya", "Fransa", "İngiltere", "İtalya", "İspanya", "Hollanda", "Portekiz", "Belçika"], "Kuzey Avrupa": ["Norveç", "İsveç", "Danimarka", "Finlandiya", "İzlanda"], "Balkanlar": ["Hırvatistan", "Sırbistan", "Yunanistan", "Bulgaristan", "Slovenya", "Bosna Hersek"], "Güney Amerika": ["Brezilya", "Arjantin", "Uruguay", "Kolombiya", "Ekvador"], "Afrika": ["Nijerya", "Senegal", "Mısır", "Fildişi Sahili", "Fas", "Cezayir"], "Asya": ["Japonya", "Güney Kore", "Suudi Arabistan", "Katar", "Avustralya", "Çin"]}
    
    curr_user = st.session_state.get('user')
    
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
    
    if "page" not in st.session_state: st.session_state.page = 0
    
    # Favorileri Taze Çek
    f_res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", curr_user).execute()
    st.session_state.fav_list = [x['oyuncu_adi'] for x in f_res.data] if f_res.data else []

    # --- 🚀 DİNAMİK SORGULAMA MOTORU ---
    # Temel sorgu (Yaş ve PA her zaman var)
    query = supabase.table("oyuncular").select("*").gte("yas", age_f[0]).lte("yas", age_f[1]).gte("pa", pa_f[0]).lte("pa", pa_f[1])
    
    # Filtreler doluysa sorguya ekle
    if name_f: 
        query = query.ilike("oyuncu_adi", f"%{name_f}%")
    if team_f: 
        query = query.ilike("kulup", f"%{team_f}%")
    if country_f:
        query = query.ilike("ulke", f"%{country_f}%")
    if pos_f != "Hepsi": 
        query = query.ilike("mevki", f"%{POS_TR[pos_f]}%")
    if reg_f != "Hepsi":
        # Seçilen bölgedeki ülkeleri "in" filtresiyle ekle
        query = query.in_("ulke", REG_TR[reg_f])
    
    # Sıralama ve Sayfalama (Filtrelenmiş 'query' üzerinden devam ediyoruz)
    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        user_is_vip = st.session_state.get('is_vip', False)

        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            pa_val = p.get("pa", 0)

            with cols[i%2]:
                if pa_val > 150 and user_is_vip is False:
                    st.markdown(f'''
                    <div style="padding:15px; border-radius:12px; margin-bottom:10px; border: 2px dashed #f2cc60; background: rgba(242, 204, 96, 0.05); text-align:center;">
                        <span style="background:#f2cc60; color:black; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:bold;">💎 ELİT YETENEK KİLİTLİ</span>
                        <h4 style="margin:10px 0; color:#8b949e;">🔒 Gizli Yıldız</h4>
                        <p style="font-size:12px; color:#8b949e;">PA: <b>{pa_val}</b> olan bu oyuncu sadece VIP Scoutlara özeldir.</p>
                        <a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="display:inline-block; background:#238636; color:white; padding:8px 15px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:13px;">KİLİDİ AÇ</a>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    card_style = "border: 2px solid #238636; background: rgba(35, 134, 54, 0.05);" if is_fav else "border: 1px solid #30363d;"
                    st.markdown(f'''
                    <div style="padding:15px; border-radius:12px; margin-bottom:10px; {card_style} position:relative;">
                        <span style="position:absolute; top:10px; right:10px; background:#238636; color:white; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:bold;">PA: {p["pa"]}</span>
                        <h4 style="margin:0;">{p["oyuncu_adi"]}</h4>
                        <p style="font-size:11px; color:#8b949e; margin:5px 0;">🏟️ {p.get("kulup","Serbest")} | 👟 {p["mevki"]}</p>
                        <a href="{tm_url}" target="_blank" style="color:#58a6ff; font-size:11px; text-decoration:none;">Transfermarkt ➔</a>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    btn_txt = "⭐ FAVORİDEN ÇIKAR" if is_fav else "☆ FAVORİLERE EKLE"
                    if st.button(btn_txt, key=f"v173_btn_{p['oyuncu_adi']}_{i}", use_container_width=True):
                        if is_fav:
                            supabase.table("favoriler").delete().eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
                            st.session_state.fav_list.remove(p['oyuncu_adi'])
                        else:
                            supabase.table("favoriler").insert({
                                "oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup', 'Serbest'), 
                                "pa": p['pa'], "mevki": p['mevki'], "ca": p.get('ca', 0),
                                "kullanici_adi": curr_user 
                            }).execute()
                            st.session_state.fav_list.append(p['oyuncu_adi'])
                        st.rerun()

        st.markdown("---")
        c1, c2, c3 = st.columns([1, 2, 1])
        if c1.button("⬅️ Geri", use_container_width=True) and st.session_state.page > 0:
            st.session_state.page -= 1; st.rerun()
        with c2: st.markdown(f"<p style='text-align:center;'>Sayfa: {st.session_state.page + 1}</p>", unsafe_allow_html=True)
        if c3.button("İleri ➡️", use_container_width=True):
            st.session_state.page += 1; st.rerun()
    else:
        st.warning("Aradığın kriterlerde mermi bulunamadı hıyarto! Filtreleri biraz gevşet.")

    res = query.order(sort_f, desc=True).range(st.session_state.page*12, (st.session_state.page*12)+11).execute()
    
    if res.data:
        cols = st.columns(2)
        user_is_vip = st.session_state.get('is_vip', False)

        for i, p in enumerate(res.data):
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            pa_val = p.get("pa", 0)

            with cols[i%2]:
                if pa_val > 150 and user_is_vip is False:
                    st.markdown(f'''
                    <div style="padding:15px; border-radius:12px; margin-bottom:10px; border: 2px dashed #f2cc60; background: rgba(242, 204, 96, 0.05); text-align:center;">
                        <span style="background:#f2cc60; color:black; padding:2px 8px; border-radius:5px; font-size:10px; font-weight:bold;">💎 ELİT YETENEK KİLİTLİ</span>
                        <h4 style="margin:10px 0; color:#8b949e;">🔒 Gizli Yıldız</h4>
                        <p style="font-size:12px; color:#8b949e;">PA: <b>{pa_val}</b> olan bu oyuncunun detayları için VIP üye olmalısın.</p>
                        <a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="display:inline-block; background:#238636; color:white; padding:8px 15px; border-radius:8px; text-decoration:none; font-weight:bold; font-size:13px;">KİLİDİ AÇ</a>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    card_style = "border: 2px solid #238636; background: rgba(35, 134, 54, 0.05);" if is_fav else "border: 1px solid #30363d;"
                    st.markdown(f'''
                    <div style="padding:15px; border-radius:12px; margin-bottom:10px; {card_style} position:relative;">
                        <span style="position:absolute; top:10px; right:10px; background:#238636; color:white; padding:2px 8px; border-radius:5px; font-size:11px; font-weight:bold;">PA: {p["pa"]}</span>
                        <h4 style="margin:0;">{p["oyuncu_adi"]}</h4>
                        <p style="font-size:11px; color:#8b949e; margin:5px 0;">🏟️ {p.get("kulup","Serbest")} | 👟 {p["mevki"]}</p>
                        <a href="{tm_url}" target="_blank" style="color:#58a6ff; font-size:11px; text-decoration:none;">Transfermarkt ➔</a>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    btn_txt = "⭐ FAVORİDEN ÇIKAR" if is_fav else "☆ FAVORİLERE EKLE"
                    if st.button(btn_txt, key=f"v173_btn_{p['oyuncu_adi']}_{i}", use_container_width=True):
                        if is_fav:
                            # --- 🛡️ DÜZELTME: Sadece BU kullanıcının favorisini sil ---
                            supabase.table("favoriler").delete().eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
                            st.session_state.fav_list.remove(p['oyuncu_adi'])
                        else:
                            # --- 🛡️ DÜZELTME: Favoriye eklerken KULLANICIYI kaydet ---
                            supabase.table("favoriler").insert({
                                "oyuncu_adi": p['oyuncu_adi'], 
                                "kulup": p.get('kulup', 'Serbest'), 
                                "pa": p['pa'], 
                                "mevki": p['mevki'], 
                                "ca": p.get('ca', 0),
                                "kullanici_adi": curr_user 
                            }).execute()
                            st.session_state.fav_list.append(p['oyuncu_adi'])
                        st.rerun()

        c1, c2 = st.columns(2)
        if c1.button("⬅️ Geri", use_container_width=True) and st.session_state.page > 0:
            st.session_state.page -= 1; st.rerun()
        if c2.button("İleri ➡️", use_container_width=True):
            st.session_state.page += 1; st.rerun()

# --- 2. RULET (V187 - ZENGİN KART & KARIŞIK HAVUZ) ---
with tabs[1]:
    st.markdown('<h2 style="text-align:center;">🎰 SCOUT RULETİ</h2>', unsafe_allow_html=True)
    
    import random
    import json
    import time
    import urllib.parse

    user_is_vip = st.session_state.get('is_vip', False)
    curr_user = st.session_state.get('user')

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

    # --- KARIŞIK OYUNCU HAVUZU ÇEKME ---
    try:
        r_offset = random.randint(0, 150) 
        res = supabase.table("oyuncular").select("*")\
            .gte("pa", min_pa)\
            .lte("pa", max_pa)\
            .range(r_offset, r_offset + 90).execute()
        
        player_pool = res.data if res.data else []
        if player_pool:
            random.shuffle(player_pool) 
    except:
        player_pool = []

    if player_pool:
        btn_label = "🎰 ALTIN RULETİ ÇEVİR" if user_is_vip else "🎰 STANDART RULETİ ÇEVİR"
        if st.button(btn_label, use_container_width=True):
            strip_players = [random.choice(player_pool) for _ in range(30)]
            winner = random.choice(player_pool)
            
            st.session_state.rulet_winner = winner
            st.session_state.animasyon_tamam = False
            strip_players[25] = winner
            players_json = json.dumps(strip_players)
            
            roulette_html = f"""
            <div id="slot-container" style="position:relative; width:100%; height:160px; background:#0d1117; border:3px solid {slot_border}; border-radius:15px; overflow:hidden; display:flex; justify-content:center; align-items:center;">
                <div style="position:absolute; width:100%; height:60px; border-top:2px solid {slot_border}; border-bottom:2px solid {slot_border}; background:rgba(242, 204, 96, 0.05); z-index:10; pointer-events:none;"></div>
                <div id="slot-track" style="display:flex; flex-direction:column; position:absolute; top:0; transition: top 4s cubic-bezier(0.1, 0, 0.1, 1); width:100%;"></div>
            </div>
            <script>
                (function() {{
                    const players = {players_json};
                    const track = document.getElementById('slot-track');
                    const itemH = 60; const contH = 160; const winI = 25;
                    track.innerHTML = players.map((p, i) => `
                        <div id="si-${{i}}" style="height:${{itemH}}px; width:100%; display:flex; flex-direction:column; justify-content:center; align-items:center; transition: opacity 0.5s;">
                            <small style="color:#8b949e; font-size:10px;">${{p.kulup || 'Scout Agent'}}</small>
                            <b style="color:white; font-size:13px;">${{p.oyuncu_adi}}</b>
                        </div>
                    `).join('');
                    setTimeout(() => {{
                        const finalY = (winI * itemH) - (contH / 2 - itemH / 2);
                        track.style.top = "-" + finalY + "px";
                        setTimeout(() => {{
                            players.forEach((_, i) => {{ if(i !== winI) document.getElementById('si-'+i).style.opacity="0"; }});
                        }}, 4000);
                    }}, 100);
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
            
            raw_val = str(p.get('deger', ''))
            if "300.000.000" in raw_val:
                display_val = "❌ Satılık Değil"
            elif raw_val in ["0", "£0", "", "None"]:
                display_val = "💎 Paha Biçilemez"
            else:
                display_val = raw_val

            if not user_is_vip:
                st.info("💡 155-200 PA arası efsaneler için Altın Rulet'i açmalısın!")
                st.markdown(f'''<a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#f2cc60; color:black; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;">🌟 ALTIN RULETİ AÇ (VIP OL)</button></a>''', unsafe_allow_html=True)

            st.markdown("---")
            col_k, col_n = st.columns([1, 1.2])
            
            with col_k:
                card_color = "#f2cc60" if user_is_vip else "#238636"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); border: 2px solid {card_color}; border-radius: 20px; padding: 20px; text-align:center; backdrop-filter: blur(5px);">
                    <div style="font-size:40px; margin-bottom:10px;">👤</div>
                    <h3 style="margin:0; font-size:20px; color:white;">{p['oyuncu_adi']}</h3>
                    <p style="color:{card_color}; font-weight:bold; font-size:14px; margin-bottom:15px;">{p['mevki']}</p>
                    <div style="display:flex; justify-content:space-around; border-top:1px solid #30363d; padding-top:15px;">
                        <div><small style="display:block; color:#8b949e; font-size:10px;">YAŞ</small><b style="font-size:16px;">{p['yas']}</b></div>
                        <div><small style="display:block; color:#8b949e; font-size:10px;">POTANSİYEL</small><b style="color:{card_color}; font-size:16px;">{p['pa']}</b></div>
                    </div>
                    <a href="{tm_url}" target="_blank" style="text-decoration:none;">
                        <div style="background:#1a3151; color:white; border-radius:10px; padding:10px; margin-top:20px; font-size:12px; font-weight:bold;">🌐 TRANSFERMARKT PROFİLİ</div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

            with col_n:
                st.markdown(f"#### 🕵️ Scout Raporu")
                st.write(f"🌍 **Ülke:** {p.get('ulke', 'Bilinmiyor')}")
                st.write(f"🏟️ **Kulüp:** {p.get('kulup', 'Serbest')}")
                st.write(f"💰 **Piyasa Değeri:** {display_val}")
                st.write(f"📈 **CA (Mevcut):** {p.get('ca', '-')}")
                
                st.markdown("---")
                # FAVORİ BUTONU ARTIK DOĞRU YERDE (Girintisi düzeltildi)
                if st.button("⭐ FAVORİLERİME EKLE", use_container_width=True, key=f"rulet_fav_{p['oyuncu_adi']}"):
                    supabase.table("favoriler").insert({
                        "oyuncu_adi": p['oyuncu_adi'], 
                        "kulup": p.get('kulup', 'Serbest'), 
                        "pa": p['pa'], 
                        "mevki": p['mevki'], 
                        "ca": p.get('ca', '-'),
                        "kullanici_adi": curr_user
                    }).execute()
                    st.success("✅ Mermi senin listene eklendi!")
    else:
        st.warning("Kriterlere uygun mermi bulunamadı.")


# --- 3. İLK 11 (V163 - PNG VE METİN ÇIKTISI) ---
with tabs[2]:
    st.markdown('<h2 style="text-align:center;">🏟️ ELITE ARENA - KADRO KUR</h2>', unsafe_allow_html=True)
    
    # --- FAVORİLERİ ÇEK ---
    try:
        res_fav = supabase.table("favoriler").select("*").order("pa", desc=True).execute()
        f_n = [f"{p['oyuncu_adi']} ({p['pa']})" for p in res_fav.data] if res_fav.data else ["Henüz Favorin Yok"]
    except:
        f_n = ["Bağlantı Hatası"]

    tactic = st.selectbox("🏟️ Diziliş Seç:", ["4-4-2", "4-3-3"], key="tactic_sel")
    
    # --- OYUNCU SEÇİMLERİ ---
    st.markdown('<div style="color:#58a6ff; font-weight:bold; font-size:12px;">🛡️ DEFANS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    gk = c1.selectbox("GK", f_n, key="sl_gk"); lb = c2.selectbox("LB", f_n, key="sl_lb")
    cb1 = c3.selectbox("CB1", f_n, key="sl_cb1"); cb2 = c4.selectbox("CB2", f_n, key="sl_cb2"); rb = c5.selectbox("RB", f_n, key="sl_rb")

    st.markdown('<div style="color:#238636; font-weight:bold; font-size:12px;">⚡ HÜCUM</div>', unsafe_allow_html=True)
    if tactic == "4-4-2":
        m1, m2, m3, m4 = st.columns(4)
        lm = m1.selectbox("LM", f_n, key="sl_lm"); cm1 = m2.selectbox("CM1", f_n, key="sl_cm1")
        cm2 = m3.selectbox("CM2", f_n, key="sl_cm2"); rm = m4.selectbox("RM", f_n, key="sl_rm")
        f1, f2 = st.columns(2)
        st1 = f1.selectbox("ST1", f_n, key="sl_st1"); st2 = f2.selectbox("ST2", f_n, key="sl_st2")
        kadro_txt = f"Diziliş: 4-4-2\nGK: {gk}\nLB: {lb}\nCB: {cb1}\nCB: {cb2}\nRB: {rb}\nLM: {lm}\nCM: {cm1}\nCM: {cm2}\nRM: {rm}\nST: {st1}\nST: {st2}"
    else:
        m1, m2, m3 = st.columns(3)
        cm1 = m1.selectbox("LCM", f_n, key="sl_lcm"); cm2 = m2.selectbox("CM", f_n, key="sl_cmm"); cm3 = m3.selectbox("RCM", f_n, key="sl_rcm")
        f1, f2, f3 = st.columns(3)
        lw = f1.selectbox("LW", f_n, key="sl_lw"); st_p = f2.selectbox("ST", f_n, key="sl_st"); rw = f3.selectbox("RW", f_n, key="sl_rw")
        kadro_txt = f"Diziliş: 4-3-3\nGK: {gk}\nLB: {lb}\nCB: {cb1}\nCB: {cb2}\nRB: {rb}\nCM: {cm1}\nCM: {cm2}\nCM: {cm3}\nLW: {lw}\nST: {st_p}\nRW: {rw}"

    # --- GÖRSEL SAHA TASARIMI ---
    players_html = ""
    if tactic == "4-4-2":
        players_html = f"""
            <div class="player" style="top:84%; left:39%; border-color:#f2cc60;"><div class="pos">GK</div><div class="name">{gk}</div></div>
            <div class="player" style="top:67%; left:2%;"><div class="pos">LB</div><div class="name">{lb}</div></div>
            <div class="player" style="top:67%; left:26%;"><div class="pos">CB</div><div class="name">{cb1}</div></div>
            <div class="player" style="top:67%; left:51%;"><div class="pos">CB</div><div class="name">{cb2}</div></div>
            <div class="player" style="top:67%; left:75%;"><div class="pos">RB</div><div class="name">{rb}</div></div>
            <div class="player" style="top:40%; left:2%;"><div class="pos">LM</div><div class="name">{lm}</div></div>
            <div class="player" style="top:40%; left:26%;"><div class="pos">CM</div><div class="name">{cm1}</div></div>
            <div class="player" style="top:40%; left:51%;"><div class="pos">CM</div><div class="name">{cm2}</div></div>
            <div class="player" style="top:40%; left:75%;"><div class="pos">RM</div><div class="name">{rm}</div></div>
            <div class="player" style="top:13%; left:26%;"><div class="pos">ST</div><div class="name">{st1}</div></div>
            <div class="player" style="top:13%; left:51%;"><div class="pos">ST</div><div class="name">{st2}</div></div>
        """
    else:
        players_html = f"""
            <div class="player" style="top:84%; left:39%; border-color:#f2cc60;"><div class="pos">GK</div><div class="name">{gk}</div></div>
            <div class="player" style="top:67%; left:2%;"><div class="pos">LB</div><div class="name">{lb}</div></div>
            <div class="player" style="top:67%; left:26%;"><div class="pos">CB</div><div class="name">{cb1}</div></div>
            <div class="player" style="top:67%; left:51%;"><div class="pos">CB</div><div class="name">{cb2}</div></div>
            <div class="player" style="top:67%; left:75%;"><div class="pos">RB</div><div class="name">{rb}</div></div>
            <div class="player" style="top:43%; left:10%;"><div class="pos">CM</div><div class="name">{cm1}</div></div>
            <div class="player" style="top:43%; left:38%;"><div class="pos">CM</div><div class="name">{cm2}</div></div>
            <div class="player" style="top:43%; left:66%;"><div class="pos">CM</div><div class="name">{cm3}</div></div>
            <div class="player" style="top:14%; left:5%;"><div class="pos">LW</div><div class="name">{lw}</div></div>
            <div class="player" style="top:11%; left:38%;"><div class="pos">ST</div><div class="name">{st_p}</div></div>
            <div class="player" style="top:14%; left:71%;"><div class="pos">RW</div><div class="name">{rw}</div></div>
        """

    # PNG İndirme Scripti ve Saha HTML
    saha_html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <div id="capture" style="position:relative; background:#238636; border:3px solid #ffffff; border-radius:15px; width:360px; height:530px; margin:auto; overflow:hidden;">
        <div style="position:absolute; top:50%; left:0; width:100%; border-top:2px solid rgba(255,255,255,0.3);"></div>
        <div style="position:absolute; top:41%; left:30%; width:40%; height:18%; border:2px solid rgba(255,255,255,0.3); border-radius:50%;"></div>
        {players_html}
        <div style="position:absolute; bottom:5px; right:10px; color:rgba(255,255,255,0.4); font-size:9px; font-weight:bold;">SOMEKU ELITE SCOUT</div>
    </div>
    <div style="display:flex; gap:10px; margin-top:15px;">
        <button onclick="downloadImage()" style="flex:1; padding:10px; background:#238636; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">📸 RESİM (PNG) İNDİR</button>
    </div>
    <script>
        function downloadImage() {{
            html2canvas(document.querySelector("#capture")).then(canvas => {{
                let link = document.createElement('a');
                link.download = 'elite-kadro.png';
                link.href = canvas.toDataURL();
                link.click();
            }});
        }}
    </script>
    <style>
        .player {{ position:absolute; background:rgba(13,17,23,0.95); border:1.5px solid #58a6ff; border-radius:6px; color:white; width:78px; padding:3px; text-align:center; box-shadow:0 4px 10px rgba(0,0,0,0.5); }}
        .pos {{ font-size:8px; color:#58a6ff; font-weight:bold; }}
        .name {{ font-size:9px; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
    </style>
    """
    
    st.components.v1.html(saha_html, height=600)

    # --- METİN OLARAK İNDİR BUTONU ---
    st.download_button(
        label="📄 KADRO LİSTESİNİ (.TXT) İNDİR",
        data=kadro_txt,
        file_name="mermi-kadro-listesi.txt",
        mime="text/plain",
        use_container_width=True
    )

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
        
# --- 5. GİZLİ YETENEK AVI (V440 - HATA DÜZELTİLDİ) ---
with tabs[4]:
    import unicodedata
    st.markdown('<h2 style="text-align:center; color:#f2cc60;">🕵️ GİZLİ YETENEK AVI</h2>', unsafe_allow_html=True)
    
    # --- 1. FONKSİYONLAR ---
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

    def skor_yaz(user, artis):
        try:
            c = supabase.table("users").select("puan").eq("username", user).execute()
            eski = c.data[0].get("puan", 0) if c.data else 0
            yeni = max(0, eski + artis)
            supabase.table("users").update({"puan": yeni}).eq("username", user).execute()
        except: pass

    # --- 2. DURUM KONTROLÜ ---
    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'target_p' not in st.session_state: st.session_state.target_p = None

    def yeni_oyun_tetikle():
        res_g = supabase.table("oyuncular").select("*").not_.eq("kulup", "None").gte("pa", 165).limit(500).execute()
        if res_g.data:
            st.session_state.target_p = random.choice(res_g.data)
            st.session_state.game_active = True
            st.session_state.game_start_time = time.time()

    if st.button("🚀 YENİ AV BAŞLAT", use_container_width=True):
        yeni_oyun_tetikle()
        st.rerun()

    # --- 3. OYUN ALANI ---
    if st.session_state.game_active and st.session_state.target_p:
        p = st.session_state.target_p
        # HATA BURADAYDI: .state kaldırıldı
        kalan = max(0, int(30 - (time.time() - st.session_state.game_start_time)))
        yuzde = (kalan / 30) * 100

        if kalan > 0:
            # KADEMELİ İPUÇLARI
            pa_hint = f"🔥 PA: {p['pa']}" if kalan <= 20 else "🔥 PA: ??"
            ca_hint = f"📊 CA: {p.get('ca','?')}" if kalan <= 10 else "📊 CA: ??"
            
            bar_color = "#238636" if yuzde > 50 else ("#f2cc60" if yuzde > 20 else "#ff4b4b")
            
            # KART TASARIMI
            st.markdown(f"""
                <div style="background:#161b22; padding:20px; border-radius:15px; border:2px solid #30363d; text-align:center;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <span style="font-size:22px;">⏳ <b>{kalan}s</b></span>
                        <span style="color:#8b949e; font-weight:bold;">{mevki_turkce_yap(p['mevki'])}</span>
                    </div>
                    <div style="width:100%; background:#30363d; height:12px; border-radius:10px; overflow:hidden; margin-bottom:15px;">
                        <div style="width:{yuzde}%; background:{bar_color}; height:100%; transition: width 0.5s ease;"></div>
                    </div>
                    <p style="color:#ffffff; font-size:19px; margin-bottom:5px;"><b>{p['yas']} Yaş | {p.get('kulup','Serbest')}</b></p>
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
                    skor_yaz(st.session_state.user, 1)
                    st.balloons()
                    st.success(f"🎯 BİLDİN! {p['oyuncu_adi']}")
                    if st.button("Sıradaki"): 
                        yeni_oyun_tetikle()
                        st.rerun()
            
            time.sleep(0.5)
            st.rerun()
        else:
            st.session_state.game_active = False
            skor_yaz(st.session_state.user, -1)
            st.error(f"⌛ SÜRE BİTTİ! Aranan: {p['oyuncu_adi']}")
            if st.button("🔄 YENİDEN DENE"):
                yeni_oyun_tetikle()
                st.rerun()

    st.markdown("---")

    
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

# --- 5. BARROW AI (V188 - AKILLI MEVKİ ANALİZİ) ---
with tabs[5]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW AI</h1></div>', unsafe_allow_html=True)
    
    user_is_vip = st.session_state.get('is_vip', False)
    curr_user = st.session_state.get('user')
    
    if "barrow_player" not in st.session_state: st.session_state.barrow_player = None

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
                st.warning(f"🔒 Barrow: 'Günlük 3 mermi hakkın doldu hıyarto! Daha fazlası için VIP ol.'")
                st.markdown(f'''<a href="https://www.shopier.com/fmscout/45690641" target="_blank" style="text-decoration:none;"><button style="width:100%; background:#ef4444; color:white; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">SINIRSIZ BARROW İÇİN VIP OL</button></a>''', unsafe_allow_html=True)

    b_in = st.text_input("Barrow'a emir ver (Örn: 'Messi gibi bir genç', 'Hummels tarzı defans'):", key="b_in_v178", disabled=not can_ask)
    
    if st.button("BARROWA SOR", disabled=not can_ask):
        if b_in:
            if not user_is_vip:
                new_count = u_data.data[0].get('barrow_count', 0) + 1
                supabase.table("users").update({"barrow_count": new_count}).eq("username", curr_user).execute()

            BARROW_INSULTS = ["Bütçen buysa git halısaha maçı ayarla hıyarto!", "Yine mi sen? Al şu mermiyi de kaybol.", "Messi'yi rüyanda görürsün ama bir mermi bulalım bakalım..."]
            st.markdown(f'<div style="background:#1a1a1a; padding:15px; border-left:5px solid #ef4444; color:#ef4444; margin-bottom:20px;">{random.choice(BARROW_INSULTS)}</div>', unsafe_allow_html=True)
            
            bq = supabase.table("oyuncular").select("*").gte("pa", 135)
            low_in = b_in.lower()
            
            # --- 🛡️ GÜÇLENDİRİLMİŞ MEVKİ MOTORU ---
            m_list = []
            
            # 1. Örnek Oyuncu Analizi
            scout_knowledge = {
                "messi": ["AM R", "AM C", "ST"], "ronaldo": ["ST", "AM L"], "neymar": ["AM L", "AM C"],
                "hummels": ["D C"], "van dijk": ["D C"], "modric": ["M C"], "de bruyne": ["AM C", "M C"],
                "haaland": ["ST"], "mbappe": ["ST", "AM L"], "musiala": ["AM C", "AM L"], "arda güler": ["AM C", "AM R"]
            }
            for pk, pv in scout_knowledge.items():
                if pk in low_in:
                    m_list.extend(pv)
                    if any(x in low_in for x in ["genç", "gibi", "tarzı"]): bq = bq.lte("yas", 21)

            # 2. Kesin Mevki Kelimeleri (Hata payını sıfıra indirmek için)
            if any(x in low_in for x in ["kaleci", "gk", "file bekçisi"]): m_list.append("GK")
            elif any(x in low_in for x in ["stoper", "defans", "dc"]): m_list.append("D C")
            elif any(x in low_in for x in ["sol bek", "dl"]): m_list.append("D L")
            elif any(x in low_in for x in ["sağ bek", "dr"]): m_list.append("D R")
            elif any(x in low_in for x in ["ön libero", "dm"]): m_list.append("DM")
            elif any(x in low_in for x in ["orta saha", "mc"]): m_list.append("M C")
            elif any(x in low_in for x in ["sol kanat", "aml"]): m_list.append("AM L")
            elif any(x in low_in for x in ["sağ kanat", "amr"]): m_list.append("AM R")
            elif any(x in low_in for x in ["ofansif orta", "amc"]): m_list.append("AM C")
            elif any(x in low_in for x in ["forvet", "golcü", "st", "santrafor"]): m_list.append("ST")
            
            if m_list:
                # Mevkileri tekilleştir ve filtrele
                or_filter = ",".join([f'mevki.ilike.%{m}%' for m in set(m_list)])
                bq = bq.or_(or_filter)

            # --- YAŞ ANALİZİ ---
            nums = re.findall(r'\d+', low_in)
            range_match = re.search(r'(\d+)\s*[-|ile|ve|ila|–]\s*(\d+)', low_in)
            if range_match:
                n1, n2 = int(range_match.group(1)), int(range_match.group(2))
                bq = bq.gte("yas", min(n1, n2)).lte("yas", max(n1, n2))
            elif any(x in low_in for x in ["en fazla", "max", "altı"]) and nums:
                bq = bq.lte("yas", int(nums[0]))
            elif nums and "yaş" in low_in: bq = bq.eq("yas", int(nums[0]))
            elif not any(x in low_in for x in scout_knowledge.keys()): bq = bq.lte("yas", 28)

            res_b = bq.limit(100).execute()
            if res_b.data:
                st.session_state.barrow_player = random.choice(res_b.data)
            else:
                st.session_state.barrow_player = "empty"
            st.rerun()

    # --- OYUNCU KARTI ---
    if st.session_state.barrow_player and st.session_state.barrow_player != "empty":
        p = st.session_state.barrow_player
        f_check = supabase.table("favoriler").select("oyuncu_adi").eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
        is_f = len(f_check.data) > 0
        tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
        border_color = "#238636" if is_f else "#ef4444"
        
        st.markdown(f'''
        <div style="background:#000; border:2px solid {border_color}; padding:20px; border-radius:15px; margin-top:20px; position:relative;">
            <span style="position:absolute; top:10px; right:10px; background:{border_color}; color:white; padding:3px 10px; border-radius:5px; font-weight:bold; font-size:12px;">PA: {p["pa"]}</span>
            <h2 style="color:{border_color}; margin:0;">{p["oyuncu_adi"]}</h2>
            <p style="color:#00ff41; font-family:'JetBrains Mono', monospace; font-size:14px; margin:15px 0;">
                🌍 Ülke: {p.get("ulke", "Bilinmiyor")}<br>
                🏟️ Kulüp: {p.get("kulup", "Serbest")}<br>
                👟 Mevki: {p.get("mevki", "-")}<br>
                🎂 Yaş: {p.get("yas", "-")}<br>
                💰 Değer: {p.get("deger", "-")}
            </p>
            <a href="{tm_url}" target="_blank" style="display:inline-block; background:#1a1a1a; color:#58a6ff; padding:5px 10px; border-radius:5px; text-decoration:none; font-size:12px; border:1px solid #30363d;">Transfermarkt Profili ➔</a>
        </div>
        ''', unsafe_allow_html=True)

        if st.button("⭐ Listeye Ekle / Çıkar", key="barrow_fav_final"):
            if is_f:
                supabase.table("favoriler").delete().eq("oyuncu_adi", p['oyuncu_adi']).eq("kullanici_adi", curr_user).execute()
                st.toast("Mermi listeden çıkarıldı!")
            else:
                supabase.table("favoriler").insert({
                    "oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup','Serbest'),
                    "pa": p['pa'], "mevki": p['mevki'], "ca": p.get('ca', 0),
                    "kullanici_adi": curr_user
                }).execute()
                st.toast("Mermi listeye eklendi!")
            st.rerun()

    elif st.session_state.barrow_player == "empty":
        st.error("Barrow: 'O kriterlerde mermi bulamadım hıyarto!'")

# --- 6. ADMIN (V130 - TAM YETKİ VE DENETİM) ---
with tabs[6]: 
    if st.session_state.get('user') == "someku":
        st.markdown('<h1 style="color:#ff4b4b; text-align:center;">🛡️ YÖNETİM MERKEZİ</h1>', unsafe_allow_html=True)
        
        # 1. GERÇEK SAYIM (470 BİN OYUNCU İÇİN)
        try:
            res_count = supabase.table("oyuncular").select("*", count="exact").limit(1).execute()
            actual_count = res_count.count
            u_res = supabase.table("users").select("*").execute()
            total_users = len(u_res.data)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Toplam Oyuncu", f"{actual_count:,}".replace(",", "."))
            c2.metric("Kayıtlı Kullanıcı", total_users)
            c3.success("Sistem Çevrimiçi")
        except:
            st.warning("Veri bağlantısı kuruluyor...")

        st.markdown("---")
        adm_tabs = st.tabs(["✏️ Oyuncu Düzenle/Ekle", "👥 Kullanıcı & Ban & Şifre", "🛠️ Sistem"])

        # --- A. OYUNCU DÜZENLEME VE EKLEME ---
        with adm_tabs[0]:
            st.write("### ✍️ Oyuncu Verilerini Düzenle")
            search_edit = st.text_input("Düzenlenecek Oyuncu Adı:", key="search_edit")
            if search_edit:
                res_e = supabase.table("oyuncular").select("*").ilike("oyuncu_adi", f"%{search_edit}%").limit(5).execute()
                for p in res_e.data:
                    with st.expander(f"DÜZENLE: {p['oyuncu_adi']} ({p['kulup']})"):
                        with st.form(f"edit_form_{p['id']}"):
                            n_ad = st.text_input("Ad", value=p['oyuncu_adi'])
                            n_klb = st.text_input("Kulüp", value=p['kulup'])
                            n_mvk = st.text_input("Mevki", value=p['mevki'])
                            n_ys = st.number_input("Yaş", value=int(p['yas']))
                            n_pa = st.number_input("PA", value=int(p['pa']))
                            n_dgr = st.text_input("Değer", value=p['deger'])
                            
                            if st.form_submit_button("GÜNCELLE"):
                                supabase.table("oyuncular").update({
                                    "oyuncu_adi": n_ad, "kulup": n_klb, "mevki": n_mvk,
                                    "yas": n_ys, "pa": n_pa, "deger": n_dgr
                                }).eq("id", p['id']).execute()
                                st.success(f"{n_ad} güncellendi!")
                                st.rerun()
                        if st.button(f"🗑️ BU OYUNCUYU SİL", key=f"del_{p['id']}"):
                            supabase.table("oyuncular").delete().eq("id", p['id']).execute()
                            st.error("Oyuncu silindi.")
                            st.rerun()

        # --- B. KULLANICI & BAN & ŞİFRE PANELİ ---
        with adm_tabs[1]:
            st.write("### 👥 Kullanıcı Denetimi")
            if u_res.data:
                for u in u_res.data:
                    with st.container():
                        col1, col2, col3 = st.columns([2, 2, 1])
                        col1.write(f"**Kullanıcı:** {u['username']}")
                        # Şifreleri maskelemeden gösteriyoruz (İstediğin gibi)
                        col2.write(f"🔑 **Şifre:** `{u.get('password', 'N/A')}`") 
                        # IP adresi (Eğer sütun varsa)
                        ip = u.get('ip_adresi', 'Bilinmiyor')
                        col1.caption(f"🌐 IP: {ip}")
                        
                        if u['username'] != "someku":
                            if col3.button("BANLA / SİL", key=f"ban_{u['id']}"):
                                supabase.table("users").delete().eq("id", u['id']).execute()
                                st.warning(f"{u['username']} sistemden atıldı.")
                                st.rerun()
                    st.markdown("---")

        # --- C. SİSTEM BAKIMI ---
        with adm_tabs[2]:
            st.write("### 🛠️ Kritik İşlemler")
            if st.button("TÜM FAVORİLERİ SIFIRLA"):
                st.warning("Emin misiniz? Geri dönüşü yok!")
                if st.checkbox("Evet, tüm favorileri temizle"):
                    supabase.table("favoriler").delete().neq("id", 0).execute()
                    st.success("Tüm favori verileri silindi.")
    else:
        st.warning("Bu bölgeye erişim izniniz yok.")
