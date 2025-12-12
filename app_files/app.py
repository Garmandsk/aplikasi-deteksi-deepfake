import streamlit as st
import time
import uuid
import os
import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps
from supabase import create_client, Client

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="CyberGuard: AI Pelindung Publik",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. KONFIGURASI & FUNGSI MODEL ---
IMG_HEIGHT = 224
IMG_WIDTH = 224 

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(current_dir, 'model_deepfake_ori.keras')

@st.cache_resource
def load_prediction_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"File model tidak ditemukan di: {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH)
    return model

def import_and_predict(image_data, model):
    image_data = image_data.convert("RGB")
    # Resize
    image = ImageOps.fit(image_data, (IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
    # Convert ke Array
    img_array = np.asarray(image)
    # Normalisasi
    normalized_image_array = (img_array.astype(np.float32) / 255.0)
    # Tambah dimensi Batch
    data = np.expand_dims(normalized_image_array, axis=0)
    # Prediksi
    prediction = model.predict(data)
    return prediction

# --- 3. KONFIGURASI SUPABASE ---
SUPABASE_URL = "https://otbcyjmlhrayctgaihop.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im90YmN5am1saHJheWN0Z2FpaG9wIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU0ODA3OTMsImV4cCI6MjA4MTA1Njc5M30.bhvXZM9yqZon6YYkR8TPaHH5HvAUNN86Cp4OGfiGc6g" 
BUCKET_NAME = "dataset-warga"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_ready = True
except Exception as e:
    supabase_ready = False
    print(f"Error connect Supabase: {e}")

def upload_to_supabase(uploaded_file, nama_pengirim, jenis_laporan):
    if not supabase_ready:
        return False, "Koneksi Supabase belum disetting/gagal."
    
    try:
        file_ext = uploaded_file.name.split('.')[-1]
        unique_filename = f"{jenis_laporan.replace(' ', '_')}_{uuid.uuid4()}.{file_ext}"
        file_bytes = uploaded_file.getvalue()
        path_on_cloud = f"uploads/{unique_filename}"
        
        supabase.storage.from_(BUCKET_NAME).upload(
            path=path_on_cloud,
            file=file_bytes,
            file_options={"content-type": uploaded_file.type}
        )
        return True, path_on_cloud
    except Exception as e:
        return False, str(e)

# --- 4. CSS CUSTOM ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #00ffbf !important;
    }
    .stButton>button {
        background-color: #00ffbf;
        color: black;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9131/9131546.png", width=100)
    st.title("🛡️ CyberGuard")
    st.caption("Social Project KCB")
    
    menu = st.radio("Navigasi:", ["Beranda", "Deteksi Visual", "Kontribusi", "Edukasi"])
    
    st.markdown("---")
    st.info("Versi Demo v1.0")

# ==========================================
# HALAMAN: BERANDA
# ==========================================
if menu == "Beranda":
    st.title("🛡️ CyberGuard: Dari Kita, Untuk Kita")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        Aplikasi ini hadir dengan konsep **Community Based Security**:
        1. **Deteksi:** Cek keaslian gambar wajah.
        2. **Edukasi:** Pahami cara kerja Deepfake.
        3. **Kontribusi:** Upload temuan Deepfake baru untuk melatih AI kita agar makin pintar.
        """)
        st.warning("⚠️ Proyek ini adalah inisiatif sosial mahasiswa untuk melawan Deepfake yang disalahgunakan.")

# ==========================================
# HALAMAN: DETEKSI VISUAL
# ==========================================
elif menu == "Deteksi Visual":
    st.header("🎭 Deteksi Visual")
    st.write("Upload gambar wajah untuk memeriksa keaslian.")
    
    model = None
    try:
        model = load_prediction_model()
        st.success("✅ Model AI berhasil dimuat!")
    except Exception as e:
        st.error(f"❌ Gagal memuat model. Pastikan file '{MODEL_PATH}' ada.")
        st.error(f"Detail Error: {e}")
        st.stop() 

    # Widget Upload File
    file = st.file_uploader("Pilih Gambar (JPG/PNG)", type=["jpg", "png", "jpeg"])

    if file is None:
        st.text("Silakan upload file gambar...")
    else:
        # Tampilkan gambar yang diupload
        image = Image.open(file)
        st.image(image, caption="Gambar yang diupload", use_container_width=True)

        # Tombol Prediksi
        if st.button("🔍 Deteksi Sekarang"):
            with st.spinner('Sedang menganalisis piksel wajah...'):
                try:
                    prediction = import_and_predict(image, model)
                    
                    # Ambil nilai confidence
                    confidence = prediction[0][0]
                    threshold = 0.5
                    
                    if confidence > threshold:
                        label = "REAL (Asli)" 
                        score = confidence * 100
                        color = "#00ffbf" # Hijau Neon
                    else:
                        label = "FAKE (Deepfake)"
                        score = (1 - confidence) * 100
                        color = "#ff4b4b" # Merah

                    st.markdown(f"<h2 style='text-align: center; color: {color} !important;'>Hasil: {label}</h2>", unsafe_allow_html=True)
                    st.info(f"Tingkat Keyakinan AI: {score:.2f}%")
                    
                    # Progress bar visual
                    st.progress(int(score), text="Confidence Score")

                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memproses gambar: {e}")

# ==========================================
# HALAMAN: KONTRIBUSI 
# ==========================================
elif menu == "Kontribusi": 
    st.header("☁️ Kontribusi Deepfake")
    st.info("Data yang Anda upload akan disimpan ke Cloud Storage untuk melatih ulang AI.")
    
    if not supabase_ready:
        st.error("⚠️ Koneksi bermasalah. Cek internet atau API Key.")
    
    with st.form("kontribusi_cloud"):
        nama = st.text_input("Nama Kontributor (Opsional):", "Anonim")
        jenis = st.selectbox("Jenis Temuan:", ["Deepfake Wajah", "Voice Cloning", "Hoaks Video"])
        file_upload = st.file_uploader("Upload Deepfake:", type=['jpg', 'png', 'mp4'])
        ket = st.text_area("Keterangan:")
        
        btn_kirim = st.form_submit_button("🚀 Upload")
        
        if btn_kirim:
            if file_upload:
                with st.spinner("Mengirim data ke cloud..."):
                    sukses, info = upload_to_supabase(file_upload, nama, jenis)
                    
                    if sukses:
                        st.balloons()
                        st.success("✅ Berhasil! Data tersimpan aman di Cloud.")
                        st.caption(f"ID File: {info}")
                    else:
                        st.error(f"Gagal Upload: {info}")
            else:
                st.warning("Pilih file dulu.")

# ==========================================
# HALAMAN: EDUKASI
# ==========================================
elif menu == "Edukasi":
    st.header("📚 Pojok Literasi")
    
    tab1, tab2 = st.tabs(["Ciri Deepfake", "Tips Aman"])
    
    with tab1:
        st.subheader("Cara Mengenali Deepfake")
        st.markdown("""
          1. **Mata Jarang Berkedip:** Manusia berkedip tiap 2-10 detik.
          2. **Sinkronisasi Bibir:** Gerakan bibir tidak pas dengan suara.
          3. **Tekstur Kulit:** Terlalu halus atau *blur* di area perbatasan wajah.
          4. **Garis Wajah:** Garis wajah tidak alami.
          5. **Pencahayaan:** Pencahayaan tidak sesuai kondisi sekitar
        """)
            
    with tab2:
        st.subheader("Langkah Pencegahan")
        st.markdown("""
        - **Verifikasi:** Jangan asal share.
        - **Sandi Keluarga:** Sepakati kode rahasia untuk validasi telepon darurat.
        - **Deteksi:** Gunakan fitur 'Deteksi' di aplikasi ini.
        - **Kontribusi:** Gunakan fitur 'Kontribusi' agar sistem deteksi aplikasi meningkat seiring berkembangnya teknologi Deepfake.
        """)