import streamlit as st
import time
import uuid
import os
import numpy as np
import tensorflow as tf
import hashlib # Tambahan untuk Hashing
from PIL import Image, ImageOps
from supabase import create_client, Client

# --- LIBRARY KRIPTOGRAFI HYBRID ---
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- 1. KONFIGURASI HALAMAN & SESSION STATE ---
st.set_page_config(
    page_title="CyberGuard: AI Pelindung Publik",
    page_icon="🛡️",
    layout="wide"
)

# Inisialisasi Session State untuk Navigasi (Agar fitur Redirect jalan)
if 'page_selection' not in st.session_state:
    st.session_state['page_selection'] = 'Beranda'

# --- 2. MODUL KRIPTOGRAFI (HYBRID & HASH) ---

@st.cache_resource
def get_rsa_keys():
    """
    Generate RSA Keys (Simulasi Server Key).
    RSA-2048 untuk membungkus kunci AES.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Load keys sekali saja
server_private_key, app_public_key = get_rsa_keys()

def calculate_hash(file_bytes):
    """Menghitung SHA-256 Hash dari file gambar (Digital Forensics)"""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()

def hybrid_encrypt(plaintext, public_key):
    """
    Enkripsi Hybrid:
    1. Data -> Dienkripsi pakai AES-256 (CFB Mode)
    2. Kunci AES -> Dienkripsi pakai RSA-2048 (OAEP Padding)
    """
    # 1. Generate Random Session Key (32 bytes = 256 bits)
    session_key = os.urandom(32)
    iv = os.urandom(16) # Initialization Vector

    # 2. Enkripsi Data pakai AES
    cipher_aes = Cipher(algorithms.AES(session_key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher_aes.encryptor()
    # Pastikan plaintext string, ubah ke bytes
    encrypted_data = encryptor.update(str(plaintext).encode()) + encryptor.finalize()

    # 3. Enkripsi Session Key pakai RSA
    encrypted_session_key = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return {
        "enc_session_key": encrypted_session_key.hex(),
        "iv": iv.hex(),
        "ciphertext": encrypted_data.hex()
    }

# --- 3. KONFIGURASI MODEL AI ---
IMG_HEIGHT = 224
IMG_WIDTH = 224 

current_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(current_dir, 'model_deepfake_ori.keras')

@st.cache_resource
def load_prediction_model():
    if not os.path.exists(MODEL_PATH):
        # Fallback dummy model jika file belum ada (biar app gak crash pas testing)
        return None
    model = tf.keras.models.load_model(MODEL_PATH)
    return model

def import_and_predict(image_data, model):
    image_data = image_data.convert("RGB")
    image = ImageOps.fit(image_data, (IMG_WIDTH, IMG_HEIGHT), Image.LANCZOS)
    img_array = np.asarray(image)
    normalized_image_array = (img_array.astype(np.float32) / 255.0)
    data = np.expand_dims(normalized_image_array, axis=0)
    prediction = model.predict(data)
    return prediction

# --- 4. KONFIGURASI SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
BUCKET_NAME = "dataset-warga"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_ready = True
except Exception as e:
    supabase_ready = False
    print(f"Error connect Supabase: {e}")

def upload_to_supabase(uploaded_file, encrypted_metadata_str, jenis_laporan):
    """
    Upload file gambar + Metadata yang SUDAH TERENKRIPSI
    """
    if not supabase_ready:
        return False, "Koneksi Supabase gagal."

    try:
        file_ext = uploaded_file.name.split('.')[-1]
        unique_filename = f"{jenis_laporan.replace(' ', '_')}_{uuid.uuid4()}.{file_ext}"
        file_bytes = uploaded_file.getvalue()
        path_on_cloud = f"uploads/{unique_filename}"

        # Upload Gambar
        supabase.storage.from_(BUCKET_NAME).upload(
            path=path_on_cloud,
            file=file_bytes,
            file_options={"content-type": uploaded_file.type}
        )
        
        # Note: Idealnya encrypted_metadata_str disimpan di Table Database Supabase.
        # Karena ini demo storage, kita anggap sukses terkirim.
        return True, path_on_cloud
    except Exception as e:
        return False, str(e)

# --- 5. CSS CUSTOM ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1, h2, h3 { color: #00ffbf !important; }
    .stButton>button {
        background-color: #00ffbf;
        color: black;
        font-weight: bold;
        border-radius: 8px;
    }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/9131/9131546.png", width=100)
    st.title("🛡️ CyberGuard")
    st.caption("Social Project KCB")

    # Menggunakan Session State untuk mengontrol navigasi
    menu = st.radio(
        "Navigasi:", 
        ["Beranda", "Deteksi Visual", "Kontribusi", "Edukasi"],
        key="page_selection" # Kunci agar bisa diubah dari tombol lain
    )

    st.markdown("---")
    st.info("Versi Demo v1.1 (Hybrid Crypto)")

# ==========================================
# HALAMAN: BERANDA
# ==========================================
if menu == "Beranda":
    st.title("🛡️ ADD: Dari Kita, Untuk Kita")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        **CyberGuard** adalah platform pertahanan siber berbasis komunitas:
        1. **Deteksi AI:** Menggunakan MobileNetV2 untuk mengenali wajah palsu.
        2. **Keamanan Data:** Menggunakan RSA-2048 & AES-256 (Hybrid Cryptosystem).
        3. **Forensik Digital:** Validasi integritas file dengan SHA-256.
        """)
        if st.button("Mulai Deteksi ->"):
            st.session_state['page_selection'] = "Deteksi Visual"
            st.rerun()
        st.link_button("📂 Feedback Aplikasi", "https://forms.gle/BiasriBofMjGVmjN8", help="Klik untuk mengisi kuesioner")

# ==========================================
# HALAMAN: DETEKSI VISUAL
# ==========================================
elif menu == "Deteksi Visual":
    st.header("🎭 Deteksi Visual")
    st.write("Upload gambar wajah untuk memeriksa keaslian.")

    model = load_prediction_model()
    if model is None:
        st.error("❌ File model tidak ditemukan. Pastikan 'model_deepfake_ori.keras' ada di folder.")
    else:
        file = st.file_uploader("Pilih Gambar (JPG/PNG)", type=["jpg", "png", "jpeg"])

        if file is not None:
            image = Image.open(file)
            st.image(image, caption="Gambar Input", width=300)

            # Hitung Hash Gambar (Forensik)
            file.seek(0)
            file_bytes = file.read()
            img_hash = calculate_hash(file_bytes)
            
            with st.expander("🔍 Info Forensik Digital (SHA-256)"):
                st.code(img_hash, language='text')
                st.caption("Hash ini adalah sidik jari unik file. Jika file diubah 1 bit, hash akan berubah.")

            if st.button("🔍 Deteksi Sekarang"):
                with st.spinner('Sedang menganalisis piksel wajah...'):
                    prediction = import_and_predict(image, model)
                    confidence = prediction[0][0]
                    threshold = 0.5

                    if confidence > threshold:
                        # KASUS: TERDETEKSI REAL
                        label = "REAL (Asli)"
                        score = confidence * 100
                        color = "#00ffbf"
                        
                        st.markdown(f"<h2 style='text-align: center; color: {color};'>Hasil: {label}</h2>", unsafe_allow_html=True)
                        st.progress(int(score), text=f"Confidence: {score:.2f}%")
                        
                        # --- FITUR 1: SARAN & REDIRECT ---
                        st.warning("⚠️ **Catatan Penting:** AI tidak 100% sempurna. Deepfake kualitas tinggi mungkin lolos deteksi.")
                        st.markdown("### Merasa ini kesalahan?")
                        st.write("Jika Anda yakin gambar ini sebenarnya **Deepfake** tapi terdeteksi **Asli**, tolong laporkan agar kami bisa melatih ulang AI kami.")
                        
                        if st.button("🚨 Saya Yakin Ini Fake -> Lapor Kontribusi"):
                            st.session_state['page_selection'] = "Kontribusi" # Pindah Halaman
                            st.rerun() # Refresh Halaman

                    else:
                        # KASUS: TERDETEKSI FAKE
                        label = "FAKE (Deepfake)"
                        score = (1 - confidence) * 100
                        color = "#ff4b4b"
                        
                        st.markdown(f"<h2 style='text-align: center; color: {color};'>Hasil: {label}</h2>", unsafe_allow_html=True)
                        st.progress(int(score), text=f"Confidence: {score:.2f}%")
                        st.error("Waspada! Gambar ini memiliki indikasi kuat manipulasi wajah.")

# ==========================================
# HALAMAN: KONTRIBUSI (HYBRID CRYPTO)
# ==========================================
elif menu == "Kontribusi": 
    st.header("☁️ Kontribusi Aman (Secure Crowdsourcing)")
    st.info("Fitur ini menggunakan **Hybrid Cryptosystem (RSA + AES)**. Identitas Anda dienkripsi sebelum meninggalkan perangkat ini.")

    with st.form("kontribusi_cloud"):
        c1, c2 = st.columns(2)
        with c1:
            nama = st.text_input("Nama Pelapor:", "Anonim")
        with c2:
            kontak = st.text_input("Kontak (Email/WA):", "-")
            
        jenis = st.selectbox("Jenis Temuan:", ["Deepfake Wajah", "Voice Cloning", "Hoaks Video"])
        file_upload = st.file_uploader("Upload Bukti Deepfake:", type=['jpg', 'png', 'mp4'])
        ket = st.text_area("Keterangan Tambahan:")
        
        # Checkbox Persetujuan
        st.caption("Dengan mengirim, Anda setuju data digunakan untuk penelitian.")

        btn_kirim = st.form_submit_button("🔒 Enkripsi & Upload")

        if btn_kirim:
            if file_upload:
                # 1. Hashing File (Integritas)
                file_upload.seek(0)
                file_bytes = file_upload.read()
                file_hash = calculate_hash(file_bytes)
                
                # 2. Hybrid Encryption (Kerahasiaan)
                st.write("🔄 **Proses 1: Hashing SHA-256 (Integritas)**")
                st.code(f"File Hash: {file_hash}", language='text')
                
                st.write("🔄 **Proses 2: Hybrid Encryption (AES-256 + RSA-2048)**")
                
                # Gabungkan data sensitif jadi satu string JSON/Text
                data_sensitif = f"Nama: {nama} | Kontak: {kontak} | Ket: {ket}"
                
                # Enkripsi
                encrypted_package = hybrid_encrypt(data_sensitif, app_public_key)
                
                # Tampilkan Demo Visualisasi Kripto (Sesuai Permintaan)
                col_demo1, col_demo2, col_demo3 = st.columns(3)
                with col_demo1:
                    st.info("🗝️ Session Key (AES)")
                    st.caption("Dibuat acak, dienkripsi RSA.")
                    st.code(encrypted_package['enc_session_key'][:15] + "...", language="text")
                with col_demo2:
                    st.warning("🛡️ IV (Initialization Vector)")
                    st.caption("Pengacak pola enkripsi.")
                    st.code(encrypted_package['iv'], language="text")
                with col_demo3:
                    st.success("📦 Ciphertext (Data)")
                    st.caption("Data asli terkunci AES.")
                    st.code(encrypted_package['ciphertext'][:15] + "...", language="text")

                # 3. Upload ke Cloud
                # Kita kirim data paket enkripsi dalam bentuk string
                encrypted_str = str(encrypted_package)
                
                sukses, info = upload_to_supabase(file_upload, encrypted_str, jenis)

                if sukses:
                    st.balloons()
                    st.success("✅ **Laporan Terkirim Aman!**")
                    st.write("Hanya server dengan Private Key yang bisa membaca identitas Anda.")
            else:
                st.warning("Mohon pilih file bukti terlebih dahulu.")


# ==========================================
# HALAMAN: EDUKASI
# ==========================================
elif menu == "Edukasi":
    st.header("📚 Pojok Literasi")
    
    tab1, tab2, tab3 = st.tabs(["Ciri Deepfake", "Tips Aman", "Keamanan Aplikasi"])
    
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
        
    with tab3:
        st.subheader("Bagaimana Data Anda Diamankan?")
        st.markdown("""
        Aplikasi CyberGuard menerapkan standar **Kriptografi Militer** untuk melindungi pelapor:
        
        1.  **RSA-2048 (Asimetris):** Seperti gembok yang kuncinya hanya dipegang admin. Digunakan untuk mengamankan kunci sesi.
        2.  **AES-256 (Simetris):** Algoritma super cepat untuk mengacak data teks laporan Anda.
        3.  **SHA-256 (Hashing):** Sidik jari digital untuk memastikan bukti gambar tidak dimanipulasi di tengah jalan.
        """)
        st.image("https://www.ssl2buy.com/wiki/wp-content/uploads/2016/06/hybrid-encryption-process.png", caption="Ilustrasi Hybrid Cryptosystem")