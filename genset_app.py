import streamlit as st
import pandas as pd
import numpy as np

def process_genset_data(df, kapasitas_kva=136.3):
    time_col = df.columns[0]
    load_col = df.columns[1]

    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    df['load_kw'] = pd.to_numeric(df[load_col], errors='coerce').abs().round(1)
    df['load_genset_flag'] = np.where(df['load_kw'] < 1, 1, 0)
    jam = df[time_col].dt.hour

    waktu_puncak = ((jam >= 4) & (jam < 6)) | ((jam >= 17) & (jam < 23))
    med_puncak = df.loc[waktu_puncak & (df['load_kw'] > 1), 'load_kw'].median()
    load_kva_puncak = med_puncak / 0.9714448 if med_puncak is not None else 0

    def interpolate_coefficient(g):
        if g <= 0:
            return 0
        elif g <= 0.25 * kapasitas_kva:
            return 9
        elif g <= 0.5 * kapasitas_kva:
            return 9 + (g - 0.25 * kapasitas_kva) * (15 - 9) / (0.25 * kapasitas_kva)
        elif g <= 0.75 * kapasitas_kva:
            return 15 + (g - 0.5 * kapasitas_kva) * (23 - 15) / (0.25 * kapasitas_kva)
        elif g <= kapasitas_kva:
            return 23 + (g - 0.75 * kapasitas_kva) * (26 - 23) / (0.25 * kapasitas_kva)
        else:
            return np.nan

    return interpolate_coefficient(load_kva_puncak)

# Streamlit Web UI
st.title("🔧 Perhitungan Koefisien & Konsumsi BBM Genset")

hm_awal = st.number_input("Masukkan Hour Meter Awal (HM Awal)", value=0.0)
hm_akhir = st.number_input("Masukkan Hour Meter Akhir (HM Akhir)", value=0.0)

uploaded_file = st.file_uploader("Upload File CSV Genset", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        coef = process_genset_data(df)
        liter = coef * (hm_akhir - hm_awal)

        st.success("✅ Perhitungan Berhasil!")
        st.write(f"**Koefisien Genset**: {coef:.2f}")
        st.write(f"**Total Konsumsi BBM**: {liter:.2f} liter")

    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses data: {e}")