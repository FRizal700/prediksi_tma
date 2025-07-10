# prediksi.py (Versi Diperbarui)
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_percentage_error
import sqlite3

def show():
    st.title("🔮 Prediksi Banjir")

    # ===== Fungsi Utama =====
    def load_data():
        conn = sqlite3.connect('flood_prediction.db')
        query = "SELECT tanggal, tma_max FROM tma_data"
        df = pd.read_sql(query, conn, parse_dates=['tanggal'])
        conn.close()
        
        if not df.empty:
            df['tahun'] = df['tanggal'].dt.year
            df['banjir'] = (df['tma_max'] > 1.6).astype(int)
            yearly_data = df.groupby('tahun')['banjir'].sum().reset_index()
            return yearly_data
        return None

    # ===== Tampilan Konten =====
    data = load_data()
    
    if data is not None and len(data) >= 4:  # Minimal 3 tahun untuk prediksi
        # ===== Input Tahun Prediksi =====
        available_years = sorted(data['tahun'].unique())
        last_actual_year = max(available_years)
        
        col1, col2 = st.columns(2)
        with col1:
            start_pred_year = st.number_input(
                "Mulai prediksi dari tahun", 
                min_value=min(available_years)+3, 
                max_value=last_actual_year+5,
                value=last_actual_year+1,
                help="Tahun pertama yang akan diprediksi"
            )
        
        with col2:
            end_pred_year = st.number_input(
                "Sampai tahun", 
                min_value=start_pred_year, 
                max_value=last_actual_year+10,
                value=last_actual_year+1,
                help="Tahun terakhir prediksi"
            )

        # ===== Proses Prediksi =====
        pred_years = range(start_pred_year, end_pred_year+1)
        all_years = range(min(available_years), end_pred_year+1)
        
        # Buat dataframe lengkap
        full_df = pd.DataFrame({'tahun': all_years})
        full_df = full_df.merge(data, on='tahun', how='left')
        
        # Hitung prediksi (3-MA)
        full_df['prediksi'] = full_df['banjir'].rolling(3).mean().shift(1)
        
        # Pisahkan data aktual dan prediksi
        actual_data = full_df[full_df['tahun'] <= last_actual_year].copy()
        pred_data = full_df[full_df['tahun'].isin(pred_years)].copy()
        
        # ===== Hitung MAPE hanya untuk data aktual =====
        eval_data = actual_data.dropna(subset=['prediksi'])
        if not eval_data.empty:
            eval_data['mape'] = (abs(eval_data['banjir'] - eval_data['prediksi']) / eval_data['banjir']) * 100
            mape = eval_data['mape'].mean()
        else:
            mape = None

        # ===== Tampilkan Hasil =====
        st.subheader("📈 Hasil Prediksi")
        
        # Gabungkan data untuk tampilan
        display_df = full_df[['tahun', 'banjir', 'prediksi']].copy()
        display_df['tipe'] = np.where(
            display_df['tahun'] <= last_actual_year, 
            'Aktual', 
            'Prediksi'
        )
        
        # Format tabel
        styled_df = display_df.rename(columns={
            'tahun': 'Tahun',
            'banjir': 'Hari Banjir Aktual',
            'prediksi': 'Prediksi (3-MA)',
            'tipe': 'Jenis Data'
        })
        
        st.dataframe(
            styled_df.style.format({
                'Hari Banjir Aktual': '{:.0f}',
                'Prediksi (3-MA)': '{:.1f}'
            }),
            height=400
        )

        # ===== Visualisasi =====
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Plot data aktual
        ax.plot(
            actual_data['tahun'], 
            actual_data['banjir'], 
            'bo-', 
            label='Aktual'
        )
        
        # Plot prediksi
        ax.plot(
            pred_data['tahun'], 
            pred_data['prediksi'], 
            'r--o', 
            label='Prediksi'
        )
        
        # Anotasi nilai
        for _, row in actual_data.iterrows():
            ax.text(
                row['tahun'], 
                row['banjir']+2, 
                f"{row['banjir']:.0f}", 
                ha='center'
            )
        
        for _, row in pred_data.iterrows():
            ax.text(
                row['tahun'], 
                row['prediksi']-2, 
                f"{row['prediksi']:.1f}", 
                ha='center', 
                color='red'
            )
        
        ax.set_title('Prediksi Hari Banjir Tahunan')
        ax.set_xlabel('Tahun')
        ax.set_ylabel('Jumlah Hari Banjir')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # ===== Tampilkan Metrik =====
        if mape is not None:
            st.subheader("📊 Evaluasi Akurasi Prediksi")
            
            col1, col2 = st.columns(2)
            col1.metric(
                "MAPE (Hanya Data Aktual)", 
                f"{mape:.1f}%",
                help="Diukur hanya untuk tahun dengan data aktual"
            )
            
            # Kategori MAPE
            if mape < 10:
                eval_msg = "SANGAT AKURAT"
                color = "green"
            elif mape < 20:
                eval_msg = "BAIK"
                color = "blue"
            elif mape < 50:
                eval_msg = "CUKUP"
                color = "orange"
            else:
                eval_msg = "TIDAK AKURAT"
                color = "red"
            
            col2.metric(
                "Kategori Akurasi",
                eval_msg,
                help="Berdasarkan nilai MAPE"
            )
            
            st.markdown(
                f"<small>Evaluasi akurasi hanya mencakup periode {eval_data['tahun'].min()}-{eval_data['tahun'].max()}</small>",
                unsafe_allow_html=True
            )
        
        # ===== Detail Perhitungan =====
        with st.expander("🔍 Detail Perhitungan Prediksi"):
            st.markdown("**Metode:** Moving Average 3 Tahun")
            st.latex(r"\text{Prediksi}_t = \frac{\text{Aktual}_{t-1} + \text{Aktual}_{t-2} + \text{Aktual}_{t-3}}{3}")
            
            st.markdown("**Contoh:**")
            example_year = start_pred_year
            st.write(f"Prediksi {example_year} = ({example_year-1} + {example_year-2} + {example_year-3}) / 3")
            
            try:
                val1 = actual_data[actual_data['tahun'] == example_year-1]['banjir'].values[0]
                val2 = actual_data[actual_data['tahun'] == example_year-2]['banjir'].values[0]
                val3 = actual_data[actual_data['tahun'] == example_year-3]['banjir'].values[0]
                st.write(f"= ({val1} + {val2} + {val3}) / 3 = {(val1+val2+val3)/3:.1f}")
            except:
                st.warning("Data tidak cukup untuk contoh perhitungan")

    elif data is not None and len(data) < 4:
        st.error("⚠️ Data tidak cukup! Butuh minimal 4 tahun data untuk prediksi.")
    else:
        st.warning("Silakan upload data TMA terlebih dahulu di halaman Data TMA")