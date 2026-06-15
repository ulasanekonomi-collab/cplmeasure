import streamlit as st
import pandas as pd
from engine import hitung_cpl_prodi

st.set_page_config(page_title="Dashboard Pengukuran CPL", layout="wide")

st.title("📊 Aplikasi Pengukuran Capaian Pembelajaran Lulusan (CPL)")
st.subheader("Program Studi - Universitas")
st.write("Silakan unggah data kurikulum dan data nilai dari SISFO untuk menghitung ketercapaian.")

# Membuat kolom layout untuk upload file
col1, col2 = st.columns(2)

with col1:
    uploaded_master = st.file_uploader("1. Unggah Master Kurikulum & Bobot (CSV/XLSX)", type=["csv", "xlsx"])

with col2:
    uploaded_nilai = st.file_uploader("2. Unggah Nilai Akhir dari SISFO (CSV/XLSX)", type=["csv", "xlsx"])

# Proses perhitungan jika kedua file sudah diunggah
if uploaded_master and uploaded_nilai:
    try:
        # Membaca file master
        if uploaded_master.name.endswith('.csv'):
            df_master = pd.read_csv(uploaded_master)
        else:
            df_master = pd.read_excel(uploaded_master)
            
        # Membaca file nilai
        if uploaded_nilai.name.endswith('.csv'):
            df_nilai = pd.read_csv(uploaded_nilai)
        else:
            df_nilai = pd.read_excel(uploaded_nilai)
            
        st.success("Data berhasil diunggah! Sedang memproses perhitungan...")
        
        # Memanggil fungsi hitung dari engine.py
        df_hasil_cpl = hitung_cpl_prodi(df_master, df_nilai)
        
        # Menampilkan Ringkasan Hasil
        st.write("### 📈 Hasil Capaian CPL Tingkat Prodi")
        st.dataframe(df_hasil_cpl, use_container_width=True)
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    st.info("💡 Menunggu unggahan berkas Master Kurikulum dan Nilai SISFO untuk kalkulasi.")
