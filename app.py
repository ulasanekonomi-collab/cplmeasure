import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    "Nilai Capaian Prodi": [round(cpl1_akhir, 2), round(cpl2_akhir, 2)],
    "Target": [target_capaian, target_capaian],
    "Status": [
        "TERCAPAI" if cpl1_akhir >= target_capaian else "TIDAK TERCAPAI",
        "TERCAPAI" if cpl2_akhir >= target_capaian else "TIDAK TERCAPAI"
    ]
}
df_hasil = pd.DataFrame(data_hasil)

# =========================================================
# CONTAINER 3: VISUALISASI HASIL & GRAFIK BATANG HORIZONTAL
# =========================================================
st.markdown("---")
st.markdown("### 📈 Ringkasan Ketercapaian")

res_col1, res_col2 = st.columns([1, 1])

with res_col1:
    st.write("#### Datatable Hasil Agregasi")
    st.dataframe(df_hasil, use_container_width=True)

with res_col2:
    st.write("#### Grafik Perbandingan CPL")
    
    # Membuat Bar Chart Horizontal yang aman dari error koordinat
    fig, ax = plt.subplots(figsize=(6, 3.5))
    
    # Set warna dinamis (biru jika tercapai, merah jika tidak)
    colors = ['#1F497D' if val >= target_capaian else '#C00000' for val in df_hasil["Nilai Capaian Prodi"]]
    
    bars = ax.barh(df_hasil["Komponen CPL"], df_hasil["Nilai Capaian Prodi"], color=colors, height=0.5)
    
    # Tambah garis pembatas target kelulusan prodi (Batas Red Line)
    ax.axvline(x=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target Batas ({target_capaian})')
    
    # Tambahkan label angka di ujung bar masing-masing
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2, f'{width}', 
                va='center', ha='left', fontsize=10, fontweight='bold')
                
    ax.set_xlim(0, 100)
    ax.set_xlabel('Nilai Capaian')
    ax.legend(loc='lower right')
    
    st.pyplot(fig)
