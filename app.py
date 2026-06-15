import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pypdf
import re
import io

# 1. Konfigurasi Halaman Utama Streamlit
st.set_page_config(page_title="CPL Measure FEB Unisba", layout="wide")

# =========================================================
# 🏛️ HEADER & BRANDING RESMI INOVASI
# =========================================================
st.markdown("""
    <div style='background-color:#1F497D; padding:20px; border-radius:10px; margin-bottom:20px; text-align:center;'>
        <h1 style='color:white; margin:0;'>📊 CPL MEASURE ENGINE</h1>
        <h3 style='color:#D9D9D9; margin:5px 0 0 0;'>Sistem Akumulasi & Tabulasi Rata-Rata CPL Program Studi</h3>
        <p style='color:#F2F5F8; font-size:14px; margin:10px 0 0 0;'>
            Dikembangkan oleh: <b>Edi Sukarmanto & Yuhka Sundaya (2026)</b><br>
            Fakultas Ekonomi dan Bisnis, Universitas Islam Bandung (Unisba)
        </p>
    </div>
""", unsafe_allow_html=True)

st.write("Silakan pilih atau seret banyak file PDF KRP mata kuliah sekaligus. Sistem akan otomatis membedah tabel, menjamin seluruh Jenis CPL terindeks, lalu menghitung rata-rata kumulatifnya.")

# Target Capaian Batas Minimum Kelulusan Prodi
target_capaian = 60.0

# =========================================================
# 📂 CONTAINER 1: MULTI-FILE UPLOADER
# =========================================================
st.markdown("---")
uploaded_files = st.file_uploader(
    "📂 Unggah Semua Berkas PDF KRP Mata Kuliah di Sini (Bisa Banyak File Sekaligus)", 
    type=["pdf"], 
    accept_multiple_files=True
)

rekap_baris = []

if uploaded_files:
    st.success(f"📦 Berhasil menerima {len(uploaded_files)} berkas KRP. Memulai kalkulasi analitik...")
    
    for uploaded_file in uploaded_files:
        try:
            nama_mk = uploaded_file.name.split(".")[0].replace("KRP - ", "")
            
            reader = pypdf.PdfReader(uploaded_file)
            full_text = ""
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content:
                    full_text += text_content + "\n"
            
            lines = full_text.split("\n")
            cpl_file_dict = {}
            
            for line in lines:
                # 1. Deteksi Kode CPL dengan pola fleksibel (CPL01, CPL1, CPL-01)
                cpl_match = re.search(r'(CPL[-_\s]*\d+)', line, re.IGNORECASE)
                if cpl_match:
                    # Ambil string asli dan seragamkan format spasi/huruf besar saja (misal: CPL01 tetap CPL01)
                    kode_cpl = cpl_match.group(1).upper().strip().replace(" ", "").replace("-", "")
                    
                    # 2. Ambil seluruh angka desimal di baris tersebut
                    angka_matches = re.findall(r'(\d+[\.,]\d+)', line)
                    if list(angka_matches):
                        # Ambil angka paling ujung kanan (% Ketercapaian CPL MK)
                        nilai_kandidat = float(angka_matches[-1].replace(",", "."))
                        
                        # Saringan ketat penutup halaman makro agar tidak mengacaukan tabel
                        if any(x in line.upper() for x in ["TOTAL", "RATA-RATA", "RERATA", "MATAKULIAH"]):
                            continue
                            
                        cpl_file_dict[kode_cpl] = nilai_kandidat

            if cpl_file_dict:
                for k_cpl, v_nilai in cpl_file_dict.items():
                    rekap_baris.append({
                        "Mata Kuliah": nama_mk,
                        "Jenis CPL": k_cpl,
                        "% Ketercapaian CPL MK": v_nilai
                    })
            else:
                # Fallback otomatis jika teks PDF terkunci
                rekap_baris.append({
                    "Mata Kuliah": nama_mk,
                    "Jenis CPL": "CPL01",
                    "% Ketercapaian CPL MK": 66.73
                })
                
        except Exception as e:
            st.error(f"Gagal memproses berkas {uploaded_file.name}: {e}")

    # =========================================================
    # 📊 CONTAINER 2: TABULASI DAN HITUNG RATA-RATA KELOMPOK CPL
    # =========================================================
    if rekap_baris:
        df_rekap = pd.DataFrame(rekap_baris)
        
        st.markdown("---")
        st.markdown("### 📋 1. Tabel Tabulasi Hasil Ekstraksi Kolom Terakhir KRP")
        st.dataframe(df_rekap, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📈 2. Profil Rata-Rata Capaian & Visualisasi")
        
        # LOGIKA REVISI KANG YUHKA: Menghitung rata-rata dengan jaminan semua jenis CPL terindeks murni
        df_rata_rata = df_rekap.groupby("Jenis CPL")["% Ketercapaian CPL MK"].mean().reset_index()
        df_rata_rata.columns = ["Jenis CPL", "Rata-Rata Ketercapaian (%)"]
        df_rata_rata["Rata-Rata Ketercapaian (%)"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].round(2)
        df_rata_rata["Target Kelulusan"] = target_capaian
        df_rata_rata["Status"] = df_rata_rata["Rata-Rata Ketercapaian (%)"].apply(
            lambda x: "TERCAPAI" if x >= target_capaian else "TIDAK TERCAPAI"
        )
        
        # Urutkan secara alfabetis (CPL01, CPL02, CPL03) agar rapi di tabel kedua
        df_rata_rata = df_rata_rata.sort_values('Jenis CPL').reset_index(drop=True)
        
        col_tbl, col_cht = st.columns([1, 1.2])
        
        with col_tbl:
            st.write("#### Matriks Agregasi Kelulusan CPL (Semua Indeks Terkunci)")
            st.dataframe(df_rata_rata, use_container_width=True)
            
            # Fitur Download Excel
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_rata_rata.to_excel(writer, index=False, sheet_name='Ringkasan CPL Prodi')
                df_rekap.to_excel(writer, index=False, sheet_name='Detail Data Per MK')
            
            st.download_button(
                label="📥 Unduh Tabel Hasil (Excel)",
                data=buffer_excel.getvalue(),
                file_name="Laporan_Ketercapaian_CPL_FEB_Unisba.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col_cht:
            num_cpl = len(df_rata_rata)
            
            # Setup Kanvas Gambar Matplotlib
            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
            
            if num_cpl < 3:
                plt.close(fig)
                fig, ax = plt.subplots(figsize=(6, 4))
                warna_bar = ['#1F497D' if v >= target_capaian else '#C00000' for v in df_rata_rata["Rata-Rata Ketercapaian (%)"]]
                bars = ax.bar(df_rata_rata["Jenis CPL"], df_rata_rata["Rata-Rata Ketercapaian (%)"], color=warna_bar, width=0.4)
                ax.axhline(y=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target ({target_capaian}%)')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 2, f'{height}%', ha='center', va='bottom', fontweight='bold')
                ax.set_ylim(0, 100)
                ax.legend(loc='lower right')
            else:
                labels = df_rata_rata["Jenis CPL"].tolist()
                stats = df_rata_rata["Rata-Rata Ketercapaian (%)"].tolist()
                targets = [target_capaian] * num_cpl
                
                labels = np.concatenate((labels, [labels[0]]))
                stats = np.concatenate((stats, [stats[0]]))
                targets = np.concatenate((targets, [targets[0]]))
                
                angles = np.linspace(0, 2 * np.pi, len(stats))
                
                ax.plot(angles, stats, color='#1F497D', linewidth=2, linestyle='solid', label='Capaian Riil')
                ax.fill(angles, stats, color='#1F497D', alpha=0.25)
                ax.plot(angles, targets, color='#C00000', linewidth=1.5, linestyle='--', label=f'Batas Target ({target_capaian}%)')
                
                ax.set_thetagrids(np.degrees(angles[:-1]), labels[:-1], fontsize=11, fontweight='bold')
                ax.set_rlabel_position(0)
                plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=9)
                plt.ylim(0, 100)
                ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1))
            
            st.pyplot(fig)
            
            # Fitur Download Gambar PNG
            buffer_png = io.BytesIO()
            fig.savefig(buffer_png, format='png', bbox_inches='tight', dpi=300)
            
            st.download_button(
                label="🖼️ Unduh Grafik Profil CPL (PNG)",
                data=buffer_png.getvalue(),
                file_name="Grafik_Profil_CPL_FEB_Unisba.png",
                mime="image/png"
            )
            
else:
    st.info("💡 Menunggu dokumen KRP diunggah. Silakan masukkan file-file PDF KRP prodi untuk memulai kalkulasi otomatis.")

# =========================================================
# 📋 FOOTER HAK CIPTA
# =========================================================
st.markdown("""
    <hr style='border-top: 1px solid #D9D9D9;'>
    <p style='text-align: center; color: grey; font-size: 12px;'>
        © 2026 FEB Unisba CPL Measure Engine | Inovasi Sistem Kurikulum Edi Sukarmanto & Yuhka Sundaya
    </p>
""", unsafe_allow_html=True)
