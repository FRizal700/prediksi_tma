import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import shutil
from matplotlib import gridspec


def show():
    st.title("📊 Data Tinggi Muka Air (TMA)")

    # Setup folder structure
    os.makedirs("data/uploaded", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    def process_and_save_data(file_path, filename):
        try:
            # Baca file
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path, decimal=',', parse_dates=['tanggal'], dayfirst=True)
            else:
                df = pd.read_excel(file_path, decimal=',')
            
            # Konversi format
            df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d/%m/%Y', errors='coerce')
            
            numeric_cols = ['jam_06', 'jam_12', 'jam_18', 'tma_min', 'tma_max', 'tma_rata']
            for col in numeric_cols:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            
            # Bersihkan data
            if df.isnull().values.any():
                st.warning("Ada data yang hilang (NaN). Data akan dibersihkan otomatis.")
                df = df.dropna()
            
            # Simpan file original dengan nama unik
            original_filename = f"{df['tanggal'].dt.year.min()}_{filename}"
            original_path = os.path.join("data/uploaded", original_filename)
            shutil.copyfile(file_path, original_path)
            
            return df
        
        except Exception as e:
            raise ValueError(f"Gagal memproses file: {str(e)}")

    def load_all_data():
        try:
            # Gabungkan semua file yang ada
            all_files = [f for f in os.listdir("data/uploaded") if f.endswith(('.csv', '.xlsx'))]
            dfs = []
            
            for file in all_files:
                file_path = os.path.join("data/uploaded", file)
                if file.endswith('.csv'):
                    df = pd.read_csv(file_path, decimal=',', parse_dates=['tanggal'], dayfirst=True)
                else:
                    df = pd.read_excel(file_path, decimal=',')
                
                df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d/%m/%Y', errors='coerce')
                dfs.append(df)
            
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                combined_df = combined_df.sort_values('tanggal')
                return combined_df
            return None
            
        except Exception as e:
            st.error(f"Gagal memuat data tersimpan: {str(e)}")
            return None

    # Coba muat data yang sudah ada
    if 'current_data' not in st.session_state:
        saved_data = load_all_data()
        if saved_data is not None:
            st.session_state['current_data'] = saved_data
            st.success("Data sebelumnya berhasil dimuat!")

    # Upload file baru
    uploaded_file = st.file_uploader("Upload file data TMA (CSV/Excel)", type=['xlsx', 'csv'])

    if uploaded_file is not None:
        try:
            # Simpan sementara
            temp_file = "temp_upload." + ("csv" if uploaded_file.name.endswith('.csv') else "xlsx")
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Proses data
            new_data = process_and_save_data(temp_file, uploaded_file.name)
            
            # Gabungkan dengan data existing jika ada
            if 'current_data' in st.session_state:
                combined_data = pd.concat([st.session_state['current_data'], new_data], ignore_index=True)
                combined_data = combined_data.drop_duplicates(subset=['tanggal'], keep='last')
                combined_data = combined_data.sort_values('tanggal')
            else:
                combined_data = new_data
            
            st.session_state['current_data'] = combined_data
            st.success(f"Data berhasil diproses dan disimpan! Tahun data: {new_data['tanggal'].dt.year.unique()}")
            
            # Hapus file temp
            os.remove(temp_file)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    # Tampilkan data jika ada
    if 'current_data' in st.session_state:
        df = st.session_state['current_data']
        
        # Tambahkan kolom analisis
        df['tahun'] = df['tanggal'].dt.year
        df['bulan'] = df['tanggal'].dt.month
        df['nama_bulan'] = df['tanggal'].dt.month_name()
        df['hari'] = df['tanggal'].dt.day
        
        # Info data
        st.subheader("Informasi Data")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Periode Awal", df['tanggal'].min().strftime('%d/%m/%Y'))
        with col2:
            st.metric("Periode Akhir", df['tanggal'].max().strftime('%d/%m/%Y'))
        with col3:
            st.metric("Jumlah Data", len(df))
        
        # Daftar tahun yang tersedia
        available_years = sorted(df['tahun'].unique())
        st.write(f"Tahun tersedia: {', '.join(map(str, available_years))}")
        
        # Tab utama
        tab1, tab2 = st.tabs(["📋 Data dan Visualisasi", "📈 Analisis Tahunan"])
        
        with tab1:
            # Filter data
            st.subheader("Filter Data")
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox("Pilih Tahun", available_years, key='year_filter')
            with col2:
                selected_month = st.selectbox("Pilih Bulan", 
                                            sorted(df[df['tahun'] == selected_year]['bulan'].unique()), 
                                            key='month_filter')
            
            filtered_data = df[(df['tahun'] == selected_year) & (df['bulan'] == selected_month)]
            
            # Tampilkan data
            st.subheader(f"Data Bulan {selected_month}/{selected_year}")
            st.dataframe(filtered_data)
            
            # Visualisasi
            st.subheader("Grafik Tinggi Muka Air")
            
            chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["Rata-rata Harian", "Per Jam", "Perbandingan", "Perbandingan Bulanan"])
            
            with chart_tab1:
                fig1, ax1 = plt.subplots(figsize=(10, 4))
                ax1.plot(filtered_data['hari'], filtered_data['tma_rata'], 'o-', color='blue')
                ax1.set_xlabel('Tanggal')
                ax1.set_ylabel('Tinggi Air (m)')
                ax1.set_title(f'Tinggi Muka Air Rata-rata Harian (Bulan {selected_month})')
                ax1.grid(True)
                st.pyplot(fig1)
            
            with chart_tab2:
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                jam_cols = ['jam_06', 'jam_12', 'jam_18']
                for jam in jam_cols:
                    ax2.plot(filtered_data['hari'], filtered_data[jam], 'o-', label=jam)
                ax2.set_xlabel('Tanggal')
                ax2.set_ylabel('Tinggi Air (m)')
                ax2.set_title('Tinggi Air Per Jam')
                ax2.legend()
                ax2.grid(True)
                st.pyplot(fig2)
            
            with chart_tab3:
                fig3, ax3 = plt.subplots(figsize=(10, 4))
                ax3.plot(filtered_data['hari'], filtered_data['tma_min'], 's-', label='Minimum')
                ax3.plot(filtered_data['hari'], filtered_data['tma_max'], '^-', label='Maksimum')
                ax3.plot(filtered_data['hari'], filtered_data['tma_rata'], 'o-', label='Rata-rata')
                ax3.set_xlabel('Tanggal')
                ax3.set_ylabel('Tinggi Air (m)')
                ax3.set_title('Perbandingan Tinggi Air Harian')
                ax3.legend()
                ax3.grid(True)
                st.pyplot(fig3)
                
            with chart_tab4:
                # Perbandingan bulanan untuk tahun yang dipilih
                year_data = df[df['tahun'] == selected_year]
                fig4, ax4 = plt.subplots(figsize=(12, 6))
                
                for bulan in sorted(year_data['bulan'].unique()):
                    bulan_data = year_data[year_data['bulan'] == bulan]
                    ax4.plot(bulan_data['hari'], bulan_data['tma_rata'], 
                            label=bulan_data['nama_bulan'].iloc[0],
                            marker='o')
                
                ax4.set_title(f'Perbandingan Bulanan Tinggi Air Rata-rata ({selected_year})')
                ax4.set_ylabel('Tinggi Air (m)')
                ax4.legend()
                ax4.grid(True)
                
                plt.tight_layout()
                st.pyplot(fig4)
            
            plt.close('all')

            # Hitung statistik banjir bulanan
            st.subheader("Statistik Banjir Bulanan")
            threshold = st.slider("Threshold Banjir (meter)", 1.0, 3.0, 1.6, 0.1, key='monthly_threshold')
            
            flood_days = filtered_data[filtered_data['tma_max'] > threshold]
            st.metric("Hari dengan Banjir", f"{len(flood_days)} hari")
            
            if not flood_days.empty:
                st.write("Detail Hari Banjir:")
                st.dataframe(flood_days)
        
        with tab2:
            # Analisis tahunan
            st.subheader("Analisis Tahunan")
            analysis_year = st.selectbox("Pilih Tahun untuk Analisis", available_years, key='analysis_year')
            
            year_data = df[df['tahun'] == analysis_year]
            
            # Statistik banjir tahunan
            st.subheader(f"Statistik Banjir Tahun {analysis_year}")
            annual_threshold = st.slider("Threshold Banjir (meter)", 1.0, 3.0, 1.6, 0.1, key='annual_threshold')
            
            # Hitung statistik per bulan
            monthly_stats = year_data.groupby(['bulan', 'nama_bulan']).agg(
                hari_banjir=('tma_max', lambda x: sum(x > annual_threshold)),
                tma_rata_rata=('tma_rata', 'mean'),
                tma_tertinggi=('tma_max', 'max'),
                tma_terendah=('tma_min', 'min')
            ).reset_index()
            
            # Tampilkan metrik utama
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Hari Banjir", monthly_stats['hari_banjir'].sum())
            col2.metric("TMA Rata-rata Tahunan", f"{year_data['tma_rata'].mean():.2f} m")
            col3.metric("TMA Tertinggi Tahunan", f"{year_data['tma_max'].max():.2f} m")
            
            # Visualisasi
            fig5, (ax6, ax7) = plt.subplots(1, 2, figsize=(16, 6))
            
            # Grafik batang hari banjir
            ax6.bar(monthly_stats['nama_bulan'], monthly_stats['hari_banjir'], color='salmon')
            ax6.set_title(f'Hari dengan Banjir per Bulan (Threshold: {annual_threshold}m)')
            ax6.set_ylabel('Jumlah Hari')
            ax6.tick_params(axis='x', rotation=45)
            ax6.grid(axis='y')
            
            # Grafik perkembangan TMA
            for bulan in sorted(year_data['bulan'].unique()):
                bulan_data = year_data[year_data['bulan'] == bulan]
                ax7.plot(bulan_data['hari'], bulan_data['tma_rata'], 
                        label=bulan_data['nama_bulan'].iloc[0],
                        marker='o')
            ax7.set_title('Perkembangan Tinggi Air Rata-rata')
            ax7.set_xlabel('Hari dalam Bulan')
            ax7.set_ylabel('Tinggi Air (m)')
            ax7.legend()
            ax7.grid(True)
            
            plt.tight_layout()
            st.pyplot(fig5)
            
            # Tabel statistik bulanan
            st.subheader("Detail Statistik Bulanan")
            st.dataframe(monthly_stats)
        
        # Tombol manajemen data
        st.subheader("Manajemen Data")
        if st.button("♻️ Reset Semua Data"):
            shutil.rmtree("data")
            os.makedirs("data/uploaded", exist_ok=True)
            os.makedirs("data/processed", exist_ok=True)
            del st.session_state['current_data']
            st.success("Data berhasil direset!")
            st.rerun()
        
        if st.button("🔄 Muat Ulang Data"):
            del st.session_state['current_data']
            st.rerun()