import streamlit as st
import pandas as pd
import numpy as np

def algoritma_emplasmen_utama(df):
    kapasitas_kva = 136.3
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

    # Koefisien interpolasi spesifik untuk kapasitas 136.3 kVA
    if load_kva_puncak <= 0:
        return 0
    elif load_kva_puncak <= 0.25 * kapasitas_kva:
        return 9
    elif load_kva_puncak <= 0.5 * kapasitas_kva:
        return 9 + (load_kva_puncak - 0.25 * kapasitas_kva) * (15 - 9) / (0.25 * kapasitas_kva)
    elif load_kva_puncak <= 0.75 * kapasitas_kva:
        return 15 + (load_kva_puncak - 0.5 * kapasitas_kva) * (23 - 15) / (0.25 * kapasitas_kva)
    elif load_kva_puncak <= kapasitas_kva:
        return 23 + (load_kva_puncak - 0.75 * kapasitas_kva) * (26 - 23) / (0.25 * kapasitas_kva)
    else:
        return np.nan

def algoritma_fle_emplasmen_utama(file_path):
    # baca excel
    df = pd.read_excel(file_path, header=3) 
    load_active = (df["Active power(W)"].abs())/1000
    
    kapasitas_kw = 109

    def hitung_faktor(load):
        if load == 0:
          return 0
        elif load <= 0.25 * kapasitas_kw:
            return 9
        elif load <= 0.5 * kapasitas_kw:
            return 9 + (load - 0.25 * kapasitas_kw) * (15 - 9) / (0.25 * kapasitas_kw)
        elif load <= 0.75 * kapasitas_kw:
            return 15 + (load - 0.5 * kapasitas_kw) * (23 - 15) / (0.25 * kapasitas_kw)
        elif load <= kapasitas_kw:
            return 23 + (load - 0.75 * kapasitas_kw) * (26 - 23) / (0.25 * kapasitas_kva)
        else:
            return np.nan

    # apply fungsi ke setiap nilai load_active
    koef_genset = load_active.apply(hitung_faktor)

    # filter hanya load > 0
    koef_nonzero = koef_genset[load_active > 0]

    # return rata-rata (tanpa nilai 0)
    return koef_nonzero.mean()

def algoritma_afdeling_lain(df, kapasitas_kva=80):  # kapasitas default sementara
    time_col = df.columns[0]
    load_col = df.columns[1]

    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=[time_col])
    df['load_kw'] = pd.to_numeric(df[load_col], errors='coerce').abs().round(1)
    jam = df[time_col].dt.hour

    waktu_puncak = ((jam >= 4) & (jam < 6)) | ((jam >= 17) & (jam < 23))
    med_puncak = df.loc[waktu_puncak & (df['load_kw'] > 1), 'load_kw'].median()
    load_kva_puncak = med_puncak / 0.95 if med_puncak is not None else 0  # efisiensi berbeda

    # Bisa disesuaikan interpolasi-nya jika kurvanya berbeda
    if load_kva_puncak <= 0:
        return 0
    elif load_kva_puncak <= 0.25 * kapasitas_kva:
        return 8
    elif load_kva_puncak <= 0.5 * kapasitas_kva:
        return 8 + (load_kva_puncak - 0.25 * kapasitas_kva) * (14 - 8) / (0.25 * kapasitas_kva)
    elif load_kva_puncak <= 0.75 * kapasitas_kva:
        return 14 + (load_kva_puncak - 0.5 * kapasitas_kva) * (21 - 14) / (0.25 * kapasitas_kva)
    elif load_kva_puncak <= kapasitas_kva:
        return 21 + (load_kva_puncak - 0.75 * kapasitas_kva) * (25 - 21) / (0.25 * kapasitas_kva)
    else:
        return np.nan

st.image("akartha_energy_logo.jpeg", width=200) 

st.title("🔧 Perhitungan Koefisien & Konsumsi BBM Genset")

# Pilih Project
project = st.selectbox("Pilih Project:", ["Alpha", "Bravo"])

# Pilih Site berdasarkan Project
if project == "Alpha":
    lokasi = st.selectbox("Pilih lokasi site:", [
        "Alpha - Emplasmen Utama",
        "Alpha - Afdelling 1&2",
        "Alpha - Afdelling 3&5",
        "Alpha - Afdelling 4&6"
    ])
elif project == "Bravo":
    lokasi = st.selectbox("Pilih lokasi site:", [
        "Bravo - FLE 1",
        "Bravo - FLE EU",
        "Bravo - FLE 3",
        "Bravo - FLE 4",
        "Bravo - FLE 5 / SGE Emplasmen Utama & 1",
        "Bravo - SGE 2",
        "Bravo - SGE 3",
        "Bravo - SGE 4",
        "Bravo - SGE 5"
    ])


hm_awal = st.number_input("Masukkan Hour Meter Awal (HM Awal)", value=0.0)
hm_akhir = st.number_input("Masukkan Hour Meter Akhir (HM Akhir)", value=0.0)

if lokasi in ["Bravo - FLE EU", "Bravo - FLE 1"]:
    uploaded_file = st.file_uploader("Upload File Data Beban per Jam (Excel) dari FusionSolar", type=["xlsx", "xls"])
else:
    uploaded_file = st.file_uploader("Upload File Data Beban per Jam (CSV) dari iSolarcloud", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        if lokasi == "Alpha - Emplasmen Utama":
            koef = algoritma_emplasmen_utama(df)

        elif lokasi == "Bravo - FLE EU":
            koef = algoritma_fle_emplasmen_utama(df)
        else:
            koef = algoritma_afdeling_lain(df)  # kapasitas_kva bisa dibuat dropdown di tahap berikutnya

        liter = koef * (hm_akhir - hm_awal)

        st.success("✅ Perhitungan Berhasil!")
        st.write(f"**Koefisien Genset**: {koef:.2f}")
        st.write(f"**Total Konsumsi BBM**: {liter:.2f} liter")

    except Exception as e:
        st.error(f"❌ Terjadi error saat memproses data: {e}")



