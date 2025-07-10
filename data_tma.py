# data_tma.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

def show():
    st.title("📊 Data Tinggi Muka Air (TMA)")
    
    # Fungsi untuk menyimpan data ke database
    def save_to_db(df):
        conn = sqlite3.connect('flood_prediction.db')
        df.to_sql('tma_data', conn, if_exists='append', index=False)
        conn.close()
    
    # Fungsi untuk memuat semua data dari database
    def load_all_data():
        conn = sqlite3.connect('flood_prediction.db')
        query = "SELECT tanggal, jam_06, jam_12, jam_18, tma_min, tma_max, tma_rata FROM tma_data"
        df = pd.read_sql(query, conn, parse_dates=['tanggal'])
        conn.close()
        return df
    
    # Fungsi untuk memproses file yang diupload
    def process_uploaded_file(uploaded_file):
        try:
            # Baca file sesuai format
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, decimal=',', parse_dates=['tanggal'], dayfirst=True)
            else:
                df = pd.read_excel(uploaded_file, decimal=',')
            
            # Pastikan kolom yang diperlukan ada
            required_cols = ['tanggal', 'jam_06', 'jam_12', 'jam_18', 'tma_min', 'tma_max', 'tma_rata']
            if not all(col in df.columns for col in required_cols):
                raise ValueError("Format file tidak sesuai. Pastikan kolom yang diperlukan ada.")
            
            # Konversi format tanggal
            df['tanggal'] = pd.to_datetime(df['tanggal'], format='%d/%m/%Y', errors='coerce')
            
            # Konversi nilai numerik
            numeric_cols = ['jam_06', 'jam_12', 'jam_18', 'tma_min', 'tma_max', 'tma_rata']
            for col in numeric_cols:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
            
            # Bersihkan data yang hilang
            if df.isnull().values.any():
                st.warning("Ada data yang hilang (NaN). Data akan dibersihkan otomatis.")
                df = df.dropna()
            
            return df
        
        except Exception as e:
            raise ValueError(f"Gagal memproses file: {str(e)}")

    # Coba muat data yang sudah ada dari database
    if 'current_data' not in st.session_state:
        saved_data = load_all_data()
        if not saved_data.empty:
            st.session_state['current_data'] = saved_data
            st.success("Data sebelumnya berhasil dimuat dari database!")

    # Upload file baru
    uploaded_file = st.file_uploader("Upload file data TMA (CSV/Excel)", type=['xlsx', 'csv'])

    if uploaded_file is not None:
        try:
            # Proses data
            new_data = process_uploaded_file(uploaded_file)
            
            # Simpan ke database
            save_to_db(new_data)
            
            # Gabungkan dengan data existing jika ada
            if 'current_data' in st.session_state:
                combined_data = pd.concat([st.session_state['current_data'], new_data], ignore_index=True)
                combined_data = combined_data.drop_duplicates(subset=['tanggal'], keep='last')
                combined_data = combined_data.sort_values('tanggal')
            else:
                combined_data = new_data
            
            st.session_state['current_data'] = combined_data
            st.success(f"Data berhasil diproses dan disimpan ke database! Tahun data: {new_data['tanggal'].dt.year.unique()}")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

    # Tampilkan data jika ada
    if 'current_data' in st.session_state and not st.session_state['current_data'].empty:
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
            conn = sqlite3.connect('flood_prediction.db')
            c = conn.cursor()
            c.execute("DELETE FROM tma_data")
            conn.commit()
            conn.close()
            del st.session_state['current_data']
            st.success("Data berhasil direset dari database!")
            st.rerun()
        
        if st.button("🔄 Muat Ulang Data"):
            del st.session_state['current_data']
            st.rerun()
    else:
        st.warning("Belum ada data TMA yang tersimpan di database. Silakan upload file data TMA.")