import pandas as pd

def hitung_cpl_prodi(df_master, df_nilai):
    """
    Menggabungkan data kurikulum dan nilai dari SISFO,
    lalu menghitung ketercapaian CPL secara otomatis.
    """
    # 1. Pastikan kolom kunci tidak ada whitespace dan seragam
    df_master['kode_mk'] = df_master['kode_mk'].astype(str).str.strip()
    df_nilai['kode_mk'] = df_nilai['kode_mk'].astype(str).str.strip()
    
    # 2. Gabungkan data berdasarkan Kode Mata Kuliah
    df_merge = pd.merge(df_master, df_nilai, on='kode_mk')
    
    # 3. Defensif: Konversi nilai dan bobot ke numerik (mengantisipasi error sisfonus)
    df_merge['nilai_angka'] = pd.to_numeric(df_merge['nilai_angka'], errors='coerce')
    df_merge['bobot'] = pd.to_numeric(df_merge['bobot'], errors='coerce')
    
    # 4. Hitung Nilai Parsial CPL (Nilai MK * Bobot)
    df_merge['nilai_cpl_parsial'] = df_merge['nilai_angka'] * df_merge['bobot']
    
    # 5. Agregasi total nilai per CPL tingkat Prodi
    df_cpl = df_merge.groupby('kode_cpl').agg(
        Nilai_CPL=('nilai_cpl_parsial', 'sum'),
        Target=('target_capaian', 'first')
    ).reset_index()
    
    # 6. Tentukan status ketercapaian
    df_cpl['Status'] = df_cpl.apply(
        lambda row: 'TERCAPAI' if row['Nilai_CPL'] >= row['Target'] else 'TERCAPAI SEBAGIAN', 
        axis=1
    )
    
    return df_cpl
