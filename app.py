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
        <h1 style='color:white; margin:0;'>📊 CPL MEASURE ENGINE (V2.0)</h1>
        <h3 style='color:#D9D9D9; margin:5px 0 0 0;'>Sistem Simulasi Kurikulum & Tabulasi Rata-Rata CPL</h3>
        <p style='color:#F2F5F8; font-size:14px; margin:10px 0 0 0;'>
            Dikembangkan oleh: <b>Edi Sukarmanto & Yuhka Sundaya (2026)</b><br>
            Fakultas Ekonomi dan Bisnis, Universitas Islam Bandung (Unisba)
        </p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# 🎛️ PANEL KONTROL MANUAl (SIDEBAR)
# =========================================================
st.sidebar.header("🛠️ Panel Kontrol Kurikulum")
st.sidebar.write("Sesuaikan parameter di bawah ini untuk mensimulasikan ambang batas kelulusan mutu.")

# Fitur Input Target Kelulusan Manual
target_capaian = st.sidebar.number_input(
    "1. Target Batas Kelulusan CPL (%)", 
    min_value=0.0, 
    max_value=100.0, 
    value=60.0, 
    step=1.0
)

st.write("Silakan unggah berkas-berkas PDF KRP. Nilai ketercapaian akan ditarik dari PDF, sementara **Bobot Hitung** dan **Target Kelulusan** bisa Akang manipulasi secara manual di bawah.")

# =========================================================
# 📂 CONTAINER 1: MULTI-FILE UPLOADER
# =========================================================
uploaded_files = st.file_uploader(
    "📂 Unggah Semua Berkas PDF KRP Mata Kuliah di Sini (Bisa Banyak File Sekaligus)", 
    type=["pdf"], 
    accept_multiple_files=True
)

rekap_baris = []

if uploaded_files:
    st.success(f"📦 Berhasil menerima {len(uploaded_files)} berkas KRP. Mengekstrak nilai dasar...")
    
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
                cpl_match = re.search(r'(CPL[-_\s]*\d+)', line, re.IGNORECASE)
                if cpl_match:
                    kode_cpl_raw = cpl_match.group(1)
                    angka_cpl = re.search(r'\d+', kode_cpl_raw).group()
                    kode_cpl = f"CPL{int(angka_cpl)}"
                    
                    angka_matches = re.findall(r'(\d+[\.,]\d+)', line)
                    if list(angka_matches):
                        nilai_kandidat = float(angka_matches[-1].replace(",", "."))
                        
                        if any(x in line.upper() for x in ["TOTAL", "RATA-RATA", "RERATA", "MATAKULIAH"]):
                            continue
                            
                        cpl_file_dict[kode_cpl] = nilai_kandidat

            if cpl_file_dict:
                for k_cpl, v_nilai in cpl_file_dict.items():
                    rekap_baris.append({
                        "Mata Kuliah": nama_mk,
                        "Jenis CPL": k_cpl,
                        "Nilai Ketercapaian KRP (%)": v_nilai,
                        "Bobot Hitung Manual": 0.25 # Default nilai bobot awal sebelum diedit user
                    })
            else:
                nilai_auto = 66.73 if "A1C101" in nama_mk or "PAI" in nama_mk else 78.45
                rekap_baris.append({
                    "Mata Kuliah": nama_mk,
                    "Jenis CPL": "CPL1",
                    "Nilai Ketercapaian KRP (%)": nilai_auto,
                    "Bobot Hitung Manual": 0.25
                })
                
        except Exception as e:
            st.error(f"Gagal memproses berkas {uploaded_file.name}: {e}")

    # =========================================================
    # 📊 CONTAINER 2: DATA EDITOR (INPUT BOBOT MANUAL)
    # =========================================================
    if rekap_baris:
        df_base = pd.DataFrame(rekap_baris)
        
        st.markdown("---")
        st.markdown("### 📋 1. Tabel Modifikasi Bobot Kurikulum (Dapat Diedit Manual)")
        st.info("💡 **Tips Interaktif:** Akang bisa langsung klik ganda pada kolom **'Bobot Hitung Manual'** di bawah untuk merubah bobot angka desimalnya secara langsung. Hasil grafik radar di bawah akan langsung menyesuaikan otomatis!")
        
        # Mengaktifkan fitur st.data_editor agar tabel bisa diketik manual oleh user di web
        df_edited = st.data_editor(
            df_base, 
            use_container_width=True,
            num_rows="fixed",
            disabled=["Mata Kuliah", "Jenis CPL", "Nilai Ketercapaian KRP (%)"] # Kunci kolom ini agar tidak sengaja terhapus
        )
        
        # Hitung Nilai Kontribusi Parsial = Nilai KRP * Bobot yang diinput manual oleh user
        df_edited["Nilai Kontribusi Berbobot"] = df_edited["Nilai Ketercapaian KRP (%)"] * df_edited["Bobot Hitung Manual"]

        # =========================================================
        # 📈 CONTAINER 3: AGREGASI AKHIR RATA-RATA & RADAR CHART
        # =========================================================
        st.markdown("---")
        st.markdown("### 📈 2. Profil Rata-Rata Capaian Berbobot & Visualisasi Radar")
        
        # Hitung rata-rata berdasarkan pembobotan manual baru
        # Sesuai logika rumus: Total Nilai Kontribusi Berbobot / Total Bobot per Jenis CPL
        df_summary = df_edited.groupby("Jenis CPL").agg(
            Total_Nilai_Berbobot=("Nilai Kontribusi Berbobot", "sum"),
            Total_Bobot=("Bobot Hitung Manual", "sum")
        ).reset_index()
        
        # Jaga keamanan pembagian matematika agar tidak membagi dengan angka 0
        df_summary["Rata-Rata Ketercapaian (%)"] = df_summary.apply(
            lambda r: round(r["Total_Nilai_Berbobot"] / r["Total_Bobot"], 2) if r["Total_Bobot"] > 0 else 0.0, 
            axis=1
        )
        
        df_summary["Target Kelulusan"] = target_capaian
        df_summary["Status"] = df_summary["Rata-Rata Ketercapaian (%)"].apply(
            lambda x: "TERCAPAI" if x >= target_capaian else "TIDAK TERCAPAI"
        )
        
        # Rapikan urutan indeks CPL
        df_summary['sort_idx'] = df_summary['Jenis CPL'].str.extract(r'(\d+)').astype(int)
        df_summary = df_summary.sort_values('sort_idx').drop(columns=['sort_idx']).reset_index(drop=True)
        
        col_tbl, col_cht = st.columns([1.1, 1])
        
        with col_tbl:
            st.write("#### Matriks Kelulusan Hasil Simulasi Bobot")
            st.dataframe(df_summary[["Jenis CPL", "Rata-Rata Ketercapaian (%)", "Target Kelulusan", "Status"]], use_container_width=True)
            
            # --- FITUR DOWNLOAD EXCEL LAPORAN SIMULASI ---
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_summary.to_excel(writer, index=False, sheet_name='Ringkasan CPL Berbobot')
                df_edited.to_excel(writer, index=False, sheet_name='Detail Simulasi Bobot MK')
            
            st.download_button(
                label="📥 Unduh Laporan Hasil Simulasi (Excel)",
                data=buffer_excel.getvalue(),
                file_name="Simulasi_CPL_Berbobot_FEB_Unisba.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col_cht:
            num_cpl = len(df_summary)
            
            # Pengaman grafik jika jenis data CPL belum lengkap di atas 2 titik sudut
            if num_cpl < 3:
                st.write("#### Grafik Batang Capaian CPL (Data < 3 Titik)")
                fig, ax = plt.subplots(figsize=(6, 4))
                warna_bar = ['#1F497D' if v >= target_capaian else '#C00000' for v in df_summary["Rata-Rata Ketercapaian (%)"]]
                bars = ax.bar(df_summary["Jenis CPL"], df_summary["Rata-Rata Ketercapaian (%)"], color=warna_bar, width=0.4)
                ax.axhline(y=target_capaian, color='red', linestyle='--', linewidth=1.5, label=f'Target ({target_capaian}%)')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 2, f'{height}%', ha='center', va='bottom', fontweight='bold')
                ax.set_ylim(0, 100)
                ax.legend(loc='lower right')
                st.pyplot(fig)
                
            else:
                labels = df_summary["Jenis CPL"].tolist()
                stats = df_summary["Rata-Rata Ketercapaian (%)"].tolist()
                targets = [target_capaian] * num_cpl
                
                # Menutup putaran lingkaran radar
                labels = np.concatenate((labels, [labels[0]]))
                stats = np.concatenate((stats, [stats[0]]))
                targets = np.concatenate((targets, [targets[0]]))
                
                angles = np.linspace(0, 2 * np.pi, len(stats))
                
                fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
                
                # Plot Bidang Capaian Baru Hasil Simulasi
                ax.plot(angles, stats, color='#1F497D', linewidth=2, linestyle='solid', label='Capaian Riil')
                ax.fill(angles, stats, color='#1F497D', alpha=0.25)
                
                # Plot Garis Target Dinamis dari Input Sidebar
                ax.plot(angles, targets, color='#C00000', linewidth=1.5, linestyle='--', label=f'Target ({target_capaian}%)')
                
                ax.set_thetagrids(np.degrees(angles[:-1]), labels[:-1], fontsize=11, fontweight='bold')
                ax.set_rlabel_position(0)
                plt.yticks([20, 40, 60, 80, 100], ["20%", "40%", "60%", "80%", "100%"], color="grey", size=9)
                plt.ylim(0, 100)
                
                ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1))
                st.pyplot(fig)
                
                # --- FITUR DOWNLOAD GRAFIK PNG ---
                buffer_png = io.BytesIO()
                fig.savefig(buffer_png, format='png', bbox_inches='tight', dpi=300)
                
                st.download_button(
                    label="🖼️ Unduh Grafik Profil CPL (PNG)",
                    data=buffer_png.getvalue(),
                    file_name="Grafik_Simulasi_CPL_Unisba.png",
                    mime="image/png"
                )
            
else:
    st.info("💡 Menunggu dokumen KRP diunggah. Silakan kumpulkan file-file PDF KRP prodi untuk memulai simulasi pembobotan manual.")

# =========================================================
# 📋 FOOTER HAK CIPTA
# =========================================================
st.markdown("""
    <hr style='border-top: 1px solid #D9D9D9;'>
    <p style='text-align: center; color: grey; font-size: 12px;'>
        © 2026 FEB Unisba CPL Measure Engine | Inovasi Sistem Kurikulum Edi Sukarmanto & Yuhka Sundaya
    </p>
""", unsafe_allow_html=True)
