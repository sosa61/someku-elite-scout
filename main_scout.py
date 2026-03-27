import streamlit as st
import pandas as pd
import os

# Sayfa Ayarları (Mobil ve Geniş Ekran Uyumu)
st.set_page_config(page_title="SOMEKU ELITE SCOUT", layout="wide")

# Görsel Tasarım ve Mobil Optimizasyon
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        background-image: linear-gradient(rgba(14, 17, 23, 0.9), rgba(14, 17, 23, 0.95)),
                          url('https://images2.imgbox.com/3f/82/XG4mOqZ1_o.png'); 
        background-size: cover; background-position: center; background-attachment: fixed;
    }
    /* Tabloyu mobilde sığdırmak için font küçültme */
    .stDataFrame div[data-testid="stTable"] { font-size: 12px !important; }
    .filter-box, .compare-box {
        background-color: rgba(20, 20, 20, 0.98);
        padding: 15px; border-radius: 15px; border: 1px solid #00D2FF;
        margin-bottom: 15px;
    }
    h1 { text-shadow: 2px 2px 10px #00D2FF; font-size: 24px !important; text-align: center; color: #00D2FF; }
    label { color: #FFFFFF !important; font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>🌪️ SOMEKU ELITE SCOUT</h1>", unsafe_allow_html=True)

# Mevki Eşleştirme Sözlüğü (Hata payını sıfırlamak için İngilizce kodlarla çalışır)
mevki_sozlugu = {
    "Kaleci": "GK", "Stoper": "DC", "Sağ Bek": "DR", "Sol Bek": "DL",
    "Ön Libero": "DM", "Merkez Orta Saha": "MC", "Sağ Kanat": "AMR",
    "Sol Kanat": "AML", "On Numara": "AMC", "Forvet": "ST"
}

@st.cache_data
def load_data(path):
    if not os.path.exists(path): return None
    try:
        df = pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        df.columns = ['ID', 'Oyuncu', 'Yaş', 'CA', 'PA', 'Ülke', 'Kulüp', 'Değer', 'Mevki', 'Rat', 'Pot_Rat'][:len(df.columns)]
        if 'ID' in df.columns: df = df.drop(columns=['ID'])
        df['PA'] = pd.to_numeric(df['PA'], errors='coerce').fillna(0).astype(int)
        df['Yaş'] = pd.to_numeric(df['Yaş'], errors='coerce').fillna(0).astype(int)
        return df
    except: return None

df = load_data("players_export.csv")

if df is not None:
    # --- 1. OYUNCU KARŞILAŞTIRMA (ARTIK ANA EKRANDA) ---
    with st.expander("⚔️ OYUNCU KARŞILAŞTIRMA PANELİ", expanded=False):
        st.markdown("<div class='compare-box'>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        oyuncu_listesi = ["Seçiniz..."] + sorted(df['Oyuncu'].unique().tolist())
        p1 = c1.selectbox("1. Oyuncu:", oyuncu_listesi, key="p1")
        p2 = c2.selectbox("2. Oyuncu:", oyuncu_listesi, key="p2")
        
        if p1 != "Seçiniz..." and p2 != "Seçiniz...":
            d1 = df[df['Oyuncu'] == p1].iloc[0]
            d2 = df[df['Oyuncu'] == p2].iloc[0]
            col_a, col_b = st.columns(2)
            col_a.metric(p1, f"PA: {d1['PA']}", f"Yaş: {d1['Yaş']}")
            col_b.metric(p2, f"PA: {d2['PA']}", f"Yaş: {d2['Yaş']}")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. TAKIMLARA GÖRE BAK (YENİ ÖZELLİK) ---
    secilen_takim = st.selectbox("🏰 Takım Seç ve Kadroya Bak:", ["Tüm Takımlar"] + sorted(df['Kulüp'].unique().tolist()))

    # --- 3. FİLTRELEME PANELİ ---
    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
    f_mevki = st.multiselect("⚽ Mevki (Türkçe seçin, İngilizce aranır):", list(mevki_sozlugu.keys()))
    col_x, col_y = st.columns(2)
    f_yas = col_x.slider("🎂 Yaş:", 14, 45, (14, 25))
    f_pa = col_y.slider("🔥 PA:", 0, 200, (130, 200))
    search = st.text_input("🔍 İsimle Ara:", placeholder="Oyuncu adı...")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- FİLTRELEME MANTIĞI ---
    filtered = df.copy()
    if secilen_takim != "Tüm Takımlar":
        filtered = filtered[filtered['Kulüp'] == secilen_takim]
    
    filtered = filtered[
        (filtered['Oyuncu'].str.contains(search, case=False, na=False)) &
        (filtered['Yaş'] >= f_yas[0]) & (filtered['Yaş'] <= f_yas[1]) &
        (filtered['PA'] >= f_pa[0]) & (filtered['PA'] <= f_pa[1])
    ]

    if f_mevki:
        ing_mevkiler = [mevki_sozlugu[m] for m in f_mevki]
        # Regex ile "veya" mantığı: Herhangi birini içeriyorsa getir
        filtered = filtered[filtered['Mevki'].str.contains('|'.join(ing_mevkiler), case=False, na=False)]

    # --- MOBİL UYUMLU TABLO ---
    st.subheader(f"✅ {len(filtered)} Oyuncu")
    # Mobilde sığması için sadece en önemli sütunları gösteriyoruz
    mobil_df = filtered[['Oyuncu', 'Yaş', 'PA', 'Mevki', 'Kulüp', 'Değer']]
    st.dataframe(mobil_df, use_container_width=True, height=400)

else:
    st.error("Veri yüklenemedi!")
