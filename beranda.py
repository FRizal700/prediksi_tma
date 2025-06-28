# pages/1_🏠_Beranda.py
import streamlit as st

def show():
    st.title("Selamat Datang di Sistem Prediksi Banjir Tahunan")
    st.write("""
    Sistem ini dirancang untuk memprediksi jumlah kejadian banjir tahunan berdasarkan data ketinggian air sungai 
    dengan menggunakan metode Moving Average.

    Fitur utama:
    - Upload dan manajemen data ketinggian air sungai
    - Analisis kejadian banjir berdasarkan threshold >1.6 meter
    - Prediksi jumlah banjir tahunan menggunakan Moving Average
    - Visualisasi data aktual vs prediksi
    - Perhitungan akurasi prediksi (MAPE)

    Gunakan menu di sebelah kiri untuk navigasi.
    """)
