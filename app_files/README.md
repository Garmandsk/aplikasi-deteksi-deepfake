# 📱 ADD App (Streamlit)

Folder ini berisi seluruh kode sumber (*source code*) untuk antarmuka pengguna (Frontend) dan logika sistem (Backend) aplikasi CyberGuard.

## 📂 Isi Folder

* **`app.py`**: File utama aplikasi. Menjalankan server Streamlit, mengatur navigasi, dan integrasi modul.
* **`model_deepfake_ori.keras`**: File model AI yang sudah dilatih (Pre-trained Model) untuk mendeteksi Deepfake.
* **`requirements.txt`**: Daftar pustaka Python yang dibutuhkan.
* **`assets/` (Opsional)**: Folder untuk logo, icon, atau gambar statis aplikasi.

## 🛠️ Fitur Utama di Sini

1.  **Modul Deteksi Visual:**
    * Memuat model `.keras` menggunakan TensorFlow.
    * Melakukan pra-pemrosesan gambar (Resize 224x224, Normalisasi).
    * Menampilkan hasil prediksi (Real/Fake) beserta skor kepercayaan (*confidence score*).
## 📊 Metrik Performa Model

Berdasarkan eksperimen terakhir di notebook ini, model MobileNetV2 Ori mencapai:

| Metrik | Skor |
| :--- | :--- |
| **Akurasi** | ~93% |
| **Presisi** | ~93% |
| **Recall** | ~93% |
| **F1-Score** | ~93% |

## 🔧 Cara Menggunakan
Anda dapat membuka file `.ipynb` menggunakan:
* Jupyter Notebook / JupyterLab
* Google Colab (Disarankan untuk akses GPU gratis)
* VS Code (dengan ekstensi Jupyter)

2.  **Modul Kriptografi:**
    * **Hashing (SHA-256):** Menghitung sidik jari digital file yang diupload untuk bukti integritas.
    * **Enkripsi (Fernet/AES):** Mengamankan data teks (nama/keterangan) sebelum dikirim ke Cloud.

3.  **Integrasi Cloud (Supabase):**
    * Menghubungkan aplikasi dengan Supabase Storage untuk fitur *Crowdsourcing*.

## ⚙️ Cara Menjalankan

Pastikan Anda berada di dalam folder ini (`app_files/`) di terminal:

```bash
streamlit run app.py