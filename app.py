# app.py - File utama dengan sistem login dan navigasi tanpa sidebar
import streamlit as st
import pandas as pd
import os

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

# Fungsi autentikasi (simpan di database di production)
def authenticate(username, password):
    valid_users = {
        "123": "123",
        "user": "user123"
    }
    return valid_users.get(username) == password

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