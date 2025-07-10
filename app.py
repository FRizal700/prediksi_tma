# app.py - File utama dengan sistem login dan navigasi tanpa sidebar
import streamlit as st
import pandas as pd
import os
import sqlite3
from datetime import datetime

# Konfigurasi halaman - sembunyikan sidebar secara permanen
st.set_page_config(
    page_title="Sistem Prediksi Banjir",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS untuk menyembunyikan sidebar dan elemen Streamlit bawaan
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .st-emotion-cache-6qob1r {display: none;}
    .st-emotion-cache-1avcm0n {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('flood_prediction.db')
    c = conn.cursor()
    
    # Buat tabel users jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Buat tabel tma_data jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS tma_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tanggal TEXT,
                  jam_06 REAL,
                  jam_12 REAL,
                  jam_18 REAL,
                  tma_min REAL,
                  tma_max REAL,
                  tma_rata REAL)''')
    
    # Tambahkan user default jika belum ada
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users VALUES (?, ?)", ('123', '123'))
        c.execute("INSERT INTO users VALUES (?, ?)", ('user', 'user123'))
    
    conn.commit()
    conn.close()

# Panggil fungsi inisialisasi database
init_db()

# Fungsi autentikasi dari database
def authenticate(username, password):
    conn = sqlite3.connect('flood_prediction.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None and result[0] == password

# Halaman Login
def show_login():
    st.title("🔐 Login Sistem Prediksi Banjir")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login", type="primary"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.current_page = "Dashboard"
                st.rerun()
            else:
                st.error("Username atau password salah")

# Navigasi menggunakan tab
def show_navigation():
    # Tab navigasi
    tabs = st.container()
    with tabs:
        col1, col2, col3, col4 = st.columns(4)
        
        if col1.button("🏠 Dashboard"):
            st.session_state.current_page = "Dashboard"
            st.rerun()
            
        if col2.button("📊 Data TMA"):
            st.session_state.current_page = "Data TMA"
            st.rerun()
            
        if col3.button("🔮 Prediksi"):
            st.session_state.current_page = "Prediksi"
            st.rerun()
            
        if col4.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    
    # Garis pemisah
    st.markdown("---")
    
    # Tampilkan username yang login
    st.caption(f"Logged in as: {st.session_state.username}")

# Main App Logic
def show():
    if not st.session_state.get('logged_in'):
        show_login()
    else:
        show_navigation()
        
        # Load halaman berdasarkan pilihan
        if st.session_state.current_page == "Dashboard":
            from beranda import show
            show()
        elif st.session_state.current_page == "Data TMA":
            from data_tma import show
            show()
        elif st.session_state.current_page == "Prediksi":
            from prediksi import show
            show()

if __name__ == "__main__":
    show()