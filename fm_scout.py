import os
import subprocess
import sys

# Eksik kütüphaneleri otomatik kuran bölüm
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pandas as pd
except ImportError:
    install('pandas')
    import pandas as pd

try:
    import altair
except ImportError:
    install('altair')

import streamlit as st

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Tasarım ve Arka Plan
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    h1 { text-shadow: 2px 2px 15px #00D2FF; font-weight: 900; text-align: center; color: #00D2FF; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

FILE_NAME = "players_export.csv"

if os.path.exists(FILE_NAME):
    try:
        # Dosyayı en esnek şekilde okuyoruz
        df = pd.read_csv(FILE_NAME, sep=None, engine='python', on_bad_lines='skip')
        # Sütunları standartlaştır
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        
        search_name = st.text_input("🔍 Oyuncu Ara:", placeholder="İsim yazın...")
        
        if search_name:
            f_df = df[df['Oyuncu'].str.contains(search_name, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True)
        else:
            st.info("💡 Aramaya başlamak için bir isim yazın.")
            st.dataframe(df.head(50), use_container_width=True)
            
    except Exception as e:
        st.error(f"Veri okuma hatası: {e}")
else:
    st.error("⚠️ players_export.csv bulunamadı!")
