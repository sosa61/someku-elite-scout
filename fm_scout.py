import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Görsel Tasarım
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .filter-box, .compare-box {
        background-color: rgba(20, 20, 20, 0.98);
        padding: 25px; border-radius: 20px; border: 1px solid #00D2FF;
        margin-bottom: 20px; box-shadow: 0 0 20px rgba(0, 210, 255, 0.2);
    }
    h1, h2, h3 { color: #00D2FF !important; text-align: center; text-shadow: 2px 2px 10px rgba(0,210,255,0.5); }
    label { color: #FFFFFF !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

# Mevki Eşleştirme
mevki_sozlugu = {
    "Kaleci": "GK", "Stoper": "DC", "Sağ Bek": "DR", "Sol Bek": "DL",
    "Ön Libero": "DM", "Merkez Orta Saha": "MC", "Sağ Kanat": "AMR",
    "Sol Kanat": "AML", "On Numara": "AMC", "Forvet": "ST"
}

@st.cache_data
def load_data(path):
    try:
        df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        if 'ID' in df.columns: df = df.drop(columns=['ID'])
        for col in ['PA', 'CA', 'Yaş']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Veri hatası: {e}")
        return None

if os.path.exists("players_export.csv"):
    df = load_data("players_export.csv")
    if df is not None:
        # --- SOL MENÜ (SİDEBAR) ---
        st.sidebar.markdown("### 👤 Geliştirici: SOMEKU")
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚔️ Oyuncu Karşılaştır")
        
        p1 = st.sidebar.selectbox("1. Oyuncuyu Seç:", ["Seçiniz..."] + list(df['Oyuncu'].unique()))
        p2 = st.sidebar.selectbox("2. Oyuncuyu Seç:", ["Seçiniz..."] + list(df['Oyuncu'].unique()))
        
        if p1 != "Seçiniz..." and p2 != "Seçiniz...":
            st.markdown("<div class='compare-box'>", unsafe_allow_html=True)
            st.markdown("### ⚔️ Karşılaştırma Paneli")
            c1, c2 = st.columns(2)
            d1 = df[df['Oyuncu'] == p1].iloc[0]
            d2 = df[df['Oyuncu'] == p2].iloc[0]
            
            with c1:
                st.info(f"**{p1}**")
                st.write(f"🎂 Yaş: {d1['Yaş']} | 🌍 {d1['Ülke']}")
                st.write(f"🔥 PA: {d1['PA']} | 📈 Rat: {d1['Rat']}")
                st.progress(int(d1['PA'])/200)
            
            with c2:
                st.success(f"**{p2}**")
                st.write(f"🎂 Yaş: {d2['Yaş']} | 🌍 {d2['Ülke']}")
                st.write(f"🔥 PA: {d2['PA']} | 📈 Rat: {d2['Rat']}")
                st.progress(int(d2['PA'])/200)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- ANA FİLTRELEME ---
        search_name = st.text_input("", placeholder="🔍 Oyuncu ismini buraya yazın...")
        
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            secilen_mevkiler = st.multiselect("⚽ Mevki Seç:", list(mevki_sozlugu.keys()))
        with col2:
            yas_araligi = st.slider("🎂 Yaş:", 14, 45, (14, 25))
        pa_araligi = st.slider("🔥 Potansiyel (PA):", 0, 200, (135, 200))
        st.markdown("</div>", unsafe_allow_html=True)

        # Filtreleme
        f_df = df[
            (df['Oyuncu'].str.contains(search_name, case=False, na=False)) &
            (df['Yaş'] >= yas_araligi[0]) & (df['Yaş'] <= yas_araligi[1]) &
            (df['PA'] >= pa_araligi[0]) & (df['PA'] <= pa_araligi[1])
        ]
        
        if secilen_mevkiler:
            karsiliklar = [mevki_sozlugu[m] for m in secilen_mevkiler]
            f_df = f_df[f_df['Mevki'].str.contains('|'.join(karsiliklar), case=False, na=False)]
            
        st.subheader(f"✅ {len(f_df)} Oyuncu Listelendi")
        st.dataframe(f_df, use_container_width=True, height=500)
else:
    st.error("⚠️ Veri bulunamadı!")
