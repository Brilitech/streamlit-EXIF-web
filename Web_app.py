import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import piexif
import io
import os

# --- PAGE CONFIG (HARUS PALING ATAS) ---
st.set_page_config(page_title="EXIF Generator v2.2", layout="wide", page_icon="📷", initial_sidebar_state="expanded")

# Import HEIF support jika tersedia
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- Custom CSS untuk UI yang lebih Cerah, Halus, dan Badge Versi ---
st.markdown("""
<style>
    /* Styling Badge Versi & Header */
    .sidebar-header { display: flex; align-items: center; gap: 10px; margin-bottom: 20px; }
    .main-title { font-size: 1.8em; font-weight: 800; margin: 0; color: #1f2937; }
    .version-badge { background-color: #3b82f6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
    
    /* Memperhalus elemen UI Streamlit */
    div.stButton > button { border-radius: 8px; font-weight: 600; transition: all 0.3s; width: 100%; border: 1px solid #e5e7eb; }
    div.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); border-color: #3b82f6; color: #3b82f6; }
    div[data-testid="stSidebar"] { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
    
    /* Penyeragaman Font */
    .stRadio label, .stSlider label, .stSelectbox label { font-size: 1rem !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# --- Konfigurasi Theme ---
def apply_theme(theme):
    if theme == "Gelap":
        return {
            "bg_color": (18, 18, 18), "text_color": (255, 255, 255), "frame_color": (30, 30, 30), "feed_bg": (10, 10, 10)
        }
    else:  # Terang
        return {
            "bg_color": (255, 255, 255), "text_color": (0, 0, 0), "frame_color": (255, 255, 255), "feed_bg": (240, 242, 245)
        }

# --- Ambil hanya nilai EXIF ---
def get_filtered_exif(image):
    filtered = []
    try:
        exif_dict = piexif.load(image.info.get('exif', b''))
        zeroth = exif_dict.get("0th", {})
        exif = exif_dict.get("Exif", {})

        make = zeroth.get(piexif.ImageIFD.Make, b"").decode(errors='ignore').strip()
        model = zeroth.get(piexif.ImageIFD.Model, b"").decode(errors='ignore').strip()
        lens = exif.get(piexif.ExifIFD.LensModel, b"").decode(errors='ignore').strip()

        iso = exif.get(piexif.ExifIFD.ISOSpeedRatings)
        fnumber = exif.get(piexif.ExifIFD.FNumber)
        exposure = exif.get(piexif.ExifIFD.ExposureTime)

        if fnumber:
            f_val = round(fnumber[0] / fnumber[1], 1)
            filtered.append(("text", f"f/{f_val}"))
        if exposure:
            filtered.append(("text", f"{exposure[0]}/{exposure[1]}s"))
        if iso:
            filtered.append(("text", f"ISO {iso}"))
            
        if make or model:
            filtered.append(("camera", make, model))
            
        if lens:
            filtered.append(("text", f"{lens}"))
    except:
        pass
    return filtered

# --- Fix orientation dari EXIF ---
def fix_image_orientation(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation_key = 274
            if orientation_key in exif:
                orientation = exif[orientation_key]
                if orientation == 3: image = image.rotate(180, expand=True)
                elif orientation == 6: image = image.rotate(270, expand=True)
                elif orientation == 8: image = image.rotate(90, expand=True)
    except:
        pass
    return image

# --- Crop & Resize ---
def crop_to_format(image, format_type, crop_x=0.5, crop_y=0.5):
    if format_type == "Bawah (Foto 4:5)": target_size = (1080, 1150)
    else: target_size = (700, 1080)

    try: resample_filter = Image.Resampling.LANCZOS
    except AttributeError: resample_filter = Image.ANTIALIAS

    return ImageOps.fit(image, target_size, method=resample_filter, centering=(crop_x, crop_y))

# --- Tambahkan bingkai ---
def add_frame(image, frame_thickness=30, theme_colors=None):
    width, height = image.size
    framed = Image.new("RGB", (width + 2 * frame_thickness, height + 2 * frame_thickness), theme_colors["frame_color"])
    framed.paste(image, (frame_thickness, frame_thickness))
    return framed

# --- Buat Template Final ---
def generate_final_template(image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors, format_type, logo_scale=1.0, font_scale=1.0):
    img_width, img_height = image.size

    if format_type == "Bawah (Foto 4:5)":
        total_width, total_height = 1080, 1350
        panel_x, panel_y, panel_w, panel_h = 0, img_height, 1080, total_height - img_height
        base_font_size, base_logo_max_size = int(panel_h * 0.15), int(panel_h * 0.5)
    else: 
        total_width, total_height = 1080, 1080
        panel_x, panel_y, panel_w, panel_h = img_width, 0, total_width - img_width, 1080
        base_font_size, base_logo_max_size = 32, 180

    font_size = int(base_font_size * font_scale)
    logo_max_size = int(base_logo_max_size * logo_scale)

    result_img = Image.new("RGB", (total_width, total_height), theme_colors["bg_color"])
    result_img.paste(image, (0, 0))

    try:
        font = ImageFont.truetype("Barlow-Light.ttf", font_size)
        font_bold = ImageFont.truetype("Barlow-Bold.ttf", font_size)
    except:
        font = font_bold = ImageFont.load_default()

    draw = ImageDraw.Draw(result_img)

    logo_path = f"logos/{logo_choice}.png"
    logo_found, logo_image = False, None
    if os.path.exists(logo_path):
        try:
            logo_image = Image.open(logo_path).convert("RGBA")
            ratio = min(logo_max_size / logo_image.width, logo_max_size / logo_image.height) if format_type == "Kanan (Foto 1:1)" else logo_max_size / logo_image.height
            logo_image = logo_image.resize((int(logo_image.width * ratio), int(logo_image.height * ratio)))
            logo_found = True
        except: pass

    line_spacing = int(8 * font_scale)
    total_lines_height = len(exif_lines) * font_size + max(0, len(exif_lines) - 1) * line_spacing
    logo_h_actual = logo_image.height if logo_found else int(font_size * 1.5)

    if format_type == "Bawah (Foto 4:5)":
        center_y = panel_y + (panel_h // 2) + logo_offset
        logo_y = center_y - (logo_h_actual // 2)
        y_text_start = center_y - (total_lines_height // 2)
    else: 
        start_y = panel_y + (panel_h - (logo_h_actual + 30 + total_lines_height)) // 2 + logo_offset
        logo_y, y_text_start = start_y, start_y + logo_h_actual + 30

    # Render Logo
    if logo_found:
        if watermark_position == "Kiri": logo_x = panel_x + 40
        elif watermark_position == "Tengah": logo_x = panel_x + (panel_w - logo_image.width) // 2
        else: logo_x = panel_x + panel_w - logo_image.width - 40
        result_img.paste(logo_image, (logo_x, logo_y), mask=logo_image)
    else:
        fallback_text = logo_choice.upper()
        try: fallback_font = ImageFont.truetype("Barlow-Bold.ttf", int(font_size * 1.5))
        except: fallback_font = font_bold
        try: text_width = draw.textlength(fallback_text, font=fallback_font)
        except: text_width = len(fallback_text) * font_size * 0.8
        
        if watermark_position == "Kiri": text_x = panel_x + 40
        elif watermark_position == "Tengah": text_x = panel_x + (panel_w - text_width) // 2
        else: text_x = panel_x + panel_w - text_width - 40
        draw.text((text_x, logo_y), fallback_text, font=fallback_font, fill=theme_colors["text_color"])

    # Render Teks EXIF
    y = y_text_start
    for item in exif_lines:
        if item[0] == "camera":
            make_text, model_text = (item[1] + " " if item[1] else ""), item[2]
            try: w_make, w_model = draw.textlength(make_text, font=font), draw.textlength(model_text, font=font_bold)
            except: w_make, w_model = len(make_text) * font_size * 0.6, len(model_text) * font_size * 0.6
            text_width = w_make + w_model
            
            if exif_position == "Kiri": x = panel_x + 40
            elif exif_position == "Tengah": x = panel_x + (panel_w - text_width) // 2
            else: x = panel_x + panel_w - text_width - 40

            draw.text((x, y), make_text, font=font, fill=theme_colors["text_color"])
            draw.text((x + w_make, y), model_text, font=font_bold, fill=theme_colors["text_color"])
        else:
            line = item[1]
            try: text_width = draw.textlength(line, font=font)
            except: text_width = len(line) * font_size * 0.6

            if exif_position == "Kiri": x = panel_x + 40
            elif exif_position == "Tengah": x = panel_x + (panel_w - text_width) // 2
            else: x = panel_x + panel_w - text_width - 40

            draw.text((x, y), line, font=font, fill=theme_colors["text_color"])
        y += font_size + line_spacing

    return result_img

# --- UI SIDEBAR (Kiri Paling Ujung) ---
with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <div class="main-title">📷 EXIF Gen</div>
            <div class="version-badge">v2.2</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📤 Upload Foto")
    uploaded_file = st.file_uploader("Pilih file gambar...", type=["jpg", "jpeg", "heic", "png"], label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("### ⚙️ Pengaturan Dasar")
    theme_choice = st.radio("🎨 Tema Kanvas", ["Terang", "Gelap"], horizontal=True)
    
    if os.path.exists("logos"):
        logo_files = os.listdir("logos")
        if logo_files: st.caption(f"✅ {len(logo_files)} logo siap digunakan.")
    else: st.warning("⚠️ Folder 'logos' tidak ditemukan.")

theme_colors = apply_theme(theme_choice)

# --- UI MAIN AREA (Bagi 2 Kolom: Kiri Kontrol, Kanan Preview) ---
if uploaded_file:
    # Membagi layar: 40% untuk panel pengaturan, 60% untuk preview
    col_controls, col_space, col_preview = st.columns([4, 0.5, 5.5])

    with col_controls:
        st.subheader("🛠️ Kustomisasi Layout")
        
        # Kelompok Format & Crop
        with st.container(border=True):
            format_foto = st.radio("📐 Format Instagram", ["Bawah (Foto 4:5)", "Kanan (Foto 1:1)"])
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            st.markdown("**✂️ Sesuaikan Posisi Crop:**")
            crop_x = st.slider("↔️ Fokus Horizontal", 0, 100, 50, label_visibility="visible") / 100.0
            crop_y = st.slider("↕️ Fokus Vertikal", 0, 100, 50, label_visibility="visible") / 100.0

        # Kelompok Skala
        with st.container(border=True):
            st.markdown("**📏 Ukuran Elemen:**")
            logo_scale = st.slider("🔍 Skala Logo (%)", 30, 200, 100, step=5) / 100.0
            font_scale = st.slider("🔠 Skala Teks EXIF (%)", 50, 200, 100, step=5) / 100.0
            logo_offset = st.slider("↕️ Vertikal Offset (Geser Atas/Bawah)", -100, 100, 0)

        # Kelompok Detail Tambahan
        with st.container(border=True):
            st.markdown("**🎨 Elemen & Posisi:**")
            logo_choice = st.selectbox("📷 Pilih Logo Kamera", ["canon", "fujifilm", "samsung", "gopro", "olympus", "fujifilm2", "iphone", "xiaomi"])
            col_pos1, col_pos2 = st.columns(2)
            with col_pos1:
                watermark_position = st.radio("📍 Posisi Logo", ["Kiri", "Tengah", "Kanan"], index=0)
            with col_pos2:
                exif_position = st.radio("📝 Posisi Teks", ["Kiri", "Tengah", "Kanan"], index=2)
            
            layout_option = st.selectbox("🖼️ Bingkai Luar", ["Tanpa Bingkai", "Dengan Bingkai"])
            rotate_degrees = st.selectbox("🔄 Rotasi Gambar", [0, 90, 180, 270])

    with col_preview:
        st.subheader("👁️ Live Preview")
        file_bytes = uploaded_file.read()
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image = fix_image_orientation(image)

            if rotate_degrees != 0: image = image.rotate(rotate_degrees, expand=True)

            exif_lines = get_filtered_exif(image)
            image = crop_to_format(image, format_foto, crop_x, crop_y)

            result_img = generate_final_template(
                image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors, format_foto, logo_scale, font_scale
            )

            if layout_option == "Dengan Bingkai":
                result_img = add_frame(result_img, frame_thickness=40, theme_colors=theme_colors)

            # Gambar akan otomatis menyesuaikan lebar kolom tanpa perlu scroll lebar!
            st.image(result_img, use_column_width=True)

            # Tombol Download tepat di bawah preview utama
            buffer = io.BytesIO()
            result_img.save(buffer, format="JPEG", quality=95)
            st.download_button(
                label="📥 Download Hasil Akhir",
                data=buffer.getvalue(),
                file_name=f"IG_EXIF_{theme_choice.lower()}_{format_foto[:5]}.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"❌ Gagal memproses gambar: {e}")

else:
    # Tampilan selamat datang sebelum upload
    st.info("👈 Silakan unggah foto pada panel di sebelah kiri untuk memulai proses desain.")
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888;'>
        <h3>Selamat datang di EXIF Gen v2.2</h3>
        <p>Aplikasi untuk menambahkan template EXIF elegan pada foto Instagram Anda secara otomatis.</p>
    </div>
    """, unsafe_allow_html=True)
