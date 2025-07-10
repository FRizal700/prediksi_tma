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
        df['banjir'] = (df['tma_max'] > 1.6).astype(int)
        yearly_floods = df.groupby('tahun')['banjir'].sum().reset_index()
        
        # ===== Otomatis deteksi tahun tersedia =====
        available_years = sorted(yearly_floods['tahun'].unique())
        min_year = min(available_years)
        max_year = max(available_years)
        
        # ===== Hitung range tahun prediksi =====
        if len(available_years) >= 4:  # Minimal 3 tahun training + 1 tahun prediksi
            validation_data = yearly_floods.copy()
            
            st.success(f"✅ Data tersedia: {min_year}-{max_year}")
            
            # ===== Perhitungan Prediksi & Metrik =====
            validation_data['prediksi'] = validation_data['banjir'].rolling(3).mean().shift(1)
            validation_data['error'] = validation_data['banjir'] - validation_data['prediksi']
            validation_data['absolute_error'] = validation_data['error'].abs()
            validation_data['squared_error'] = validation_data['error']**2
            validation_data['mape'] = (validation_data['absolute_error'] / validation_data['banjir']) * 100

            # ===== Tabel Utama =====
            st.subheader("📊 Tabel Prediksi Banjir Tahunan")
            display_df = validation_data.rename(columns={
                'tahun': 'Tahun',
                'banjir': 'Aktual',
                'prediksi': 'Prediksi (3-MA)',
                'error': 'Error',
                'absolute_error': '|Error|',
                'squared_error': 'Error²',
                'mape': 'MAPE (%)'
            })
            st.dataframe(
                display_df.style.format({
                    'Aktual': '{:.0f}', 
                    'Prediksi (3-MA)': '{:.1f}',
                    'Error': '{:.1f}', 
                    '|Error|': '{:.1f}', 
                    'Error²': '{:.1f}', 
                    'MAPE (%)': '{:.1f}'
                })
            )

            # ===== Hitung Metrik Hanya untuk Tahun yang Bisa Diprediksi =====
            eval_data = validation_data.dropna(subset=['prediksi'])
            if not eval_data.empty:
                # ===== Metrik Evaluasi =====
                st.subheader("📈 Metrik Evaluasi Prediksi")
                mae = eval_data['absolute_error'].mean()
                mse = eval_data['squared_error'].mean()
                rmse = np.sqrt(mse)
                mape = eval_data['mape'].mean()
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("MAE", f"{mae:.1f} ", help="Rata-rata error absolut")
                col2.metric("MSE", f"{mse:.1f}", help="Rata-rata kuadrat error")
                col3.metric("RMSE", f"{rmse:.1f} ", help="Akar MSE")
                col4.metric("MAPE", f"{mape:.1f}%", help="Error persentase rata-rata")

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
                    st.latex(r"""
                    \text{Prediksi}_t = \frac{\text{Aktual}_{t-1} + \text{Aktual}_{t-2} + \text{Aktual}_{t-3}}{3}
                    """)
                    
                    contoh_tahun = eval_data['tahun'].iloc[-1]
                    tahun_prediksi = [contoh_tahun-1, contoh_tahun-2, contoh_tahun-3]
                    train_data = validation_data[validation_data['tahun'].isin(tahun_prediksi)]
                    
                    st.write(f"**Contoh Prediksi {contoh_tahun}:**")
                    st.write(f"= ({train_data['banjir'].iloc[0]} + {train_data['banjir'].iloc[1]} + {train_data['banjir'].iloc[2]}) / 3")
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
                    
                    # Bagian 4: Perhitungan MSE
                    st.markdown("---\n### 📊 Perhitungan Mean Squared Error (MSE)")
                    st.latex(r"""
                    \text{MSE} = \frac{1}{n}\sum_{i=1}^n (\text{Error}_i)^2
                    """)
                    st.write("**Perhitungan:**")
                    st.write("= (" + " + ".join([f"{x:.1f}" for x in eval_data['squared_error']]) + f") / {len(eval_data)}")
                    st.write(f"= **{mse:.1f}**")
                    
                    # Bagian 5: Perhitungan MAPE
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
                    
                    # Bagian 6: Penjelasan Kategori MAPE
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
                
                # Plot prediksi hanya untuk tahun yang bisa diprediksi
                ax.plot(eval_data['tahun'], eval_data['prediksi'], 'r--o', label='Prediksi (3-MA)')
                
                # Anotasi nilai
                for _, row in validation_data.iterrows():
                    ax.text(row['tahun'], row['banjir']+2, f"{row['banjir']:.0f}", ha='center')
                    if not pd.isna(row['prediksi']):
                        ax.text(row['tahun'], row['prediksi']-2, f"{row['prediksi']:.1f}", 
                            ha='center', color='red')
                
                ax.set_xlabel('Tahun')
                ax.set_ylabel('Hari Banjir')
                ax.legend()
                ax.grid(True, linestyle='--', alpha=0.7)
                st.pyplot(fig)
                
            else:
                st.warning("⚠️ Belum ada tahun yang bisa diprediksi (butuh minimal 3 tahun data historis)")
        else:
            st.error(f"❌ Data tidak cukup! Butuh minimal 4 tahun data (tersedia: {len(available_years)} tahun)")
    else:
        st.warning("""
        ⚠️ Silakan proses data TMA terlebih dahulu di halaman **Data TMA**.
        """)