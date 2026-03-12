# 📷 Instagram EXIF Template Generator

Aplikasi web untuk membuat watermark foto profesional dengan menampilkan data EXIF kamera secara otomatis.

## ✨ Fitur

- 🎨 **Dual Theme**: Mode terang dan gelap
- 📸 **Auto EXIF Detection**: Ekstraksi otomatis data kamera (ISO, Aperture, Shutter Speed, dll)
- 🖼️ **Custom Layout**: Opsi dengan/tanpa bingkai
- 🔄 **Auto Crop**: Resize otomatis ke rasio 4:5 Instagram
- 📱 **Preview Feed**: Simulasi tampilan di Instagram grid
- 🏷️ **Multi Brand Logo**: Mendukung Canon, Fujifilm, Samsung, GoPro, Olympus, iPhone
- 📁 **Format Support**: JPEG, HEIC, PNG

## 🚀 Demo

[Live Demo di Streamlit Cloud](https://your-app-url.streamlit.app)

## 📦 Instalasi

### Prasyarat
- Python 3.8+
- pip

### Langkah Instalasi

1. Clone repository
```bash
git clone https://github.com/username/instagram-exif-generator.git
cd instagram-exif-generator
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Siapkan folder `logos` dengan file PNG logo kamera:
   - `canon.png`
   - `fujifilm.png`
   - `samsung.png`
   - `gopro.png`
   - `olympus.png`
   - `fujifilm2.png`
   - `iphone.png`

4. (Opsional) Tambahkan font `Barlow-Light.ttf` untuk hasil lebih baik

5. Jalankan aplikasi
```bash
streamlit run app.py
```

## 📁 Struktur Folder

```
instagram-exif-generator/
├── app.py                 # File utama aplikasi
├── requirements.txt       # Dependencies Python
├── README.md             # Dokumentasi
├── logos/                # Folder logo kamera (PNG transparan)
│   ├── canon.png
│   ├── fujifilm.png
│   ├── samsung.png
│   ├── gopro.png
│   ├── olympus.png
│   ├── fujifilm2.png
│   └── iphone.png
└── Barlow-Light.ttf      # Font (opsional)
```

## 🎯 Cara Penggunaan

1. **Upload Foto**: Pilih foto dari kamera Anda (format JPEG/HEIC/PNG)
2. **Pilih Theme**: Terang atau Gelap
3. **Kustomisasi**:
   - Pilih logo kamera yang sesuai
   - Atur posisi logo dan teks EXIF
   - Tambahkan bingkai jika diinginkan
4. **Preview**: Lihat hasil dan preview feed Instagram
5. **Download**: Klik tombol download untuk menyimpan

## 🌐 Deploy ke Streamlit Cloud

1. Push repository ke GitHub
2. Buka [share.streamlit.io](https://share.streamlit.io)
3. Login dengan GitHub
4. Pilih repository dan branch
5. Set main file: `app.py`
6. Deploy!

### Catatan Deploy:
- Pastikan file `requirements.txt` sudah benar
- Folder `logos` harus ada di repository
- Font `Barlow-Light.ttf` opsional (akan fallback ke default jika tidak ada)

## 🛠️ Teknologi

- **Streamlit**: Framework web app
- **Pillow (PIL)**: Image processing
- **piexif**: EXIF data extraction
- **pillow-heif**: HEIC format support

## 📝 Lisensi

MIT License - Bebas digunakan untuk proyek personal maupun komersial

## 🤝 Kontribusi

Pull requests are welcome! Untuk perubahan besar, silakan buka issue terlebih dahulu.

## 📧 Kontak

Jika ada pertanyaan atau saran, silakan buka issue di GitHub.

---

Made with ❤️ by Python Enthusiast
