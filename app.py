import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import re

# 1. Konfigurasi Halaman Utama Streamlit
st.set_page_config(page_title="Tabulasi CPL Akurat", layout="wide")

st.title("📊 Sistem Akumulasi & Tabulasi Rata-Rata CPL Prodi")
st.subheader("Engine: Ekstraksi Baris Tabel '% Ketercapaian CPL MK'")
st.write("Unggah banyak file PDF KRP sekaligus. Sistem akan membaca matriks tabel secara presisi untuk menghitung rata-rata per jenis CPL.")

target_capaian = 60.0

# =========================================================
# 📂 CONTAINER 1: MULTI-FILE UPLOADER
# =========================================================
st.markdown("---")
uploaded_files = st.file_uploader(
    "📂 Unggah Semua Berkas PDF KRP Mata Kuliah (Bisa Banyak File Sekaligus)", 
    type=["pdf"], 
    accept_multiple_files=True
)

rekap_baris = []

if uploaded_files:
    st.success(f"📦 Berhasil menerima {len(uploaded_files)} berkas KRP. Memulai pemindaian tabel...")
    
    for uploaded_file in uploaded_files:
        try:
            nama_mk = uploaded_file.name.split(".")[0].replace("KRP - ", "")
            
            # Membuka PDF menggunakan pdfplumber untuk deteksi struktur tabel murni
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    # Ekstrak seluruh tabel yang ada di dalam halaman terkait
                    tables = page.extract_tables()
                    
                    for table in tables:
                        for row in table:
                            # Amankan baris kosong atau baris pendek yang bukan bagian data utama
                            if not row or len(row) < 6:
                                continue
                            
                            # Kolom 1 (Index 0) biasanya berisi Kode CPL (misal: CPL01)
                            cpl_cell = str(row[0]).strip() if row[0] else ""
                            
                            # Kolom Terakhir (Index -1) berisi % Ketercapaian CPL MK
                            nilai_cell = str(row[-1]).strip() if row[-1] else ""
                            
                            # Saringan 1: Cek apakah kolom pertama mengandung kata kunci 'CPL'
                            cpl_match = re.search(r'(CPL[-_\s]*\d+)', cpl_cell, re.IGNORECASE)
                            
                            if cpl_match:
                                # Bersihkan format CPL (misal: CPL01 -> CPL1)
                                angka_cpl = re.search(r'\d+', cpl_match.group(1)).group()
                                kode_cpl = f"CPL{int(angka_cpl)}"
                                
                                # Saringan 2: Ambil angka desimal kelulusan di kolom paling kanan
                                # Regex mencari pola angka seperti 75.49 atau 66,73
                                nilai_match = re.search(r'(\d+[\.,]\d+)', nilai_cell)
                                
                                if nilai_match:
                                    nilai_cpl = float(nilai_match.group(1).replace(",", "."))
                                    
                                    # Abaikan baris penutup jika terbawa ke dalam saringan (seperti total atau rata-rata makro)
                                    if "TOTAL" in cpl_cell.upper() or "RATA" in cpl_cell.upper():
                                        continue
                                        
                                    rekap_baris.append({
                                        "Mata Kuliah": nama_mk,
                                        "Jenis CPL": kode_cpl,
                                        "% Ketercapaian CPL MK": nilai_cpl
                                    })
                                    
        except Exception as e:
            st.error(f"Gagal memproses berkas {uploaded_file.name}: {e}")

    # =========================================================
    # 📊 CONTAINER 2: REKAPITULASI & HITUNG RATA-RATA
    # =========================================================
    if rekap_baris:
        df_rekap = pd.DataFrame(rekap_baris)
        
        # Bersihkan duplikasi baris identik yang sering muncul akibat merge cell pada PDF
        df_rekap = df_rekap.drop_duplicates().reset_index(drop=True)
        
        st.markdown("---")
        st.markdown("### 📋 1. Tabel Hasil Ekstraksi Baris Kolom Terakhir KRP")
        st.dataframe(df_rekap, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📈 2. Hasil Rata-Rata Capaian per Jenis CPL")
        
        # LOGIKA INTI: Hitung rata-rata berdasarkan kelompok Jenis CPL (CPL1, CPL2, dst)
        df_rata_rata = df_rekap.groupby("Jenis CPL")["% Ketercapaian CPL MK"].mean().reset_index()
        df_rata_rata.columns = ["Jenis CPL", "Rata-Rata Ketercapaian (%)"]
        df_rata_rata["Rata-Rata Ketercapaian (%)"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].round(2)
        df_rata_rata["Target Kelulusan"] = target_capaian
        df_rata_rata["Status"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].apply(
            lambda x: "TERCAPAI" if x >= target_capaian else "TIDAK TERCAPAI"
        )
        
        col_tbl, col_cht = st.columns([1, 1.2])
        
        with col_tbl:
            st.write("#### Matriks Gabungan Nilai CPL Prodi")
            st.dataframe(df_rata_rata, use_container_width=True)
            
        with col_cht:
            st.write("#### Grafik Batang Rata-Rata Capaian CPL")
            fig, ax = plt.subplots(figsize=(6, 3.5))
            
            warna_bar = ['#1F497D' if v >= target_capaian else '#C00000' for v in df_rata_rata["Rata-Rata Ketercapaian (%)"]]
            bars = ax.bar(df_rata_rata["Jenis CPL"], df_rata_rata["Rata-Rata Ketercapaian (%)"], color=warna_bar, width=0.4)
            
            ax.axhline(y=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target ({target_capaian}%)')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2, f'{height}%',
                        ha='center', va='bottom', fontweight='bold', fontsize=10)
                        
            ax.set_ylim(0, 100)
            ax.set_ylabel('Nilai Rata-Rata (%)')
            ax.legend(loc='lower right')
            st.pyplot(fig)
            
    else:
        st.warning("⚠️ Dokumen berhasil dibaca, namun tidak ditemukan baris tabel yang cocok dengan kriteria CPL.")

else:
    st.info("💡 Menunggu dokumen KRP diunggah. Silakan masukkan beberapa file PDF KRP sekaligus.")
