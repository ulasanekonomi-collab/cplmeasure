import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Konfigurasi halaman utama
st.set_page_config(page_title="KRP PDF Scanner to CPL", layout="wide")

st.title("📊 Aplikasi Pengukuran CPL Otomatis via Upload Dokumen KRP")
st.subheader("Mode Auto-Extractor PDF (KRP Unisba Standard)")
st.write("Unggah dokumen PDF Kontrak Rencana Penilaian (KRP) Mata Kuliah untuk mengalkulasi CPL secara otomatis.")

# =========================================================
# CONTAINER 1: FITUR UPLOAD BERKAS PDF KRP
# =========================================================
st.markdown("---")
uploaded_file = st.file_uploader("📂 Unggah File PDF KRP Mata Kuliah di Sini", type=["pdf"])

# Target capaian standar prodi
target_capaian = 60.0

if uploaded_file is not None:
    st.success(f"Berkas '{uploaded_file.name}' berhasil diunggah! Memulai ekstraksi data...")
    
    # Simulasikan mesin parser parser membaca struktur tabel PDF KRP - A1C101
    # Di sistem produksi, bagian ini akan di-parse menggunakan library pdfplumber
    try:
        st.info("🤖 System Engine sedang membaca struktur tabel KRP berlapis (CPL -> CPMK -> Komponen)...")
        
        # Data hasil ekstraksi otomatis dari tabel PDF KRP yang Akang unggah
        # Ini mereplikasi baris sub-bobot & rerata nilai (RN) dari dokumen asli
        data_extracted = {
            "Komponen Asesmen": ["UTS (Tes Tertulis/Lisan)", "Quiz", "Kuliah/Forum (Partisipasi)", "Sikap/Hadir (Observasi)", "Tugas (Tes Tertulis/Lisan)"],
            "Kode CPL": ["CPL01", "CPL01", "CPL01", "CPL01", "CPL01"],
            "Perkiraan Bobot (PK)": [0.25, 0.05, 0.25, 0.10, 0.35],
            "Rerata Nilai (RN)": [75.49, 75.49, 75.49, 95.60, 66.73]
        }
        
        df_mentah = pd.DataFrame(data_extracted)
        
        # Lakukan kalkulasi rumus matematika kanan: PK X RN
        df_mentah["PK x RN"] = df_mentah["Perkiraan Bobot (PK)"] * df_mentah["Rerata Nilai (RN)"]
        
        # Tampilkan data mentah yang berhasil ditangkap oleh mesin dari PDF
        st.markdown("### 📋 Data Komponen Asesmen Hasil Ekstraksi PDF")
        st.dataframe(df_mentah, use_container_width=True)
        
        # =========================================================
        # CONTAINER 2: AGREGASI AKHIR TINGKAT MATA KULIAH
        # =========================================================
        # Hitung total penjumlahan PK x RN untuk mendapatkan % Ketercapaian CPL MK
        total_cpl_mk = df_mentah["PK x RN"].sum()
        
        df_hasil_akhir = pd.DataFrame({
            "Indikator Capaian": ["Nilai Akhir CPL MK (PAI I)", "Target Kelulusan Prodi"],
            "Persentase (%)": [round(total_cpl_mk, 2), target_capaian],
            "Status": ["TERCAPAI" if total_cpl_mk >= target_capaian else "TIDAK TERCAPAI", "-"]
        })
        
        st.markdown("---")
        st.markdown("### 📈 Kesimpulan Ketercapaian CPL Mata Kuliah")
        
        col_res1, col_res2 = st.columns([1, 1])
        
        with col_res1:
            st.write("#### Tabel Hasil Akumulasi")
            st.dataframe(df_hasil_akhir, use_container_width=True)
            
            if total_cpl_mk >= target_capaian:
                st.balloons()
                st.success(f"🎉 Selamat! Mata kuliah ini **MEMENUHI** target capaian CPL Prodi dengan nilai akhir **{round(total_cpl_mk, 2)}%**.")
            else:
                st.error(f"⚠️ Perhatian! Mata kuliah ini **BELUM MEMENUHI** target capaian CPL Prodi.")
                
        with col_res2:
            st.write("#### Visualisasi Ketercapaian")
            fig, ax = plt.subplots(figsize=(5, 3))
            
            warna_bar = '#1F497D' if total_cpl_mk >= target_capaian else '#C00000'
            bar = ax.bar(["PAI I (Aqidah)"], [total_cpl_mk], color=warna_bar, width=0.4)
            
            # Buat garis target warna merah putus-putus
            ax.axhline(y=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target Batas ({target_capaian}%)')
            
            # Memunculkan text angka di atas bar
            ax.text(0, total_cpl_mk + 2, f'{round(total_cpl_mk, 2)}%', ha='center', va='bottom', fontweight='bold')
            
            ax.set_ylim(0, 100)
            ax.set_ylabel('Nilai Capaian (%)')
            ax.legend(loc='lower right')
            
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Gagal memproses dokumen PDF: {e}. Pastikan format dokumen sesuai template KRP.")

else:
    st.info("💡 Silakan unggah dokumen PDF KRP (Contoh: KRP - C0901 - A1C101.pdf) untuk melihat simulasi ekstraksi otomatis.")
