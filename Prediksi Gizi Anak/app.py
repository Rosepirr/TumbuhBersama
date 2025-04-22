import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import joblib
import zscore

# Load model dan fitur
model_path = 'model_deteksi_tumbuh gaharu.pkl'
model = joblib.load(model_path)
selected_features = joblib.load('selected_features.pkl')

# Set page
im = Image.open('1-removebg-preview.png')
st.set_page_config(page_title="Tumbuh Bersama Online", page_icon=im, layout="wide")

# Logo dan header
st.image("image (2).png", width=100)
st.image("bg tumbuh kembang.png", use_container_width=True)

# Input nama dan tanggal
nama = st.text_input("Nama")
dob = st.date_input("Tanggal Lahir", value=datetime.now(), format="DD/MM/YYYY")
visit_date = st.date_input("Tanggal Kunjungan", value=datetime.now(), format="DD/MM/YYYY")

# Hitung umur
if dob and visit_date:
    total_days = (visit_date - dob).days
    age_months = total_days // 30
    age_days = total_days % 30
    st.session_state.age_months = age_months
    st.session_state.age_days = age_days
else:
    st.session_state.age_months = None
    st.session_state.age_days = None

if st.session_state.age_months is not None and st.session_state.age_days is not None:
    if st.session_state.age_months < 0:
        st.error("Error: Umur tidak bisa kurang dari 0 bulan.")
    elif st.session_state.age_months > 60:
        st.error("Error: Umur tidak bisa lebih dari 60 bulan.")
    else:
        st.write(f"Umur: {st.session_state.age_months} bulan")
else:
    st.write("Umur: - bulan")

# Input berat dan tinggi badan
berat = st.text_input("Masukkan berat badan (kg). Contoh : 8.2")
tinggi = st.text_input("Masukkan tinggi badan (cm). Contoh : 98.3")

# Input kategori
col1, col2 = st.columns(2)

with col1:
    gender = st.radio("Gender*", ("Laki-laki", "Perempuan"))
    perkembangan = st.radio("Perkembangan Anak Yang Terlihat*", ("Menyimpang", "Normal", "Sehat"))
    polam = st.radio("Pola Makan*", ("Baik", "Kurang"))

with col2:
    lingso = st.radio("Lingkungan Tempat Tinggal*", options=["Aman", "Tidak Aman"])
    imunisasi = st.radio("Imunisasi Yang Diberikan?*", options=["Lengkap", "Tidak Lengkap"])
    penkel = st.radio("Pendapatan Keluarga*", options=["Rendah", "Menengah", "Tinggi"])

# Konversi input
JK = 0 if gender == 'Laki-laki' else 1
berat = float(berat) if berat else 0
tinggi = float(tinggi) if tinggi else 0
bulan = st.session_state.age_months
gender_input = gender.lower()

# Z-Score dan Status
z_bb = z_tb = z_bb_tb = 0

if berat:
    z_bb = zscore.ZSWeight(gender_input, bulan, berat)
    st.subheader("Hasil Z-Score:")
    st.write(f"**BB/U (Berat Badan per Umur):** {z_bb:.2f}")
    st.write(f"**Status Gizi BB/U:** {zscore.statusgiziberat(z_bb)}")

if tinggi:
    z_tb = zscore.ZSHeight(gender_input, bulan, tinggi)
    st.write(f"**TB/U (Tinggi Badan per Umur):** {z_tb:.2f}")
    st.write(f"**Status Gizi TB/U:** {zscore.statusGiziTinggi(z_tb)}")

if berat and tinggi:
    try:
        z_bb_tb = zscore.ZSWeightByHeight(gender_input, tinggi, berat)
        st.write(f"**BB/TB (Berat Badan per Tinggi Badan):** {z_bb_tb:.2f}")
        st.write(f"**Status Gizi BB/TB:** {zscore.statusGizi(z_bb_tb)}")
    except Exception as e:
        st.error(f"Terjadi kesalahan dalam menghitung BB/TB: {e}")

# Tombol submit dan klasifikasi
if st.button('Submit'):
    st.subheader('Hasil Klasifikasi')

    try:
        input_data = pd.DataFrame([[
            JK,
            st.session_state.age_months,
            tinggi,
            berat,
            zscore.statusBerat(z_bb),
            z_bb,
            zscore.statusBeratTinggi(z_bb_tb),
            z_bb_tb,
            zscore.statusTinggi(z_tb),
            z_tb,
            {'Menyimpang': 0, 'Normal': 1, 'Sehat': 2}[perkembangan],
            {'Aman': 0, 'Tidak Aman': 1}[lingso],
            {'Lengkap': 0, 'Tidak Lengkap': 1}[imunisasi],
            {'Rendah': 0, 'Menengah': 1, 'Tinggi': 2}[penkel],
            {'Baik': 0, 'Kurang': 1}[polam]
        ]], columns=selected_features)

        # Prediksi
        klasifikasi = model.predict(input_data)
        hasil = int(klasifikasi[0])

        if hasil == 0:
            st.success('Kondisi Balita : Tidak Berisiko')
        elif hasil == 1:
            st.warning('Kondisi Balita : Hampir Berisiko')
        elif hasil == 2:
            st.error('Kondisi Balita : Berisiko')
    except ValueError as e:
        st.error(f"Error saat klasifikasi: {e}")