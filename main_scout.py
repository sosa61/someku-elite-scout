import streamlit as st
import pandas as pd
import os
import hashlib
import json
import urllib.parse
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
URL = "https://iwgowefraytdbcdgeqdz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml3Z293ZWZyYXl0ZGJjZGdlcWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2MzM3MDEsImV4cCI6MjA5MDIwOTcwMX0.kWYUaG8OFvsAe-IBD4XcR7a2l2mflj4Y0HJfugU2m-o"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# --- TASARIM ---
st.markdown("""<style>.stApp { background-color: #0E1117; color: white; }.player-card { background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(0,210,255,0.05) 100%); border: 1px solid #00D2FF; border-radius: 12px; padding: 18px; margin-bottom: 15px; }.stat-box { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 13px; margin-right: 8px; }.duyuru-bandi { background: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 20px; border: 2px solid white; }.admin-stat { background: rgba(0, 210, 255, 0.1); border: 1px solid #00D2FF; padding: 15px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

@st.cache_resource
def get_hash(password): return hashlib.sha256(str.encode(password)).hexdigest()

def get_announcement():
    try:
        res = supabase.table("ayarlar").select("duyuru").eq("id", 1).execute()
        return res.data[0]['duyuru'] if res.data else "Sistem Aktif!"
    except: return "Elite Scout!"

if 'user' not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🌪️ SOMEKU ELITE SCOUT")
    st.markdown(f'<div class="duyuru-bandi">{get_announcement()}</div>', unsafe_allow_html=True)
    auth = st.radio("İşlem:", ["Giriş Yap", "Kayıt Ol"], horizontal=True)
    u = st.text_input("Kullanıcı"); p = st.text_input("Şifre", type="password")
    if st.button("Devam"):
        hp = get_hash(p)
        if auth == "Kayıt Ol":
            try: supabase.table("kullanicilar").insert({"username": u, "password": hp}).execute(); st.success("Kayıt Başarılı!")
            except: st.error("Kullanıcı mevcut.")
        else:
            res = supabase.table("kullanicilar").select("*").eq("username", u).execute()
            if res.data and res.data[0]['password'] == hp: st.session_state.user = u; st.rerun()
            else: st.error("Hatalı!")
else:
    @st.cache_data
    def load_data():
        if not os.path.exists("players_export.csv"): return pd.DataFrame()
        df = pd.read_csv("players_export.csv", sep=None, engine='python', skiprows=1, header=None)
        df = df.iloc[:, [1, 2, 3, 4, 5, 6, 7, 8]]
        df.columns = ['Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki']
        for col in ['PA', 'CA', 'Yaş']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df

    df = load_data()
    tabs = st.tabs(["🔍 SCOUT", "🔥 POPÜLER", "⭐ LİSTEM", "⚔️ KIYAS", "⚽ KADROM", "💡 ÖNERİ", "🛠️ ADMIN"])

    # --- 🔥 POPÜLER TAMİR EDİLDİ ---
    with tabs[1]:
        st.subheader("🔥 En Çok Favoriye Eklenenler")
        try:
            p_res = supabase.table("favoriler").select("oyuncu_adi").execute()
            if p_res.data:
                fav_df = pd.DataFrame(p_res.data)
                # KADRO: verilerini listeden çıkarıyoruz sadece oyuncuları sayıyoruz
                pop_counts = fav_df[~fav_df['oyuncu_adi'].str.contains("KADRO:", na=False)]['oyuncu_adi'].value_counts().reset_index()
                pop_counts.columns = ['Oyuncu', 'Favori Sayısı']
                st.table(pop_counts.head(10))
            else: st.info("Henüz popüler oyuncu yok.")
        except: st.error("Veri çekilemedi.")

    # --- ⚔️ KIYAS TAMİR EDİLDİ ---
    with tabs[3]:
        st.subheader("⚔️ Oyuncu Kıyaslama")
        p_list = sorted(df['Oyuncu'].tolist())
        sel_players = st.multiselect("Kıyaslanacak 2 Oyuncu Seç:", p_list, max_selections=2)
        if len(sel_players) == 2:
            compare_df = df[df['Oyuncu'].isin(sel_players)].set_index('Oyuncu')
            st.table(compare_df[['CA', 'PA', 'Yaş', 'Kulüp', 'Mevki', 'Değer']])

    # --- 💡 ÖNERİ TAMİR EDİLDİ ---
    with tabs[5]:
        st.subheader("💡 Öneri ve Geri Bildirim")
        oneri_metni = st.text_area("Sistem hakkında önerini yaz Someku'ya gitsin:")
        if st.button("Öneriyi Gönder"):
            if oneri_metni:
                try:
                    supabase.table("oneriler").insert({"kullanici": st.session_state.user, "mesaj": oneri_metni}).execute()
                    st.success("Önerin başarıyla gönderildi!")
                except Exception as e: st.error(f"Hata oluştu: {e}")
            else: st.warning("Lütfen bir mesaj yazın.")

    # --- 🛠️ ADMIN PANELİ (ÖNERİLER BURAYA DÜŞER) ---
    with tabs[6]:
        if any(a in st.session_state.user.lower() for a in ["someku", "omer", "admin"]):
            st.title("🛠️ Admin Paneli")
            
            # Gelen Önerileri Göster
            st.subheader("📩 Gelen Öneriler")
            try:
                onr_data = supabase.table("oneriler").select("*").order("tarih", desc=True).execute()
                if onr_data.data:
                    st.dataframe(pd.DataFrame(onr_data.data), use_container_width=True)
                else: st.info("Henüz gelen bir öneri yok.")
            except: st.error("Öneriler tablosu bulunamadı.")

            # Üye Sayısı ve Listesi
            st.write("---")
            u_data = supabase.table("kullanicilar").select("username").execute()
            st.markdown(f'<div class="admin-stat"><h3>Kayıtlı Üye Sayısı</h3><h2>{len(u_data.data)}</h2></div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(u_data.data), use_container_width=True)
        else:
            st.error("Admin yetkiniz yok.")

    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()
