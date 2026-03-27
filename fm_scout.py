import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .filter-box {
        background-color: rgba(25, 25, 25, 0.95);
        padding: 25px; border-radius: 20px; border: 1px solid #00D2FF;
        margin-bottom: 25px; box-shadow: 0 0 20px rgba(0, 210, 255, 0.3);
    }
    h1 { text-shadow: 2px 2px 15px #00D2FF; font-weight: 900; text-align: center; color: #00D2FF; margin-bottom: 5px; }
    label { color: #00D2FF !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)
st.sidebar.write("👤 Geliştirici: **SOMEKU**")

FILE_NAME = "players_export.csv"

@st.cache_data
def load_data(path):
    try:
        # Hata payını sıfırlamak için farklı ayırıcıları deniyoruz
        df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        # Sütun isimlerini zorla düzeltelim
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        if 'ID' in df.columns: df = df.drop(columns=['ID'])
        for col in ['PA', 'CA', 'Yaş']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Veri okuma hatası: {e}")
        return None

if os.path.exists(FILE_NAME):
    df = load_data(FILE_NAME)
    if df is not None:
        search_name = st.text_input("", placeholder="🔍 Oyuncu ismini buraya yazın...", key="main_search")
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        f1, f2, f3 = st.columns([3, 2, 2])
        with f1: m_secim = st.multiselect("⚽ Mevki Seç:", ["GK", "DC", "DR", "DL", "DM", "MC", "AMR", "AML", "AMC", "ST"])
        with f2: yas_araligi = st.slider("🎂 Yaş:", 14, 45, (14, 23))
        with f3: pa_araligi = st.slider("🔥 PA Potansiyel:", 0, 200, (0, 200))
        st.markdown("</div>", unsafe_allow_html=True)

        if not search_name and not m_secim and pa_araligi == (0, 200):
            st.info("💡 Aramaya başlamak için yukarıya bir isim yazın.")
        else:
            f_df = df[
                (df['Oyuncu'].str.contains(search_name, case=False, na=False)) &
                (df['Yaş'] >= yas_araligi[0]) & (df['Yaş'] <= yas_araligi[1]) &
                (df['PA'] >= pa_araligi[0]) & (df['PA'] <= pa_araligi[1])
            ]
            if m_secim:
                f_df = f_df[f_df['Mevki'].str.contains('|'.join(m_secim), case=False, na=False)]
            st.subheader(f"✅ {len(f_df)} Oyuncu Bulundu")
            st.dataframe(f_df, use_container_width=True, height=650)
else:
    st.error("⚠️ players_export.csv dosyası bulunamadı! Lütfen GitHub'a yüklediğinizden emin olun.")
