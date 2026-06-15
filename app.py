import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pdfplumber
import re

# 1. Konfigurasi Halaman Utama Streamlit
st.set_page_config(page_title="Tabulasi CPL Radar", layout="wide")

st.title("📊 Sistem Akumulasi & Tabulasi Rata-Rata CPL Prodi")
st.subheader("Engine Visualisasi Dinamis: Auto-Radar Chart Profile")
st.write("Unggah dokumen-dokumen PDF KRP sekaligus. Sistem akan mengalkulasi rata-rata kolom % Ketercapaian CPL MK dan membentuk Grafik Radar.")

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
            
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 6:
                                continue
                            
                            cpl_cell = str(row[0]).strip() if row[0] else ""
                            nilai_cell = str(row[-1]).strip() if row[-1] else ""
                            
                            cpl_match = re.search(r'(CPL[-_\s]*\d+)', cpl_cell, re.IGNORECASE)
                            
                            if cpl_match:
                                angka_cpl = re.search(r'\d+', cpl_match.group(1)).group()
                                kode_cpl = f"CPL{int(angka_cpl)}"
                                
                                nilai_match = re.search(r'(\d+[\.,]\d+)', nilai_cell)
                                
                                if nilai_match:
                                    nilai_cpl = float(nilai_match.group(1).replace(",", "."))
                                    
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
    # 📊 CONTAINER 2: HITUNG RATA-RATA & AGREGASI
    # =========================================================
    if rekap_baris:
        df_rekap = pd.DataFrame(rekap_baris).drop_duplicates().reset_index(drop=True)
        
        st.markdown("### 📋 1. Tabel Tabulasi Hasil Ekstraksi Kolom Terakhir KRP")
        st.dataframe(df_rekap, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📈 2. Hasil Rata-Rata Capaian & Profil Radar CPL")
        
        # Agregasi Rata-Rata murni per kelompok jenis CPL
        df_rata_rata = df_rekap.groupby("Jenis CPL")["% Ketercapaian CPL MK"].mean().reset_index()
        df_rata_rata.columns = ["Jenis CPL", "Rata-Rata Ketercapaian (%)"]
        df_rata_rata["Rata-Rata Ketercapaian (%)"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].round(2)
        df_rata_rata["Target Kelulusan"] = target_capaian
        df_rata_rata["Status"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].apply(
            lambda x: "TERCAPAI" if x >= target_capaian else "TIDAK TERCAPAI"
        )
        
        # Urutkan index berdasarkan urutan CPL1, CPL2, dst agar melingkar rapi
        df_rata_rata['sort_idx'] = df_rata_rata['Jenis CPL'].str.extract(r'(\d+)').astype(int)
        df_rata_rata = df_rata_rata.sort_values('sort_idx').drop(columns=['sort_idx']).reset_index(drop=True)
        
        col_tbl, col_cht = st.columns([1, 1.2])
        
        with col_tbl:
            st.write("#### Matriks Agregasi Nilai CPL Prodi")
            st.dataframe(df_rata_rata, use_container_width=True)
            
        with col_cht:
            num_cpl = len(df_rata_rata)
            
            # 💡 LOGIKA SAFETY SWITCH: JIKA VARIABEL DATA < 3, JANGAN PAKAI RADAR (FALLBACK TO BAR CHART)
            if num_cpl < 3:
                st.write("#### Grafik Batang Capaian CPL (Data < 3 Titik)")
                fig, ax = plt.subplots(figsize=(6, 4))
                warna_bar = ['#1F497D' if v >= target_capaian else '#C00000' for v in df_rata_rata["Rata-Rata Ketercapaian (%)"]]
                bars = ax.bar(df_rata_rata["Jenis CPL"], df_rata_rata["Rata-Rata Ketercapaian (%)"], color=warna_bar, width=0.4)
                ax.axhline(y=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target ({target_capaian}%)')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 2, f'{height}%', ha='center', va='bottom', fontweight='bold')
                ax.set_ylim(0, 100)
                ax.legend(loc='lower right')
                st.pyplot(fig)
                
            else:
                st.write("#### Spider Web / Radar Chart Profil CPL Prodi")
                
                labels = df_rata_rata["Jenis CPL"].tolist()
                stats = df_rata_rata["Rata-Rata Ketercapaian (%)"].tolist()
                targets = [target_capaian] * num_cpl
                
                # Menutup putaran lingkaran grafik (Close the loop)
                labels = np.concatenate((labels, [labels[0]]))
                stats = np.concatenate((stats, [stats[0]]))
                targets = np.concatenate((targets, [targets[0]]))
                
                # Menghitung pembagian sudut keliling lingkaran radis
                angles = np.linspace(0, 2 * np.pi, len(stats))
                
                fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
                
                # Plot Garis Capaian Riil Prodi (Warna Biru Navy)
                ax.plot(angles, stats, color='#1F497D', linewidth=2, linestyle='solid', label='Capaian Riil')
                ax.fill(angles, stats, color='#1F497D', alpha=0.25)
                
                # Plot Garis Ambang Batas Target Minimal (Warna Merah Putus-putus)
                ax.plot(angles, targets, color='#C00000', linewidth=1.5, linestyle='--', label=f'Batas Target ({target_capaian}%)')
                
                # Desain kosmetik grid radar
                ax.set_thetagrids(np.degrees(angles[:-1]), labels[:-1], fontsize=11, fontweight='bold')
                ax.set_rlabel_position(0)
                plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=9)
                plt.ylim(0, 100)
                
                ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1))
                st.pyplot(fig)
            
    else:
        st.warning("⚠️ Dokumen berhasil dibaca, namun tidak ditemukan baris tabel yang cocok dengan kriteria CPL.")

else:
    st.info("💡 Menunggu dokumen KRP diunggah. Silakan seret beberapa berkas PDF KRP sekaligus untuk mengaktifkan grafik radar otomatis.")
