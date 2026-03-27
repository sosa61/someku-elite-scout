import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Görsel Tasarım
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
    label { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

# FM'deki karmaşık yazımları yakalamak için yeni sözlük
mevki_sozlugu = {
    "Kaleci": "GK",
    "Stoper": "D (C)",
    "Sağ Bek": "D (R)",
    "Sol Bek": "D (L)",
    "Ön Libero": "DM",
    "Merkez Orta Saha": "M (C)",
    "Sağ Kanat": "(R)",  # İçinde R geçen kanatları yakalar
    "Sol Kanat": "(L)",  # İçinde L geçen kanatları yakalar
    "On Numara": "AM (C)",
    "Forvet": "S (C)"
}

@st.cache_data
def load_data(path):
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        if 'ID' in df.columns: df = df.drop(columns=['ID'])
        df['Kulüp'] = df['Kulüp'].fillna('Kulüpsüz').astype(str)
        df['Mevki'] = df['Mevki'].fillna('-').astype(str)
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        return df
    except: return None

df = load_data("players_export.csv")

if df is not None:
    # ⚔️ Karşılaştırma
    with st.expander("⚔️ OYUNCU KARŞILAŞTIRMA PANELİ"):
        oyuncu_listesi = ["Seçiniz..."] + sorted([x for x in df['Oyuncu'].unique() if isinstance(x, str)])
        p1 = st.selectbox("1. Oyuncu:", oyuncu_listesi, key="p1")
        p2 = st.selectbox("2. Oyuncu:", oyuncu_listesi, key="p2")
        if p1 != "Seçiniz..." and p2 != "Seçiniz...":
            d1, d2 = df[df['Oyuncu'] == p1].iloc[0], df[df['Oyuncu'] == p2].iloc[0]
            st.metric(f"{p1} vs {p2}", f"PA: {d1['PA']} - {d2['PA']}", f"Yaş: {d1['Yaş']} - {d2['Yaş']}")

    # 🏰 Takım Seçimi
    takimlar = ["Tüm Takımlar"] + sorted([t for t in df['Kulüp'].unique() if isinstance(t, str)])
    secilen_takim = st.selectbox("🏰 Takım Seç:", takimlar)

    # 🔍 Filtreler
    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
    f_mevki = st.multiselect("⚽ Mevki Seç:", list(mevki_sozlugu.keys()))
    f_yas = st.slider("🎂 Yaş:", 14, 45, (14, 25))
    f_pa = st.slider("🔥 PA:", 0, 200, (130, 200))
    search = st.text_input("🔍 İsimle Ara:")
    st.markdown("</div>", unsafe_allow_html=True)

    # Filtreleme Başlıyor
    filtered = df.copy()
    if secilen_takim != "Tüm Takımlar": filtered = filtered[filtered['Kulüp'] == secilen_takim]
    
    filtered = filtered[
        (filtered['Oyuncu'].str.contains(search, case=False, na=False)) &
        (filtered['Yaş'] >= f_yas[0]) & (filtered['Yaş'] <= f_yas[1]) &
        (filtered['PA'] >= f_pa[0]) & (filtered['PA'] <= f_pa[1])
    ]

    # AKILLI MEVKİ ARAMA (Burası sorunu çözen yer)
    if f_mevki:
        # Regex (düzenli ifadeler) kullanarak FM yazım stillerini yakalıyoruz
        karsiliklar = [mevki_sozlugu[m] for m in f_mevki]
        patterns = '|'.join([f"\\{k}" if "(" in k else k for k in karsiliklar])
        filtered = filtered[filtered['Mevki'].str.contains(patterns, case=False, na=False, regex=True)]

    st.subheader(f"✅ {len(filtered)} Oyuncu")
    # Mobil uyumlu tablo görünümü
    st.dataframe(filtered[['Oyuncu', 'Yaş', 'PA', 'Mevki', 'Kulüp', 'Değer']], use_container_width=True)
else:
    st.error("Veri dosyası bulunamadı!")
