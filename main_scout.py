import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    .filter-box, .compare-box {
        background-color: rgba(20, 20, 20, 0.98);
        padding: 15px; border-radius: 15px; border: 1px solid #00D2FF;
        margin-bottom: 15px;
    }
    h1 { text-shadow: 2px 2px 10px #00D2FF; font-size: 24px !important; text-align: center; color: #00D2FF; }
    label { color: #FFFFFF !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

# Bölge Sözlüğü (Ülkeleri Gruplara Ayırıyoruz)
bolge_grupları = {
    "Güney Amerika": ["Argentina", "Brazil", "Uruguay", "Colombia", "Chile", "Ecuador", "Paraguay", "Peru", "Venezuela", "Bolivia"],
    "Avrupa (Genel)": ["Germany", "France", "Spain", "Italy", "Portugal", "Netherlands", "Belgium", "Switzerland", "Austria"],
    "Kuzey Avrupa": ["Norway", "Sweden", "Denmark", "Finland", "Iceland"],
    "Afrika": ["Nigeria", "Senegal", "Ivory Coast", "Cameroon", "Ghana", "Algeria", "Morocco", "Egypt", "Mali", "Tunisia"],
    "Asya": ["Japan", "South Korea", "China", "Australia", "Iran", "Saudi Arabia", "Uzbekistan"],
    "Balkanlar/Doğu": ["Turkey", "Croatia", "Serbia", "Greece", "Bulgaria", "Romania", "Poland", "Czech Republic", "Slovakia", "Hungary"]
}

mevki_sozlugu = {
    "Kaleci": "GK", "Stoper": "D (C)", "Sağ Bek": "D (R)", "Sol Bek": "D (L)",
    "Ön Libero": "DM", "Merkez Orta Saha": "M (C)", "Sağ Kanat": "(R)",
    "Sol Kanat": "(L)", "On Numara": "AM (C)", "Forvet": "S (C)"
}

@st.cache_data
def load_data(path):
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        if 'ID' in df.columns: df = df.drop(columns=['ID'])
        df['Kulüp'] = df['Kulüp'].fillna('Kulüpsüz').astype(str)
        df['Ülke'] = df['Ülke'].fillna('Bilinmiyor').astype(str)
        df['Mevki'] = df['Mevki'].fillna('-').astype(str)
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        return df.sort_values(by='PA', ascending=False)
    except: return None

df = load_data("players_export.csv")

if df is not None:
    # Karşılaştırma Paneli (Expander içinde gizlendi)
    with st.expander("⚔️ OYUNCU KARŞILAŞTIRMA PANELİ"):
        oyuncu_listesi = ["Seçiniz..."] + sorted([x for x in df['Oyuncu'].unique()])
        p1 = st.selectbox("1. Oyuncu:", oyuncu_listesi, key="p1")
        p2 = st.selectbox("2. Oyuncu:", oyuncu_listesi, key="p2")
        if p1 != "Seçiniz..." and p2 != "Seçiniz...":
            d1, d2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.metric(f"{p1} vs {p2}", f"PA: {d1['PA']} - {d2['PA']}", f"Yaş: {d1['Yaş']} - {d2['Yaş']}")

    # Ana Filtreleme Paneli
    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        f_mevki = st.multiselect("⚽ Mevki Seç:", list(mevki_sozlugu.keys()))
        f_bolge = st.multiselect("🌎 Bölge/Kıta Seç:", list(bolge_grupları.keys()))
    with col_b:
        f_yas = st.slider("🎂 Yaş:", 14, 45, (14, 45))
        f_pa = st.slider("🔥 PA:", 0, 200, (0, 200))
    
    search = st.text_input("🔍 İsim veya Kulüp ile Ara:")
    st.markdown("</div>", unsafe_allow_html=True)

    # Filtreleme İşlemi
    filtered = df.copy()
    
    # Bölge Filtresi (Yeni)
    if f_bolge:
        secilen_ulkeler = []
        for b in f_bolge:
            secilen_ulkeler.extend(bolge_grupları[b])
        filtered = filtered[filtered['Ülke'].isin(secilen_ulkeler)]

    # Diğer Filtreler
    filtered = filtered[
        (filtered['Oyuncu'].str.contains(search, case=False, na=False) | 
         filtered['Kulüp'].str.contains(search, case=False, na=False)) &
        (filtered['Yaş'] >= f_yas[0]) & (filtered['Yaş'] <= f_yas[1]) &
        (filtered['PA'] >= f_pa[0]) & (filtered['PA'] <= f_pa[1])
    ]

    # Mevki Filtresi (Zırhlı Regex)
    if f_mevki:
        karsiliklar = [mevki_sozlugu[m] for m in f_mevki]
        def mevki_kontrol(m_hucre):
            return any(re.search(re.escape(k), m_hucre, re.IGNORECASE) for k in karsiliklar)
        filtered = filtered[filtered['Mevki'].apply(mevki_kontrol)]

    st.subheader(f"✅ {len(filtered)} Potansiyel Yetenek Listelendi")
    st.dataframe(filtered[['Oyuncu', 'Yaş', 'PA', 'Mevki', 'Ülke', 'Kulüp', 'Değer']], use_container_width=True)
else:
    st.error("Lütfen 'players_export.csv' dosyasını yüklediğinizden emin olun!")
