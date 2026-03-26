import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import piexif
import io
import os

# Import HEIF support jika tersedia
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

# --- Konfigurasi Theme ---
def apply_theme(theme):
    if theme == "Gelap":
        return {
            "bg_color": (18, 18, 18),
            "text_color": (255, 255, 255),
            "frame_color": (30, 30, 30),
            "feed_bg": (10, 10, 10)
        }
    else:  # Terang
        return {
            "bg_color": (255, 255, 255),
            "text_color": (0, 0, 0),
            "frame_color": (255, 255, 255),
            "feed_bg": (250, 250, 250)
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
        focal = exif.get(piexif.ExifIFD.FocalLength)

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
        
    except Exception as e:
        filtered.append(("text", f"Error: {str(e)}"))
    return filtered

# --- Fix orientation dari EXIF ---
def fix_image_orientation(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation_key = 274
            if orientation_key in exif:
                orientation = exif[orientation_key]
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except:
        pass
    return image

# --- Crop & Resize dinamis (4:5 atau 1:1) ---
def crop_to_format(image, format_type, theme_colors):
    if format_type == "Bawah (Foto 4:5)":
        target_width, target_height = 1080, 1350
        target_ratio = 1080 / 1350
    else:  # Kanan (Foto 1:1)
        target_width, target_height = 1080, 1080
        target_ratio = 1.0

    width, height = image.size
    img_ratio = width / height

    if img_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    elif img_ratio < target_ratio:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))

    # Gunakan LANCZOS untuk hasil resize terbaik jika versi Pillow mendukung
    try:
        resample_filter = Image.Resampling.LANCZOS
    except AttributeError:
        resample_filter = Image.ANTIALIAS

    image.thumbnail((target_width, target_height), resample_filter)

    final_img = Image.new("RGB", (target_width, target_height), theme_colors["bg_color"])
    x = (target_width - image.width) // 2
    y = (target_height - image.height) // 2
    final_img.paste(image, (x, y))
    
    return final_img

# --- Tambahkan bingkai ---
def add_frame(image, frame_thickness=30, theme_colors=None):
    width, height = image.size
    new_width = width + 2 * frame_thickness
    new_height = height + 2 * frame_thickness
    framed = Image.new("RGB", (new_width, new_height), theme_colors["frame_color"])
    framed.paste(image, (frame_thickness, frame_thickness))
    return framed

# --- Buat Template Final ---
def generate_final_template(image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors, format_type):
    img_width, img_height = image.size

    # Pengaturan Dimensi Area Berdasarkan Format
    if format_type == "Bawah (Foto 4:5)":
        exif_area_height = 200
        total_width = img_width
        total_height = img_height + exif_area_height
        panel_x, panel_y = 0, img_height
        panel_w, panel_h = img_width, exif_area_height
        font_size = int(exif_area_height * 0.13)
        logo_max_size = int(exif_area_height * 0.6)
    else:  # Kanan (Foto 1:1)
        exif_area_width = 380  # Lebar panel kanan
        total_width = img_width + exif_area_width
        total_height = img_height
        panel_x, panel_y = img_width, 0
        panel_w, panel_h = exif_area_width, img_height
        font_size = 32  # Ukuran font agak dibesarkan untuk panel kanan
        logo_max_size = 180

    result_img = Image.new("RGB", (total_width, total_height), theme_colors["bg_color"])
    result_img.paste(image, (0, 0))

    # Load Fonts
    try:
        font = ImageFont.truetype("Barlow-Light.ttf", font_size)
        font_bold = ImageFont.truetype("Barlow-Bold.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
            font_bold = font

    draw = ImageDraw.Draw(result_img)

    # Siapkan Logo
    logo_path = f"logos/{logo_choice}.png"
    logo_found = False
    logo_image = None
    
    if os.path.exists(logo_path):
        try:
            logo_image = Image.open(logo_path).convert("RGBA")
            if format_type == "Bawah (Foto 4:5)":
                ratio = logo_max_size / logo_image.height
            else:
                # Untuk panel kanan, batasi lebar logo agar tidak mentok
                ratio = min(logo_max_size / logo_image.width, 80 / logo_image.height)
            
            logo_image = logo_image.resize((int(logo_image.width * ratio), int(logo_image.height * ratio)))
            logo_found = True
        except:
            pass

    # --- Kalkulasi Posisi Y agar Vertikal Tengah (khusus panel kanan) ---
    line_spacing = 8
    total_lines_height = len(exif_lines) * (font_size + line_spacing)
    
    if logo_found:
        logo_h_actual = logo_image.height
    else:
        logo_h_actual = font_size * 2 # Estimasi untuk fallback teks logo
    
    group_total_height = logo_h_actual + 30 + total_lines_height

    if format_type == "Kanan (Foto 1:1)":
        y_start = panel_y + (panel_h - group_total_height) // 2 + logo_offset
    else:
        y_start = img_height + 20 + logo_offset # Statis untuk bawah

    # Gambar Logo / Fallback Teks
    logo_y = y_start
    if logo_found:
        if watermark_position == "Kiri":
            logo_x = panel_x + 40
        elif watermark_position == "Tengah":
            logo_x = panel_x + (panel_w - logo_image.width) // 2
        else:
            logo_x = panel_x + panel_w - logo_image.width - 40
            
        result_img.paste(logo_image, (logo_x, logo_y), mask=logo_image)
        y_text_start = logo_y + logo_image.height + 30
    else:
        fallback_text = logo_choice.upper()
        try:
            fallback_font = ImageFont.truetype("Barlow-Bold.ttf", int(font_size * 1.5))
        except:
            fallback_font = font_bold
            
        try:
            text_width = draw.textlength(fallback_text, font=fallback_font)
        except:
            text_width = len(fallback_text) * font_size * 0.8
            
        if watermark_position == "Kiri": text_x = panel_x + 40
        elif watermark_position == "Tengah": text_x = panel_x + (panel_w - text_width) // 2
        else: text_x = panel_x + panel_w - text_width - 40
        
        draw.text((text_x, logo_y), fallback_text, font=fallback_font, fill=theme_colors["text_color"])
        y_text_start = logo_y + int(font_size * 1.5) + 30

    # Tulis Teks EXIF
    y = y_text_start
    for item in exif_lines:
        item_type = item[0]
        
        if item_type == "camera":
            make_text = item[1] + " " if item[1] else ""
            model_text = item[2]
            try:
                w_make = draw.textlength(make_text, font=font)
                w_model = draw.textlength(model_text, font=font_bold)
            except:
                w_make = len(make_text) * font_size * 0.6
                w_model = len(model_text) * font_size * 0.6
            text_width = w_make + w_model
            
            if exif_position == "Kiri": x = panel_x + 40
            elif exif_position == "Tengah": x = panel_x + (panel_w - text_width) // 2
            else: x = panel_x + panel_w - text_width - 40

            draw.text((x, y), make_text, font=font, fill=theme_colors["text_color"])
            draw.text((x + w_make, y), model_text, font=font_bold, fill=theme_colors["text_color"])
        else:
            line = item[1]
            try:
                text_width = draw.textlength(line, font=font)
            except:
                text_width = len(line) * font_size * 0.6

            if exif_position == "Kiri": x = panel_x + 40
            elif exif_position == "Tengah": x = panel_x + (panel_w - text_width) // 2
            else: x = panel_x + panel_w - text_width - 40

            draw.text((x, y), line, font=font, fill=theme_colors["text_color"])
            
        y += font_size + line_spacing

    return result_img

# --- Preview mockup IG feed 3 kolom ---
def create_feed_mockup(final_img, theme_colors, format_type):
    # Sesuaikan rasio mockup berdasarkan format
    if format_type == "Bawah (Foto 4:5)":
        preview_w, preview_h = 360, 450
    else: # Landscape/Square base
        ratio = final_img.width / final_img.height
        preview_h = 360
        preview_w = int(preview_h * ratio)

    final_img_resized = final_img.resize((preview_w, preview_h))
    feed_width = 3 * preview_w + 4 * 10
    feed_height = preview_h + 2 * 10

    feed = Image.new("RGB", (feed_width, feed_height), theme_colors["feed_bg"])

    for i in range(3):
        x = 10 + i * (preview_w + 10)
        feed.paste(final_img_resized, (x, 10))

    return feed

# --- UI Streamlit ---
st.set_page_config(page_title="Instagram EXIF Generator", layout="centered", page_icon="📷")

st.markdown("""
<style>
    .main-title { font-size: 2.5em; font-weight: bold; text-align: center; margin-bottom: 10px; }
    .subtitle { text-align: center; color: #666; margin-bottom: 30px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📷 Instagram EXIF Template Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Buat watermark foto profesional dengan data EXIF kamera</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Pengaturan Dasar")
    theme_choice = st.radio("🎨 Theme", ["Terang", "Gelap"], horizontal=True)
    st.markdown("---")
    
    if not os.path.exists("logos"):
        st.warning("⚠️ Folder 'logos' belum ditemukan!")
    else:
        logo_files = os.listdir("logos") if os.path.exists("logos") else []
        if logo_files:
            st.success(f"✅ {len(logo_files)} logo terdeteksi")
            
    st.info("💡 **Tips:** Upload foto asli kamera untuk data EXIF maksimal.")

theme_colors = apply_theme(theme_choice)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📤 Kustomisasi Tampilan")
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "heic", "png"])
    
    if uploaded_file:
        st.markdown("---")
        format_foto = st.radio("📐 Format & Posisi EXIF", ["Bawah (Foto 4:5)", "Kanan (Foto 1:1)"])
        rotate_degrees = st.selectbox("🔄 Rotasi Gambar", [0, 90, 180, 270])
        logo_choice = st.selectbox("📷 Logo Kamera", ["canon", "fujifilm", "samsung", "gopro", "olympus", "fujifilm2", "iphone", "xiaomi"])
        watermark_position = st.radio("📍 Posisi Logo", ["Kiri", "Tengah", "Kanan"], horizontal=True)
        exif_position = st.radio("📝 Posisi Teks", ["Kiri", "Tengah", "Kanan"], horizontal=True)
        logo_offset = st.slider("↕️ Vertikal Offset", -50, 50, 0, help="Geser blok logo & teks ke atas/bawah")
        layout_option = st.selectbox("🖼️ Bingkai Luar", ["Tanpa Bingkai", "Dengan Bingkai"])

with col2:
    if uploaded_file:
        file_bytes = uploaded_file.read()
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image = fix_image_orientation(image)

            if rotate_degrees != 0:
                image = image.rotate(rotate_degrees, expand=True)

            exif_lines = get_filtered_exif(image)
            
            # Crop berdasarkan pilihan format
            image = crop_to_format(image, format_foto, theme_colors)

            if layout_option == "Dengan Bingkai":
                image = add_frame(image, frame_thickness=40, theme_colors=theme_colors)

            # Generate template final
            result_img = generate_final_template(
                image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors, format_foto
            )

            st.image(result_img, caption=f"📸 Preview Template ({format_foto})")

            st.markdown("---")
            st.subheader("📱 Preview Feed")
            feed_mockup = create_feed_mockup(result_img, theme_colors, format_foto)
            st.image(feed_mockup, caption="Simulasi Tampilan Feed")

            buffer = io.BytesIO()
            result_img.save(buffer, format="JPEG", quality=95)
            st.download_button(
                label="📥 Download Template",
                data=buffer.getvalue(),
                file_name=f"instagram_exif_{theme_choice.lower()}.jpg",
                mime="image/jpeg"
            )
            
        except Exception as e:
            st.error(f"❌ Gagal memproses gambar: {e}")
            st.exception(e) 
    else:
        st.info("👆 Upload gambar di panel kiri untuk memulai")
        st.markdown("### Preview akan muncul di sini")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    Made by Brilitech | 
    <a href='https://github.com' target='_blank'>GitHub</a>
</div>
""", unsafe_allow_html=True)
