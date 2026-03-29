```python
import streamlit as st
from supabase import create_client, Client
import urllib.parse
import random
import time

# --- BAĞLANTI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "BURAYA_SUPABASE_KEY"
supabase: Client = create_client(URL, KEY)

# --- SAYFA ---
st.set_page_config(page_title="SOMEKU SCOUT", layout="wide", page_icon="🕵️")

# --- CSS ---
st.markdown("""
<style>
.stApp { background-color: #0d1117; color: white; }
.player-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; margin-bottom: 15px; border-left: 5px solid #3b82f6; }
.fav-active { border: 2px solid gold !important; }
.pa-badge { background: green; padding: 4px 10px; border-radius: 6px; float:right; }
</style>
""", unsafe_allow_html=True)

# --- FONKSİYON ---
def get_user_favs(username):
    try:
        res = supabase.table("favoriler").select("oyuncu_adi").eq("kullanici_adi", username).execute()
        return [f['oyuncu_adi'] for f in res.data] if res.data else []
    except:
        return []

# --- SESSION ---
if 'user' not in st.session_state: st.session_state.user = None
if 'fav_list' not in st.session_state: st.session_state.fav_list = []
if 'roulette_player' not in st.session_state: st.session_state.roulette_player = None

# --- LOGIN ---
if st.session_state.user is None:
    st.title("🕵️ SOMEKU SCOUT")
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
        if res.data:
            st.session_state.user = u
            st.session_state.fav_list = get_user_favs(u)
            st.rerun()
        else:
            st.error("Hatalı giriş")
    st.stop()

# --- TABS ---
tabs = st.tabs(["🔍 SCOUT","🎰 RULET","📋 11 KUR","⭐ FAVORİLER","🏟️ TAKIM","💡 ÖNERİ","🛠️ ADMIN"])

# --- SCOUT ---
with tabs[0]:
    name = st.text_input("Oyuncu Ara")
    max_val = st.slider("💰 Max Piyasa Değeri (M€)", 1, 300, 300)

    sort_opt = st.selectbox("📊 Sırala", ["PA", "Yaş", "Değer"])

    query = supabase.table("oyuncular").select("*").lte("piyasa_degeri", max_val)

    if name:
        query = query.ilike("oyuncu_adi", f"%{name}%")

    if sort_opt == "PA":
        query = query.order("pa", desc=True)
    elif sort_opt == "Yaş":
        query = query.order("yas")
    else:
        query = query.order("piyasa_degeri", desc=True)

    res = query.execute()

    if res.data:
        for p in res.data:
            is_fav = p['oyuncu_adi'] in st.session_state.fav_list

            tm_url = f"https://www.transfermarkt.com.tr/schnellsuche/ergebnis/schnellsuche?query={urllib.parse.quote(p['oyuncu_adi'])}"

            st.markdown(f"""
            <div class="player-card {'fav-active' if is_fav else ''}">
                <span class="pa-badge">PA: {p.get('pa','?')}</span>
                <h3>{p['oyuncu_adi']}</h3>
                <p>
                📍 {p.get('ulke','')} |
                🏟️ {p.get('kulup','')} |
                🎂 {p.get('yas','?')} |
                📊 CA: {p.get('ca','?')} |
                💰 {p.get('piyasa_degeri','?')}M€
                </p>
                <a href="{tm_url}" target="_blank">Transfermarkt</a>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"{'⭐ Favoriden Çıkar' if is_fav else '☆ Favori Ekle'}", key=p['oyuncu_adi']):
                if is_fav:
                    supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute()
                    st.session_state.fav_list.remove(p['oyuncu_adi'])
                else:
                    supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                    st.session_state.fav_list.append(p['oyuncu_adi'])
                st.rerun()

# --- RULET ---
with tabs[1]:
    if st.button("🎰 ÇEVİR"):
        lucky = supabase.table("oyuncular").select("*").gte("pa",150).lte("yas",21).execute()
        if lucky.data:
            st.session_state.roulette_player = random.choice(lucky.data)

    if st.session_state.roulette_player:
        p = st.session_state.roulette_player
        st.success(f"{p['oyuncu_adi']}")

        is_fav = p['oyuncu_adi'] in st.session_state.fav_list
        if st.button("⭐ Favori İşlemi"):
            if is_fav:
                supabase.table("favoriler").delete().eq("kullanici_adi", st.session_state.user).eq("oyuncu_adi", p['oyuncu_adi']).execute()
                st.session_state.fav_list.remove(p['oyuncu_adi'])
            else:
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": p['oyuncu_adi']}).execute()
                st.session_state.fav_list.append(p['oyuncu_adi'])
            st.rerun()

# --- 11 KUR ---
with tabs[2]:
    f_names = st.session_state.fav_list if st.session_state.fav_list else ["Boş"]

    st.markdown("## 🧤 Kaleci")
    st.selectbox("GK", f_names)

    st.markdown("## 🛡️ Defans")
    st.selectbox("DC1", f_names)
    st.selectbox("DC2", f_names)

    st.markdown("## ⚙️ Orta Saha")
    st.selectbox("MC1", f_names)
    st.selectbox("MC2", f_names)

    st.markdown("## 🎯 Forvet")
    st.selectbox("ST", f_names)

# --- FAVORİLER ---
with tabs[3]:
    favs = get_user_favs(st.session_state.user)
    if favs:
        for f in favs:
            st.write(f)
    else:
        st.info("Favori yok")

# --- TAKIM ÇARKI ---
with tabs[4]:
    teams_data = supabase.table("oyuncular").select("kulup").execute().data
    teams = list(set([t["kulup"] for t in teams_data if t["kulup"]]))

    if st.button("🏟️ ÇARKI ÇEVİR"):
        st.success(random.choice(teams))

# --- ÖNERİ ---
with tabs[5]:
    konu = st.selectbox("Konu", ["Hata","Öneri","Tasarım"])
    msg = st.text_area("Mesaj")

    if st.button("Gönder"):
        supabase.table("oneriler").insert({
            "kullanici_adi": st.session_state.user,
            "konu": konu,
            "mesaj": msg
        }).execute()
        st.success("Gönderildi")

# --- ADMIN ---
with tabs[6]:
    if st.session_state.user == "someku":
        st.subheader("Oyuncu Ekle")

        ad = st.text_input("Oyuncu Adı")
        kulup = st.text_input("Kulüp")

        if st.button("Ekle"):
            supabase.table("oyuncular").insert({
                "oyuncu_adi": ad,
                "kulup": kulup
            }).execute()
            st.success("Eklendi")
    else:
        st.error("Yetki yok")
```
