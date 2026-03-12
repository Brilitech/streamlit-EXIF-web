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
            filtered.append(f"f/{f_val}")
        if exposure:
            filtered.append(f"{exposure[0]}/{exposure[1]}s")
        if iso:
            filtered.append(f"ISO {iso}")
        if make or model:
            filtered.append(f"{make} {model}".strip())
        if lens:
            filtered.append(f"{lens}")
        
    except Exception as e:
        filtered.append(f"Error: {str(e)}")
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

# --- Crop, resize, dan center ke 1080x1350 canvas ---
def crop_and_fit_to_4x5(image, theme_colors):
    target_width, target_height = 1080, 1350
    target_ratio = target_width / target_height

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

    image.thumbnail((target_width, target_height))

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

def generate_final_template(image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors):
    img_width, img_height = image.size
    exif_area_height = 200
    total_height = img_height + exif_area_height

    result_img = Image.new("RGB", (img_width, total_height), theme_colors["bg_color"])
    result_img.paste(image, (0, 0))

    font_size = int(exif_area_height * 0.13)
    try:
        font = ImageFont.truetype("Barlow-Light.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()

    draw = ImageDraw.Draw(result_img)
    y_start = img_height + 20

    # Logo kamera
    logo_path = f"logos/{logo_choice}.png"

    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            max_logo_height = int(exif_area_height * 0.6)
            ratio = max_logo_height / logo.height
            logo = logo.resize((int(logo.width * ratio), max_logo_height))

            if watermark_position == "Kiri":
                logo_x = 30
            elif watermark_position == "Tengah":
                logo_x = (img_width - logo.width) // 2
            else:
                logo_x = img_width - logo.width - 30

            logo_y = y_start + logo_offset
            result_img.paste(logo, (logo_x, logo_y), mask=logo)

        except Exception as e:
            print("Logo error:", e)

    # Tulis teks EXIF
    y = y_start
    for line in exif_lines:
        try:
            text_width = draw.textlength(line, font=font)
        except:
            # Fallback untuk versi PIL lama
            text_width = len(line) * font_size * 0.6

        if exif_position == "Kiri":
            x = 40
        elif exif_position == "Tengah":
            x = (img_width - text_width) // 2
        else:
            x = img_width - text_width - 40

        draw.text((x, y), line, font=font, fill=theme_colors["text_color"])
        y += font_size + 5

    return result_img

# --- Preview mockup IG feed 3 kolom ---
def create_feed_mockup(final_img, theme_colors):
    final_img_resized = final_img.resize((360, 450))
    feed_width = 3 * 360 + 4 * 10
    feed_height = 450 + 2 * 10

    feed = Image.new("RGB", (feed_width, feed_height), theme_colors["feed_bg"])

    for i in range(3):
        x = 10 + i * (360 + 10)
        feed.paste(final_img_resized, (x, 10))

    return feed

# --- UI Streamlit ---
st.set_page_config(page_title="Instagram EXIF Generator", layout="centered", page_icon="📷")

# Custom CSS untuk styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📷 Instagram EXIF Template Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Buat watermark foto profesional dengan data EXIF kamera</div>', unsafe_allow_html=True)

# Sidebar untuk pengaturan
with st.sidebar:
    st.header("⚙️ Pengaturan")
    theme_choice = st.radio("🎨 Theme", ["Terang", "Gelap"], horizontal=True)
    st.markdown("---")
    st.info("💡 **Tips:** Upload foto hasil kamera untuk mendapatkan data EXIF yang lengkap")

# Apply theme
theme_colors = apply_theme(theme_choice)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📤 Upload & Kustomisasi")
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "heic", "png"], help="Mendukung JPEG, HEIC, dan PNG")
    
    if uploaded_file:
        st.markdown("---")
        rotate_degrees = st.selectbox("🔄 Rotasi Gambar", [0, 90, 180, 270])
        logo_choice = st.selectbox("📷 Logo Kamera", ["canon", "fujifilm", "samsung", "gopro", "olympus", "fujifilm2", "iphone"])
        watermark_position = st.radio("📍 Posisi Logo", ["Kiri", "Tengah", "Kanan"], horizontal=True)
        exif_position = st.radio("📝 Posisi Teks EXIF", ["Kiri", "Tengah", "Kanan"], horizontal=True)
        logo_offset = st.slider("↕️ Offset Logo", 0, 50, 10, help="Geser logo ke bawah")
        layout_option = st.selectbox("🖼️ Layout", ["Tanpa Bingkai", "Dengan Bingkai"])

with col2:
    if uploaded_file:
        file_bytes = uploaded_file.read()
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            image = fix_image_orientation(image)

            if rotate_degrees != 0:
                image = image.rotate(rotate_degrees, expand=True)

            exif_lines = get_filtered_exif(image)
            
            # Apply theme saat crop
            image = crop_and_fit_to_4x5(image, theme_colors)

            if layout_option == "Dengan Bingkai":
                image = add_frame(image, frame_thickness=40, theme_colors=theme_colors)

            # Generate template dengan theme
            result_img = generate_final_template(
                image, exif_lines, logo_choice, watermark_position, exif_position, logo_offset, theme_colors
            )

            st.image(result_img, caption="📸 Preview Template")

            st.markdown("---")
            st.subheader("📱 Preview Feed Instagram")
            feed_mockup = create_feed_mockup(result_img, theme_colors)
            st.image(feed_mockup, caption="Grid 3 Kolom Instagram")

            # Download button
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
            st.exception(e)  # Tampilkan detail error untuk debugging
    else:
        st.info("👆 Upload gambar di panel kiri untuk memulai")
        
        # Placeholder sederhana tanpa error
        st.markdown("### Preview akan muncul di sini")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    Made with ❤️ by Python Enthusiast | 
    <a href='https://github.com' target='_blank'>GitHub</a>
</div>
""", unsafe_allow_html=True)
