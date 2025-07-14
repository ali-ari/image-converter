from PIL import Image, ImageOps, ImageDraw, ImageFont
import os
from io import BytesIO


# Optional: Background removal using rembg
try:
    from rembg import remove
    rembg_available = True
except ImportError:
    rembg_available = False

def convert_image(
    input_path,
    output_format="png",
    resize=None,
    compress_quality=85,
    grayscale=False,
    add_watermark=False,
    watermark_text="Sample",
    background_remove=False
):
    try:
        img = Image.open(input_path).convert("RGBA")  # Always load with alpha for background remove

        if background_remove and rembg_available:
            img_bytes = remove(img)
            img = Image.open(BytesIO(img_bytes))

        if grayscale:
            img = ImageOps.grayscale(img)

        if resize:
            img = img.resize(resize)

        if add_watermark:
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()
            text_position = (10, 10)
            text_color = (255, 255, 255, 128)  # White with transparency
            draw.text(text_position, watermark_text, font=font, fill=text_color)

        file_name, _ = os.path.splitext(input_path)
        output_path = f"{file_name}_converted.{output_format.lower()}"

        img = img.convert("RGB") if output_format.lower() != "png" else img
        img.save(
            output_path,
            format=output_format.upper(),
            quality=compress_quality,
            optimize=True  # <-- added!
        )

        print(f"✅ Saved: {output_path}")
    except Exception as e:
        print(f"❌ Failed to convert {input_path}: {e}")

def batch_convert(
    folder_path,
    output_format="png",
    resize=None,
    compress_quality=85,
    grayscale=False,
    add_watermark=False,
    watermark_text="Sample",
    background_remove=False
):
    supported_formats = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff")

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(supported_formats):
            input_path = os.path.join(folder_path, filename)
            convert_image(
                input_path,
                output_format=output_format,
                resize=resize,
                compress_quality=compress_quality,
                grayscale=grayscale,
                add_watermark=add_watermark,
                watermark_text=watermark_text,
                background_remove=background_remove
            )


