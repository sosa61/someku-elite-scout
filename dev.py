import streamlit as st
from supabase import create_client, Client
import urllib.parse
import pandas as pd
import random
import time
import re
import streamlit.components.v1 as components

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

# --- 2. RULET (V152 - KESİN SENKRONİZASYON) ---
with tabs[1]:
    st.markdown('<h2 style="text-align:center;">🎰 SCOUT RULETİ</h2>', unsafe_allow_html=True)
    
    import random
    import json
    import time
    import urllib.parse

    # Hafıza Yönetimi
    if 'rulet_winner' not in st.session_state:
        st.session_state.rulet_winner = None
    if 'animasyon_tamam' not in st.session_state:
        st.session_state.animasyon_tamam = False

    # Veritabanından Oyuncuları Çek
    r_offset = random.randint(0, 500)
    res = supabase.table("oyuncular").select("*").gte("pa", 135).range(r_offset, r_offset + 100).execute()
    
    if res.data:
        if st.button("🎰 RULETİ ÇEVİR (135+ PA MERMİSİ SÜR)", use_container_width=True):
            all_p = res.data
            # Şeridi 40 kart yapalım
            strip_players = [random.choice(all_p) for _ in range(40)]
            
            # KAZANAN Kartı 35. Sıraya Sabitliyoruz
            winner_idx = 35
            winner = random.choice(all_p)
            strip_players[winner_idx] = winner
            
            # Hafızaya alalım
            st.session_state.rulet_winner = winner
            st.session_state.animasyon_tamam = False
            
            players_json = json.dumps(strip_players)
            
            roulette_html = f"""
            <div id="roulette-root">
                <style>
                    #r-wrapper {{
                        position: relative; width: 100%; height: 240px;
                        background: #0d1117; border: 3px solid #30363d;
                        border-radius: 15px; overflow: hidden;
                        display: flex; justify-content: center; align-items: center;
                    }}
                    #r-pointer {{
                        position: absolute; top: 0; left: 50%; transform: translateX(-50%);
                        width: 4px; height: 100%; background: #238636; z-index: 1000;
                        box-shadow: 0 0 25px #238636;
                    }}
                    #r-track {{
                        display: flex; position: absolute; left: 50%;
                        transition: transform 5s cubic-bezier(0.1, 0, 0.1, 1);
                        will-change: transform;
                        transform: translateX(0px);
                    }}
                    .r-card {{
                        min-width: 160px !important; max-width: 160px !important;
                        height: 190px; background: #161b22;
                        border: 2px solid #30363d; margin: 0; border-radius: 12px;
                        display: flex; flex-direction: column; justify-content: center;
                        align-items: center; text-align: center; color: transparent;
                        background-image: repeating-linear-gradient(45deg, #1c2128 0, #1c2128 10px, #161b22 10px, #161b22 20px);
                    }}
                    .is-winner {{
                        border-color: #238636 !important; color: white !important;
                        background: #0e2a14 !important; background-image: none !important;
                        box-shadow: inset 0 0 30px #238636; transform: scale(1.05);
                    }}
                </style>
                <div id="r-wrapper">
                    <div id="r-pointer"></div>
                    <div id="r-track"></div>
                </div>
            </div>
            <script>
                (function() {{
                    const players = {players_json};
                    const track = document.getElementById('r-track');
                    const cardWidth = 160;
                    const winIdx = {winner_idx};

                    track.innerHTML = "";
                    players.forEach((p, i) => {{
                        const card = document.createElement('div');
                        card.className = 'r-card';
                        card.id = 'card-' + i;
                        card.innerHTML = '📂<br><small>TOP SECRET</small>';
                        track.appendChild(card);
                    }});

                    // Şeridi tam orta noktadan başlat
                    track.style.transform = "translateX(0px)";

                    setTimeout(() => {{
                        // HESAPLAMA: (Kart Sayısı * Genişlik) + (Yarım Kart ki tam çizgiye gelsin)
                        const targetX = (winIdx * cardWidth) + (cardWidth / 2);
                        track.style.transform = "translateX(-" + targetX + "px)";
                        
                        setTimeout(() => {{
                            const winCard = document.getElementById('card-' + winIdx);
                            const p = players[winIdx];
                            winCard.classList.add('is-winner');
                            winCard.innerHTML = `
                                <small style="font-size:10px;">${{p.kulup || 'Serbest'}}</small><br>
                                <b style="font-size:12px;">${{p.oyuncu_adi}}</b><br>
                                <div style="background:#238636;padding:2px 8px;border-radius:4px;font-size:11px;">PA: ${{p.pa}}</div>
                            `;
                        }}, 5000);
                    }}, 100);
                }})();
            </script>
            """
            st.components.v1.html(roulette_html, height=270)
            time.sleep(5.5)
            st.session_state.animasyon_tamam = True
            st.rerun()

        # --- ALT PANEL SONUÇ (SESSION STATE) ---
        if st.session_state.rulet_winner and st.session_state.animasyon_tamam:
            p = st.session_state.rulet_winner
            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"
            st.markdown("---")
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); border: 2px solid #238636; border-radius: 20px; padding: 20px; text-align: center; backdrop-filter: blur(10px);">
                    <div style="font-size: 40px; margin-bottom: 10px;">👤</div>
                    <h3 style="margin:0;">{p['oyuncu_adi']}</h3>
                    <p style="color: #238636; font-weight: bold; margin: 5px 0;">{p['mevki']}</p>
                    <div style="display: flex; justify-content: space-around; margin-top: 15px; border-top: 1px solid #30363d; padding-top: 10px;">
                        <div><small style="display:block; color:#8b949e;">YAŞ</small><b>{p['yas']}</b></div>
                        <div><small style="display:block; color:#8b949e;">CA</small><b style="color:#58a6ff;">{p.get('ca', '-')}</b></div>
                        <div><small style="display:block; color:#8b949e;">PA</small><b style="color:#238636;">{p['pa']}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.subheader("🕵️ Scout Raporu")
                st.write(f"🌍 **Ülke:** {p.get('ulke', 'Bilinmiyor')}")
                st.write(f"🏟️ **Mevcut Kulüp:** {p.get('kulup', 'Serbest')}")
                st.write(f"💰 **Değer:** {p.get('deger', 'N/A')}")
                
                if st.button("⭐ FAVORİLERİME EKLE", use_container_width=True):
                    supabase.table("favoriler").insert({
                        "oyuncu_adi": p['oyuncu_adi'], "kulup": p.get('kulup', 'Serbest'), 
                        "pa": p['pa'], "mevki": p['mevki'], "ca": p.get('ca', '-')
                    }).execute()
                    st.success("✅ Favorilere eklendi!")
    else:
        st.error("Mermi havuzu yüklenemedi.")

# --- 📋 İLK 11 (V127 - DİNAMİK DİZİLİŞ VE DİKEY SAHA) ---
with tabs[2]:
    st.subheader("📋 Stratejik İlk 11")
    f_n = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]
    
    # 1. DİZİLİŞ SEÇİMİ
    tactic = st.selectbox("🏟️ Saha Dizilişi Seç:", ["4-4-2", "4-3-3"], key="tactic_sel")
    
    # 2. OYUNCU SEÇİMLERİ (Dizilişe Göre Dinamik)
    st.markdown('<div class="section-header">🧤 KALECİ VE DEFANS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    gk = c1.selectbox("GK", f_n, key="sl_gk"); lb = c2.selectbox("LB", f_n, key="sl_lb")
    cb1 = c3.selectbox("CB1", f_n, key="sl_cb1"); cb2 = c4.selectbox("CB2", f_n, key="sl_cb2"); rb = c5.selectbox("sl_rb", f_n)

    st.markdown('<div class="section-header">⚙️ ORTA SAHA VE FORVET</div>', unsafe_allow_html=True)
    if tactic == "4-4-2":
        m1, m2, m3, m4 = st.columns(4)
        lm = m1.selectbox("LM", f_n, key="sl_lm"); cm1 = m2.selectbox("CM1", f_n, key="sl_cm1")
        cm2 = m3.selectbox("CM2", f_n, key="sl_cm2"); rm = m4.selectbox("RM", f_n, key="sl_rm")
        f1, f2 = st.columns(2)
        st1 = f1.selectbox("ST1", f_n, key="sl_st1"); st2 = f2.selectbox("ST2", f_n, key="sl_st2")
    else: # 4-3-3
        m1, m2, m3 = st.columns(3)
        cm1 = m1.selectbox("LCM", f_n, key="sl_lcm"); cm2 = m2.selectbox("CM", f_n, key="sl_cmm"); cm3 = m3.selectbox("RCM", f_n, key="sl_rcm")
        f1, f2, f3 = st.columns(3)
        lw = f1.selectbox("LW", f_n, key="sl_lw"); st_p = f2.selectbox("ST", f_n, key="sl_st"); rw = f3.selectbox("RW", f_n, key="sl_rw")

    # 3. GÖRSEL SAHA TASARIMI (DİKEY VE DAR)
    # Oyuncu yerleşim koordinatları dizilişe göre değişir
    players_html = ""
    if tactic == "4-4-2":
        players_html = f"""
            <div class="player" style="top:85%; left:42%; border-color:#f2cc60;"><div class="pos">GK</div><div class="name">{gk}</div></div>
            <div class="player" style="top:68%; left:5%;"><div class="pos">LB</div><div class="name">{lb}</div></div>
            <div class="player" style="top:68%; left:30%;"><div class="pos">CB</div><div class="name">{cb1}</div></div>
            <div class="player" style="top:68%; left:55%;"><div class="pos">CB</div><div class="name">{cb2}</div></div>
            <div class="player" style="top:68%; left:80%;"><div class="pos">RB</div><div class="name">{rb}</div></div>
            <div class="player" style="top:42%; left:5%;"><div class="pos">LM</div><div class="name">{lm}</div></div>
            <div class="player" style="top:42%; left:30%;"><div class="pos">CM</div><div class="name">{cm1}</div></div>
            <div class="player" style="top:42%; left:55%;"><div class="pos">CM</div><div class="name">{cm2}</div></div>
            <div class="player" style="top:42%; left:80%;"><div class="pos">RM</div><div class="name">{rm}</div></div>
            <div class="player" style="top:15%; left:30%;"><div class="pos">ST</div><div class="name">{st1}</div></div>
            <div class="player" style="top:15%; left:55%;"><div class="pos">ST</div><div class="name">{st2}</div></div>
        """
    else: # 4-3-3
        players_html = f"""
            <div class="player" style="top:85%; left:42%; border-color:#f2cc60;"><div class="pos">GK</div><div class="name">{gk}</div></div>
            <div class="player" style="top:68%; left:5%;"><div class="pos">LB</div><div class="name">{lb}</div></div>
            <div class="player" style="top:68%; left:30%;"><div class="pos">CB</div><div class="name">{cb1}</div></div>
            <div class="player" style="top:68%; left:55%;"><div class="pos">CB</div><div class="name">{cb2}</div></div>
            <div class="player" style="top:68%; left:80%;"><div class="pos">RB</div><div class="name">{rb}</div></div>
            <div class="player" style="top:45%; left:15%;"><div class="pos">CM</div><div class="name">{cm1}</div></div>
            <div class="player" style="top:45%; left:42%;"><div class="pos">CM</div><div class="name">{cm2}</div></div>
            <div class="player" style="top:45%; left:70%;"><div class="pos">CM</div><div class="name">{cm3}</div></div>
            <div class="player" style="top:15%; left:10%;"><div class="pos">LW</div><div class="name">{lw}</div></div>
            <div class="player" style="top:12%; left:42%;"><div class="pos">ST</div><div class="name">{st_p}</div></div>
            <div class="player" style="top:15%; left:75%;"><div class="pos">RW</div><div class="name">{rw}</div></div>
        """

    pitch_css = """
    <style>
        .pitch {
            position: relative; background-color: #238636;
            background-image: radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px);
            background-size: 20px 20px;
            border: 4px solid #ffffff; border-radius: 15px;
            width: 380px; height: 550px; margin: auto; overflow: hidden;
        }
        .mid-line { position: absolute; top: 50%; left: 0; width: 100%; border-top: 2px solid rgba(255,255,255,0.4); }
        .mid-circle { position: absolute; top: 41%; left: 30%; width: 40%; height: 18%; border: 2px solid rgba(255,255,255,0.4); border-radius: 50%; }
        .player {
            position: absolute; background: rgba(13, 17, 23, 0.95);
            border: 2px solid #58a6ff; border-radius: 6px; color: white;
            width: 75px; padding: 3px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.5);
        }
        .pos { font-size: 8px; color: #58a6ff; font-weight: bold; }
        .name { font-size: 9px; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
    """
    
    st.components.v1.html(f"{pitch_css}<div class='pitch'><div class='mid-line'></div><div class='mid-circle'></div>{players_html}</div>", height=570)
    
    # İndirme Metni
    kadro_txt = f"Diziliş: {tactic}\nKadro: {gk}, {lb}, {cb1}, {cb2}, {rb}..."
    st.download_button("📩 KADRO LİSTESİNİ İNDİR", kadro_txt, file_name="kadro.txt")

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

# --- 5. BARROW AI (V122 - BİN VE MİLYON BÜTÇE ZEKASI) ---
with tabs[4]:
    st.markdown('<div style="text-align:center;"><h1 style="color:#ef4444;">🤵 BARROW AI</h1></div>', unsafe_allow_html=True)
    b_in = st.text_input("Barrow'a emir ver (Örn: '500 bin euro defans', '3m forvet', '15-18 yaş 200k'):", key="b_in_v122")
    
    if st.button("BARROWA SOR"):
        if b_in:
            st.markdown(f'<div class="barrow-box"><p class="barrow-text">{random.choice(BARROW_INSULTS)}</p></div>', unsafe_allow_html=True)
            
            # --- NUMERİK VE BİRİM ANALİZİ ---
            all_nums = re.findall(r'\d+', b_in)
            req_min_age = None
            req_max_age = None
            req_price_limit = None # Milyon cinsinden saklayacağız
            
            # 1. BÜTÇE AYIKLAMA (Bin/Milyon Farkı)
            # Milyon kontrolü (5m, 5 milyon vb)
            m_match = re.search(r'(\d+)\s*(m|milyon|milyon|mio)', b_in.lower())
            # Bin kontrolü (500 bin, 500k, 500b vb)
            k_match = re.search(r'(\d+)\s*(bin|k|b|bin)', b_in.lower())
            
            if m_match:
                req_price_limit = float(m_match.group(1))
                if str(m_match.group(1)) in all_nums: all_nums.remove(str(m_match.group(1)))
            elif k_match:
                # Bin değerini Milyona çevir (Örn: 500 bin -> 0.5)
                req_price_limit = float(k_match.group(1)) / 1000
                if str(k_match.group(1)) in all_nums: all_nums.remove(str(k_match.group(1)))

            # 2. YAŞ ARALIĞI AYIKLAMA
            if len(all_nums) >= 2:
                n1, n2 = int(all_nums[0]), int(all_nums[1])
                req_min_age, req_max_age = min(n1, n2), max(n1, n2)
            elif len(all_nums) == 1:
                req_max_age = int(all_nums[0])

            # Sorgu Başlangıcı
            bq = supabase.table("oyuncular").select("*").gte("pa", 135)
            
            # Yaş Filtresi
            if req_min_age and req_max_age: bq = bq.gte("yas", req_min_age).lte("yas", req_max_age)
            elif req_max_age: bq = bq.lte("yas", req_max_age)
            else: bq = bq.lte("yas", 26)
                
            # Mevki Filtresi
            low_in = b_in.lower()
            t_m_list = []
            if "defans" in low_in or "stoper" in low_in or "bek" in low_in: t_m_list.extend(["D C", "D L", "D R"])
            elif "forvet" in low_in or "golcü" in low_in: t_m_list.append("ST")
            elif "orta saha" in low_in: t_m_list.extend(["M C", "DM", "AM C"])
            elif "kanat" in low_in: t_m_list.extend(["AM L", "AM R"])
            elif "kaleci" in low_in: t_m_list.append("GK")
            
            for k, v in BARROW_KNOWLEDGE.items():
                if k in low_in: t_m_list.extend(v)
            if t_m_list:
                bq = bq.or_(",".join([f'mevki.ilike.%{m}%' for m in set(t_m_list)]))
            
            res_b = bq.order("pa", desc=True).limit(1000).execute()
            
            if res_b.data:
                # Fiyat Karşılaştırma Fonksiyonu
                def get_m_value(x):
                    v_s = str(x.get("deger", "0")).replace(",", ".")
                    v_n = re.findall(r"[-+]?\d*\.\d+|\d+", v_s)
                    if v_n:
                        r = float(v_n[0])
                        # Veritabanındaki 'K' değerlerini M'ye çevirip kıyasla
                        return r / 1000 if "K" in v_s.upper() else r
                    return 9999.0

                final_b = res_b.data
                if req_price_limit is not None:
                    final_b = [x for x in res_b.data if get_m_value(x) <= req_price_limit]
                
                if final_b:
                    p_b = random.choice(final_b)
                    is_f = p_b['oyuncu_adi'] in st.session_state.get('fav_list', [])
                    tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p_b['oyuncu_adi'])}"
                    
                    st.markdown(f'''<div class="player-card {"fav-active" if is_f else ""}" style="border-left-color:#ff0000; background:#000;">
                        <h3 style="color:#ff0000;">{p_b["oyuncu_adi"]}</h3>
                        <p style="font-family:'JetBrains Mono'; color:#00ff41;">🏟️ {p_b["kulup"]} | 👟 {p_b["mevki"]} | 📊 PA: {p_b["pa"]} | 🎂 YAŞ: {p_b["yas"]} | 💰 {p_b.get("deger","-")}</p>
                        <a href="{tm_url}" target="_blank" class="tm-link">Transfermarkt ➔</a></div>''', unsafe_allow_html=True)
                    
                    if st.button(f"{'⭐ Listeden Çıkar' if is_f else '⭐ Listeye Ekle'}", key=f"bf_v122_{p_b['oyuncu_adi']}"):
                        if is_f:
                            supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p_b['oyuncu_adi']).execute()
                            st.session_state.fav_list.remove(p_b['oyuncu_adi'])
                        else:
                            supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p_b['oyuncu_adi']}).execute()
                            st.session_state.fav_list.append(p_b['oyuncu_adi'])
                        st.rerun()
                else:
                    st.error(f"Barrow: '{req_price_limit*1000 if req_price_limit < 1 else req_price_limit}{' bin' if req_price_limit < 1 else 'M'}' bütçeye ancak su alırsın hıyarto! Bütçeyi artır.")
            else:
                st.warning("Barrow: 'İstediğin kriterlerde mermi bulamadım, siktir git kendin ara.'")



# --- 6. ADMIN (V130 - TAM YETKİ VE DENETİM) ---
with tabs[5]: 
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
