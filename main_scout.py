import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Görsel Tasarım ve Türkçeleştirme
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .filter-box {
        background-color: rgba(20, 20, 20, 0.98);
        padding: 30px; border-radius: 25px; border: 2px solid #00D2FF;
        margin-bottom: 25px; box-shadow: 0 0 30px rgba(0, 210, 255, 0.2);
    }
    h1 { text-shadow: 2px 2px 20px #00D2FF; font-weight: 900; text-align: center; color: #00D2FF; margin-bottom: 10px; }
    h3 { color: #00D2FF !important; }
    label { color: #FFFFFF !important; font-size: 16px !important; font-weight: bold !important; }
    .stMultiSelect div div div div { color: #00D2FF !important; background-color: #1E1E1E !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
st.sidebar.write("👤 Geliştirici: **SOMEKU**")
st.sidebar.info("Trabzonspor Scouting Sistemi v2.0")

FILE_NAME = "players_export.csv"

# Mevki Eşleştirme Sözlüğü (Detaylı Türkçe)
mevki_sozlugu = {
    "Kaleci": "GK",
    "Stoper": "DC",
    "Sağ Bek": "DR",
    "Sol Bek": "DL",
    "Ön Libero": "DM",
    "Merkez Orta Saha": "MC",
    "Sağ Kanat": "AMR",
    "Sol Kanat": "AML",
    "Ofansif Orta Saha": "AMC",
    "Forvet": "ST"
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
        st.error(f"Veri yüklenirken hata: {e}")
        return None

if os.path.exists(FILE_NAME):
    df = load_data(FILE_NAME)
    if df is not None:
        search_name = st.text_input("", placeholder="🔍 Aramak istediğiniz oyuncunun ismini yazın...", key="main_search")
        
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>🎯 Detaylı Filtreleme Paneli</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            secilen_turkce_mevkiler = st.multiselect(
                "⚽ Sahadaki Pozisyonu Seçin:", 
                options=list(mevki_sozlugu.keys()),
                help="Birden fazla mevki seçebilirsiniz."
            )
        with col2:
            yas_araligi = st.slider("🎂 Yaş Aralığı:", 14, 45, (14, 25))
            
        pa_araligi = st.slider("🔥 Minimum - Maksimum Potansiyel (PA):", 0, 200, (135, 200))
        st.markdown("</div>", unsafe_allow_html=True)

        # Filtreleme Mantığı
        f_df = df[
            (df['Oyuncu'].str.contains(search_name, case=False, na=False)) &
            (df['Yaş'] >= yas_araligi[0]) & (df['Yaş'] <= yas_araligi[1]) &
            (df['PA'] >= pa_araligi[0]) & (df['PA'] <= pa_araligi[1])
        ]
        
        if secilen_turkce_mevkiler:
            ingilizce_karsiliklar = [mevki_sozlugu[m] for m in secilen_turkce_mevkiler]
            f_df = f_df[f_df['Mevki'].str.contains('|'.join(ingilizce_karsiliklar), case=False, na=False)]
            
        st.subheader(f"📊 Kriterlere Uygun {len(f_df)} Potansiyel Oyuncu")
        st.dataframe(f_df, use_container_width=True, height=600)
else:
    st.error("⚠️ Veri dosyası (players_export.csv) bulunamadı!")
