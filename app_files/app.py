import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Deepfake Detection KCB",
    page_icon="🕵️",
    layout="centered"
)

# --- KONFIGURASI MODEL (WAJIB DISESUAIKAN) ---
# Samakan dengan input shape saat training di Colab!
IMG_HEIGHT = 224  # [UBAH DISINI] Misal: 128, 150, atau 224
IMG_WIDTH = 224   # [UBAH DISINI]
MODEL_PATH = 'model_deepfake_final.keras'

# --- FUNGSI LOAD MODEL (Cached agar cepat) ---
@st.cache_resource
def load_prediction_model():
    model = tf.keras.models.load_model(MODEL_PATH)
    return model

# --- FUNGSI PRE-PROCESSING GAMBAR ---
def import_and_predict(image_data, model):
    # 1. Resize gambar sesuai input model
    image = ImageOps.fit(image_data, (IMG_WIDTH, IMG_HEIGHT), Image.ANTIALIAS)
    
    # 2. Convert ke Array
    img_array = np.asarray(image)
    
    # 3. Normalisasi (Samakan dengan training! Biasanya dibagi 255)
    # Jika saat training pakai rescale=1./255, gunakan baris ini:
    normalized_image_array = (img_array.astype(np.float32) / 255.0)
    
    # 4. Tambah dimensi Batch (Model butuh input: [1, 224, 224, 3])
    data = np.expand_dims(normalized_image_array, axis=0)
    
    # 5. Prediksi
    prediction = model.predict(data)
    return prediction

# --- UI UTAMA ---
st.title("🕵️ Deteksi Deepfake (KCB)")
st.write("Upload gambar wajah untuk mendeteksi apakah **Asli (Real)** atau **Palsu (Fake)**.")

# Load Model saat aplikasi mulai
try:
    model = load_prediction_model()
    st.success("✅ Model berhasil dimuat!")
except Exception as e:
    st.error(f"❌ Gagal memuat model. Pastikan file '{MODEL_PATH}' ada di folder yang sama.")
    st.stop()

# Widget Upload File
file = st.file_uploader("Pilih Gambar (JPG/PNG)", type=["jpg", "png", "jpeg"])

if file is None:
    st.text("Silakan upload file gambar...")
else:
    # Tampilkan gambar yang diupload
    image = Image.open(file)
    st.image(image, use_column_width=True)
    
    # Tombol Prediksi
    if st.button("🔍 Deteksi Sekarang"):
        with st.spinner('Sedang menganalisis...'):
            try:
                # Lakukan Prediksi
                prediction = import_and_predict(image, model)
                
                # --- LOGIKA HASIL (SESUAIKAN DENGAN MODEL ANDA) ---
                # Asumsi: Binary Classification (Output 1 node dengan Sigmoid)
                # 0 = Fake, 1 = Real (atau sebaliknya, cek label training Anda!)
                
                confidence = prediction[0][0]
                
                # Ambang batas (Threshold) biasanya 0.5
                if confidence > 0.5:
                    label = "REAL (Asli)" 
                    score = confidence * 100
                    color = "green"
                else:
                    label = "FAKE (Palsu)"
                    score = (1 - confidence) * 100
                    color = "red"
                
                st.markdown(f"### Hasil: <span style='color:{color}'>{label}</span>", unsafe_allow_html=True)
                st.info(f"Confidence Score: {score:.2f}%")
                
                # Tampilkan raw output untuk debugging (bisa dihapus nanti)
                st.caption(f"Raw Output Model: {prediction}")

            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses gambar: {e}")
                st.write("Tips: Cek kembali ukuran input (IMG_HEIGHT/WIDTH) di script.")