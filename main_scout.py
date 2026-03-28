import streamlit as st
import pd as pd # pandas as pd yerine pd olarak kalsın (kısa yazım için)
import pandas as pd
import os
import hashlib
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# FM Pozisyon Sözlüğü
ana_mevkiler = {"GK": "Kaleci", "D C": "Stoper", "D L": "Sol Bek", "D R": "Sağ Bek", "DM": "Ön Libero", "M C": "Orta Saha", "AM C": "On Numara", "AM L": "Sol Kanat", "AM R": "Sağ Kanat", "ST": "Forvet"}

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

# --- TASARIM GÜNCELLEMESİ ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; background-image: linear-gradient(rgba(14,23,23,0.96), rgba(14,23,23,0.96)), url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); background-size: cover; background-attachment: fixed; }
    .bagwell-chat { background: linear-gradient(135deg, #232526 0%, #414345 100%); padding: 20px; border-radius: 15px; border: 1px solid #00D2FF; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,210,255,0.2); }
    .player-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00D2FF; border-radius: 12px; padding: 15px; margin-bottom: 20px; }
    .progress-bg { background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; margin: 10px 0; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 10px; transition: 0.5s; }
    </style>
    """, unsafe_allow_html=True)

if 'user' not in st.session_state: st.session_state.user = None

# --- GİRİŞ / KAYIT ---
if st.session_state.user is None:
    st.markdown("<h1>🔐 GİRİŞ</h1>", unsafe_allow_html=True)
    auth = st.radio("", ["Giriş", "Kayıt"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        if auth == "Kayıt": supabase.table("kullanicilar").insert({"username": u, "password": get_hash(p)}).execute(); st.success("Tamam!")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == get_hash(p): st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data(ttl=3600)
    def load_data():
        if not os.path.exists("players_export.csv"): return None
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['CA'] = pd.to_numeric(df['CA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        def clean_val(x):
            try: return float(str(x).replace('£', '').replace('€', '').replace('M', '000000').replace('K', '000').replace('.', '').replace(',', '').strip())
            except: return 0
        df['ValNum'] = df['Değer'].apply(clean_val)
        for col in ['Oyuncu', 'Ülke', 'Kulüp', 'Mevki']: df[col] = df[col].fillna('-').astype(str).str.strip()
        return df

    df = load_data()
    st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

    # --- 🕵️‍♂️ BAGWELL AI: CHAT VE AKILLI ÖNERİ ✅ ---
    with st.container():
        st.markdown(f'<div class="bagwell-chat"><h3>🕵️‍♂️ Bagwell AI</h3>Selam {st.session_state.user}, nasıl bir oyuncu arıyorsun? Seninle sohbet edebilirim!</div>', unsafe_allow_html=True)
        q = st.text_input("", placeholder="Örn: 'Yamal'ın ucuz versiyonunu bul' veya 'Bana İtalyan genç defans lazım'...", label_visibility="collapsed").lower()
        
        if q:
            ai_df = df.copy()
            msg = "Anladım Ömer, veritabanını tarıyorum..."
            
            # Sohbet Mantığı
            if "yamal" in q or "kanat" in q:
                ai_df = ai_df[ai_df['Mevki'].str.contains("AM R|AM L", na=False)]
                msg = "Harika seçim! Yamal gibi kanat oynayan genç yetenekleri süzüyorum. İşte senin için bulduğum klonlar:"
            elif "defans" in q or "stoper" in q:
                ai_df = ai_df[ai_df['Mevki'].str.contains("D C", na=False)]
                msg = "Savunmayı beton gibi yapacak o ismi bulalım. İşte en sağlam genç defans önerilerim:"
            elif "türk" in q:
                ai_df = ai_df[ai_df['Ülke'].str.contains("Tür", na=False)]
                msg = "Yerli ve milli wonderkidlerimizi listeliyorum. Geleceğin yıldızları burada:"

            if "genç" in q: ai_df = ai_df[ai_df['Yaş'] <= 21]
            if "ucuz" in q: ai_df = ai_df[ai_df['ValNum'] <= 15000000]
            if "italy" in q or "italyan" in q: ai_df = ai_df[ai_df['Ülke'].str.contains("Ita", na=False)]
            
            ai_df = ai_df.sort_values(by="PA", ascending=False)
            
            st.markdown(f"*{msg}*")
            cols = st.columns(3)
            for i, (idx, r) in enumerate(ai_df.head(3).iterrows()):
                cols[i].info(f"**{r['Oyuncu']}**\n\n🛡️ {r['Kulüp']}\n⚽ {r['Mevki']}\nYaş: {r['Yaş']} | PA: {r['PA']} | CA: {r['CA']}\n💰 {r['Değer']}")

    # --- SEKMELER (ADMİN TAMİR EDİLDİ ✅) ---
    tabs = st.tabs(["🔍 Scout", "🔥 Popüler", "⭐ Liste", "⚔️ Kıyas", "⚽ Kadrom", "🛠️ Admin"])

    with tabs[0]: # SCOUT
        col1, col2 = st.columns(2); search = col1.text_input("🔍 Manuel Ara:"); f_pa = col2.slider("🔥 Min PA:", 0, 200, 130)
        f_mevki = st.multiselect("Pozisyon:", list(ana_mevkiler.keys()), format_func=lambda x: f"{x} ({ana_mevkiler[x]})")
        f_ulke = st.multiselect("Ülke:", sorted(df['Ülke'].unique()))
        f_yas = st.slider("Yaş Aralığı:", 14, 45, (14, 45))

        f_df = df[(df['PA'] >= f_pa) & (df['Yaş'] >= f_yas[0]) & (df['Yaş'] <= f_yas[1])]
        if search: f_df = f_df[f_df['Oyuncu'].str.contains(search, case=False)]
        if f_mevki: f_df = f_df[f_df['Mevki'].apply(lambda x: any(m in x for m in f_mevki))]
        if f_ulke: f_df = f_df[f_df['Ülke'].isin(f_ulke)]

        for idx, row in f_df.head(15).iterrows():
            perc = (row['CA'] / row['PA'] * 100) if row['PA'] > 0 else 0
            color = "#FF4B4B" if perc < 40 else "#FFD700" if perc < 75 else "#00FFC2"
            st.markdown(f"""<div class="player-card"><b>{row['Oyuncu']}</b> ({row['Yaş']})<br><small>{row['Kulüp']} | {row['Mevki']}</small><div class="progress-bg"><div class="progress-fill" style="width:{perc}%; background:{color};"></div></div><small>PA: {row['PA']} | CA: {row['CA']} | 💰 {row['Değer']}</small>""", unsafe_allow_html=True)
            if st.button(f"⭐ Ekle", key=f"add_{idx}"):
                supabase.table("favoriler").insert({"kullanici_adi": st.session_state.user, "oyuncu_adi": row['Oyuncu']}).execute()
                st.toast("Eklendi!")
            st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]: # POPÜLER
        pop = supabase.table("favoriler").select("oyuncu_adi").execute()
        if pop.data: st.table(pd.DataFrame(pop.data)['oyuncu_adi'].value_counts().head(10))

    with tabs[5]: # ADMİN (TAMİR EDİLDİ ✅)
        st.subheader("🛠️ Admin Paneli")
        all_logs = supabase.table("favoriler").select("*").execute()
        if all_logs.data: st.dataframe(pd.DataFrame(all_logs.data).tail(50))
        all_users = supabase.table("kullanicilar").select("username").execute()
        if all_users.data: st.write(f"Toplam Üye: {len(all_users.data)}")

    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()
