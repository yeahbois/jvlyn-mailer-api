import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

# Configuration
TEMPLATE_PATH = "assets/ticket_template.jpg"
FONT_PATH = "assets/font.ttf"
# Vercel filesystem is read-only except for /tmp
OUTPUT_DIR = "/tmp/temp_tickets"
QR_DIR = "/tmp/temp_qrs"

# Coordinates from snippet
NAME_POS = (641, 866)
JENIS_TIKET_POS = (641, 1023)
EMAIL_POS = (641, 699)
NOMOR_PESANAN_POS = (52, 1262)
QR_POS = (137, 667)

# Ensure directories exist in /tmp
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

def generate_qr(data, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(QR_DIR, f"{filename}.png")
    img.save(path)
    return path

def wrap_text(text, max_chars=20):
    return "\n".join(textwrap.wrap(text, width=max_chars))

def create_ticket(buyer_name, buyer_email, order_id, ticket_id, ticket_type):
    if not os.path.exists(TEMPLATE_PATH):
        # Create a dummy template for testing if it doesn't exist
        dummy = Image.new('RGB', (1410, 2000), color=(255, 255, 255))
        os.makedirs(os.path.dirname(TEMPLATE_PATH), exist_ok=True)
        dummy.save(TEMPLATE_PATH)

    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(base)

    # Use bundled font for better readability
    try:
        font_mid = ImageFont.truetype(FONT_PATH, 33)
    except Exception as e:
        print(f"Error loading font: {e}. Falling back to default.")
        font_mid = ImageFont.load_default()

    # Draw text
    wrapped_name = wrap_text(buyer_name.upper(), max_chars=20)
    draw.text(NAME_POS, wrapped_name, fill="black", font=font_mid)
    draw.text(JENIS_TIKET_POS, str(ticket_type), fill="black", font=font_mid)
    draw.text(EMAIL_POS, str(buyer_email), fill="black", font=font_mid)
    draw.text(NOMOR_PESANAN_POS, f"#{order_id}", fill="black", font=font_mid)
    draw.text((571, 1362), "Sabtu, 18 Juli 2026", fill="black", font=font_mid)

    # Generate and paste QR
    qr_path = generate_qr(ticket_id, ticket_id)
    qr_img = Image.open(qr_path).convert("RGBA")
    qr_img = qr_img.resize((374, 374), Image.Resampling.NEAREST)

    base.paste(qr_img, QR_POS, qr_img)

    output_path = os.path.join(OUTPUT_DIR, f"ticket_{ticket_id}.png")
    base.save(output_path)

    # Cleanup QR
    if os.path.exists(qr_path):
        os.remove(qr_path)

    return output_path
