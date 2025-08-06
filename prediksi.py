import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_percentage_error, mean_absolute_error, mean_squared_error


def show():
    st.title("🔮 Prediksi Banjir")

    def calculate_moving_average(data, window=3):
        return data.rolling(window=window, min_periods=1).mean()

    def calculate_mape(actual, predicted):
        actual = np.array(actual)
        predicted = np.array(predicted)
        mask = actual != 0
        if sum(mask) == 0:
            return float('inf')
        return mean_absolute_percentage_error(actual[mask], predicted[mask]) * 100

    if 'current_data' in st.session_state:
        df = st.session_state['current_data']
        df['banjir'] = (df['tma_max'] > 1.60).astype(int)
        yearly_floods = df.groupby('tahun')['banjir'].sum().reset_index()
        
        # ===== Otomatis deteksi tahun tersedia =====
        available_years = sorted(yearly_floods['tahun'].unique())
        min_year = min(available_years)
        max_year = max(available_years)
        
        # ===== Pilihan Periode Moving Average =====
        st.subheader("⚙️ Pengaturan Prediksi")
        ma_period = st.selectbox(
            "Pilih jumlah periode Moving Average:",
            ["3 periode", "4 periode"],
            index=0
        )
        window_size = 3 if ma_period == "3 periode" else 4
        
        # ===== Hitung range tahun prediksi =====
        min_required_years = window_size + 1  # Minimal n tahun training + 1 tahun prediksi
        if len(available_years) >= min_required_years:
            validation_data = yearly_floods.copy()
            
            st.success(f"✅ Data tersedia: {min_year}-{max_year}")
            
            # ===== Perhitungan Prediksi & Metrik =====
            validation_data['prediksi'] = validation_data['banjir'].rolling(window_size).mean().shift(1)
            
            # ===== Tambahkan prediksi untuk tahun berikutnya =====
            if len(validation_data) >= window_size:
                last_years = validation_data['banjir'].tail(window_size).values
                next_year_pred = np.mean(last_years)
                next_year = max_year + 1
                
                # Tambahkan baris prediksi tahun berikutnya
                new_row = {
                    'tahun': next_year,
                    'banjir': np.nan,
                    'prediksi': next_year_pred
                }
                validation_data = pd.concat([validation_data, pd.DataFrame([new_row])], ignore_index=True)
            
            validation_data['error'] = validation_data['banjir'] - validation_data['prediksi']
            validation_data['absolute_error'] = validation_data['error'].abs()
            validation_data['mape'] = (validation_data['absolute_error'] / validation_data['banjir']) * 100

            # ===== Tabel Utama =====
            st.subheader("📊 Tabel Prediksi Banjir Tahunan")
            display_df = validation_data.rename(columns={
                'tahun': 'Tahun',
                'banjir': 'Aktual',
                'prediksi': f'Prediksi ({window_size}-Periode)',
                'error': 'Error',
                'absolute_error': '|Error|',
                'mape': 'MAPE (%)'
            })
            st.dataframe(
                display_df.style.format({
                    'Aktual': '{:.0f}', 
                    f'Prediksi ({window_size}-Periode)': '{:.1f}',
                    'Error': '{:.1f}', 
                    '|Error|': '{:.1f}', 
                    'MAPE (%)': '{:.1f}'
                }).map(lambda x: 'color: red' if pd.isna(x) else '', subset=['Aktual'])
            )

            # ===== Hitung Metrik Hanya untuk Tahun yang Bisa Diprediksi =====
            eval_data = validation_data.dropna(subset=['prediksi', 'banjir'])  # Hanya tahun dengan aktual dan prediksi
            
            if not eval_data.empty:
                # ===== Metrik Evaluasi =====
                st.subheader("📈 Metrik Evaluasi Prediksi")
                mae = eval_data['absolute_error'].mean()
                mape = eval_data['mape'].mean()
                
                col1, col2 = st.columns(2)
                col1.metric("MAE", f"{mae:.1f} ", help="Rata-rata error absolut")
                col2.metric("MAPE", f"{mape:.1f}%", help="Error persentase rata-rata")

                # ===== Kategori MAPE =====
                if mape < 10:
                    eval_msg = "SANGAT AKURAT <10%"
                    eval_color = "green"
                elif mape < 20:
                    eval_msg = "BAIK 10-20%"
                    eval_color = "blue"
                elif mape < 50:
                    eval_msg = "CUKUP 20-50%"
                    eval_color = "orange"
                else:
                    eval_msg = "TIDAK AKURAT >50%"
                    eval_color = "red"
                
                st.markdown(f"**Kategori Akurasi:** <span style='color:{eval_color};font-weight:bold'>{eval_msg}</span>", unsafe_allow_html=True)

                # ===== Detail Perhitungan =====
                with st.expander("🧮 DETAIL PERHITUNGAN", expanded=False):
                    # Bagian 1: Perhitungan Prediksi
                    st.markdown("### 🔢 Perhitungan Prediksi")
                    st.latex(fr"""
                    \text{{Prediksi}}_t = \frac{{\text{{Aktual}}_{{t-1}} + \text{{Aktual}}_{{t-2}} + \cdots + \text{{Aktual}}_{{t-{window_size}}}}}{{{window_size}}}
                    """)
                    
                    contoh_tahun = eval_data['tahun'].iloc[-1]
                    tahun_prediksi = [contoh_tahun-i for i in range(1, window_size+1)]
                    train_data = validation_data[validation_data['tahun'].isin(tahun_prediksi)]
                    
                    st.write(f"**Contoh Prediksi {contoh_tahun}:**")
                    st.write("= (" + " + ".join([f"{x:.0f}" for x in train_data['banjir']]) + f") / {window_size}")
                    st.write(f"= **{validation_data.loc[validation_data['tahun']==contoh_tahun, 'prediksi'].values[0]:.1f}** ")
                    
                    # Bagian 2: Perhitungan Error
                    st.markdown("---\n### 📉 Perhitungan Error")
                    st.latex(r"""
                    \text{Error} = \text{Aktual} - \text{Prediksi}
                    """)
                    
                    # Bagian 3: Perhitungan MAD/MAE
                    st.markdown("---\n### 📊 Perhitungan Mean Absolute Deviation (MAD/MAE)")
                    st.latex(r"""
                    \text{MAE} = \frac{1}{n}\sum_{i=1}^n |\text{Error}_i|
                    """)
                    st.write("**Perhitungan:**")
                    st.write("= (" + " + ".join([f"{x:.1f}" for x in eval_data['absolute_error']]) + f") / {len(eval_data)}")
                    st.write(f"= **{mae:.1f}**")
                    
                    # Bagian 4: Perhitungan MAPE
                    st.markdown("---\n### 📊 Perhitungan Mean Absolute Percentage Error (MAPE)")
                    st.latex(r"""
                    \text{MAPE} = \left(\frac{1}{n}\sum_{i=1}^n \frac{|\text{Error}_i|}{\text{Aktual}_i}\right) \times 100\%
                    """)
                    st.write("**Perhitungan:**")
                    mape_calcs = []
                    for _, row in eval_data.iterrows():
                        mape_calcs.append(f"({row['absolute_error']:.1f}/{row['banjir']})")
                    st.write("= (" + " + ".join(mape_calcs) + f") / {len(eval_data)} × 100%")
                    st.write(f"= **{mape:.1f}%**")
                    
                    # Bagian 5: Penjelasan Kategori MAPE
                    st.markdown("---\n### 📚 Kategori MAPE (Berdasarkan Skripsi Referensi)")
                    st.table(pd.DataFrame({
                        "MAPE (%)": ["<10", "10-20", "20-50", "++50"],
                        "Kategori": ["Sangat Akurat", "Baik", "Cukup", "Tidak Akurat"],
                        "Interpretasi": [
                            "Prediksi hampir sempurna untuk keputusan strategis",
                            "Reliabel untuk perencanaan operasional",
                            "Dapat menunjukkan tren tetapi perlu verifikasi",
                            "Tidak direkomendasikan untuk pengambilan keputusan"
                        ]
                    }))

                # ===== Visualisasi =====
                st.subheader("📉 Grafik Prediksi vs Aktual")
                fig, ax = plt.subplots(figsize=(10,5))
                
                # Plot data aktual
                ax.plot(validation_data['tahun'], validation_data['banjir'], 'bo-', label='Aktual')
                
                # Plot prediksi untuk tahun yang bisa diprediksi
                ax.plot(eval_data['tahun'], eval_data['prediksi'], 'r--o', label=f'Prediksi ({window_size}-MA)')
                
                # Plot prediksi tahun berikutnya jika ada
                if len(validation_data) > len(eval_data):
                    next_year_data = validation_data.iloc[-1]
                    ax.plot(next_year_data['tahun'], next_year_data['prediksi'], 'gs--', label='Prediksi Tahun Depan')
                    ax.text(next_year_data['tahun'], next_year_data['prediksi']-2, 
                           f"{next_year_data['prediksi']:.1f}*", ha='center', color='green')
                
                # Anotasi nilai
                for _, row in validation_data.iterrows():
                    if not pd.isna(row['banjir']):
                        ax.text(row['tahun'], row['banjir']+2, f"{row['banjir']:.0f}", ha='center')
                    if not pd.isna(row['prediksi']) and row['tahun'] in eval_data['tahun'].values:
                        ax.text(row['tahun'], row['prediksi']-2, f"{row['prediksi']:.1f}", 
                            ha='center', color='red')
                
                ax.set_xlabel('Tahun')
                ax.set_ylabel('Hari Banjir')
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(fig)
                
                # Keterangan prediksi tahun depan
                if len(validation_data) > len(eval_data):
                    st.markdown(f"> *Prediksi untuk tahun depan menggunakan metode {window_size}-MA (Moving Average {window_size} tahun terakhir)*")
                
            else:
                st.warning(f"⚠️ Belum ada tahun yang bisa diprediksi (butuh minimal {window_size} tahun data historis)")
        else:
            st.error(f"❌ Data tidak cukup! Butuh minimal {min_required_years} tahun data (tersedia: {len(available_years)} tahun)")
    else:
        st.warning("""
        ⚠️ Silakan proses data TMA terlebih dahulu di halaman **Data TMA**.
        """)