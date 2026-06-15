import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Pengukuran CPL Interaktif", layout="wide")

st.title("📊 Aplikasi Pengukuran Capaian Pembelajaran Lulusan (CPL)")
st.subheader("Mode Input Manual & Simulasi Kurikulum")
st.write("Masukkan nilai rata-rata mata kuliah di bawah ini untuk melihat ketercapaian CPL secara langsung.")

# =========================================================
# CONTAINER 1: INPUT MANUAL OLEH USER
# =========================================================
st.markdown("### 📝 Form Input Nilai Mata Kuliah")

col1, col2 = st.columns(2)

with col1:
    st.info("🎯 **Komponen Kelompok CPL1**")
    nilai_pai1 = st.number_input("PAI I (Aqidah) - Bobot 0.35", min_value=0.0, max_value=100.0, value=78.60, step=1.0)
    nilai_pai3 = st.number_input("PAI III (Fiqih Muamalat) - Bobot 0.35", min_value=0.0, max_value=100.0, value=78.41, step=1.0)
    nilai_pai4 = st.number_input("PAI IV (Akhlaq) - Bobot 0.30", min_value=0.0, max_value=100.0, value=80.86, step=1.0)

with col2:
    st.info("🎯 **Komponen Kelompok CPL2**")
    nilai_pancasila = st.number_input("Pancasila - Bobot 0.25", min_value=0.0, max_value=100.0, value=84.35, step=1.0)
    nilai_kwn = st.number_input("Kewarganegaraan - Bobot 0.25", min_value=0.0, max_value=100.0, value=53.38, step=1.0)
    nilai_pai5 = st.number_input("PAI V (Sejarah Islam) - Bobot 0.25", min_value=0.0, max_value=100.0, value=89.05, step=1.0)
    nilai_pai6 = st.number_input("PAI VI (Peradaban Islam) - Bobot 0.25", min_value=0.0, max_value=100.0, value=75.66, step=1.0)

# =========================================================
# CONTAINER 2: PROSES KALKULASI LOGIKA (ENGINE INTERNAL)
# =========================================================
# Hitung Nilai Akhir CPL berdasarkan perkalian bobot (Logika dari REKAP 2)
cpl1_akhir = (nilai_pai1 * 0.35) + (nilai_pai3 * 0.35) + (nilai_pai4 * 0.30)
cpl2_akhir = (nilai_pancasila * 0.25) + (nilai_kwn * 0.25) + (nilai_pai5 * 0.25) + (nilai_pai6 * 0.25)

target_capaian = 60.0

# Membuat ringkasan dataframe hasil
data_hasil = {
    "Komponen CPL": ["CPL1", "CPL2"],
    "Nilai Capaian prodi": [round(cpl1_akhir, 2), round(cpl2_akhir, 2)],
    "Target": [target_capaian, target_capaian],
    "Status": [
        "TERCAPAI" if cpl1_akhir >= target_capaian else "TIDAK TERCAPAI",
        "TERCAPAI" if cpl2_akhir >= target_capaian else "TIDAK TERCAPAI"
    ]
}
df_hasil = pd.DataFrame(data_hasil)

# =========================================================
# CONTAINER 3: VISUALISASI HASIL & GRAFIK RADAR
# =========================================================
st.markdown("---")
st.markdown("### 📈 Ringkasan Ketercapaian")

res_col1, res_col2 = st.columns([1, 1])

with res_col1:
    st.write("#### Datatable Hasil Agregasi")
    st.dataframe(df_hasil, use_container_width=True)

with res_col2:
    st.write("#### Grafik Radar (Spider Web Chart)")
    
    # Setup data untuk radar chart (harus memutar/close loop)
    labels = ['CPL1', 'CPL2']
    stats = [cpl1_akhir, cpl2_akhir]
    targets = [target_capaian, target_capaian]
    
    # Agar garis grafiknya menyambung melingkar
    labels = np.concatenate((labels, [labels[0]]))
    stats = np.concatenate((stats, [stats[0]]))
    targets = np.concatenate((targets, [targets[0]]))
    
    label_loc = np.linspace(start=0, stop=2 * np.pi, num=len(stats))
    
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    
    # Gambar garis capaian riil
    ax.plot(label_loc, stats, label='Capaian Real', color='#1F497D', linewidth=2)
    ax.fill(label_loc, stats, color='#1F497D', alpha=0.2)
    
    # Gambar garis target minimal
    ax.plot(label_loc, targets, label='Target Batas', color='red', linestyle='--', linewidth=1.5)
    
    # Set pengatur sudut label
    ax.set_thetagrids(np.degrees(label_loc[:-1]), ['CPL1', 'CPL2'])
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    st.pyplot(fig)
