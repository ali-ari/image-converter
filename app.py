from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image, ImageOps, ImageDraw, ImageFont
import os
from io import BytesIO
from zipfile import ZipFile
import uuid

# Optional background remover
try:
    from rembg import remove
    rembg_available = True
except ImportError:
    rembg_available = False

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def process_image(img_path, options):
    img = Image.open(img_path).convert("RGBA")

    if options['remove_bg'] and rembg_available:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_bytes = remove(buffered.getvalue())
        img = Image.open(BytesIO(img_bytes))


    if options['grayscale']:
        img = ImageOps.grayscale(img)

    if options['resize']:
        img = img.resize(options['resize'])

    # Add logo watermark if uploaded
    if options['watermark_logo']:
        try:
            watermark = Image.open(options['watermark_logo']).convert("RGBA")
            wm_ratio = 0.2  # watermark size relative to image
            watermark = watermark.resize((int(img.width * wm_ratio), int(img.height * wm_ratio)))

            # Calculate position
            pos = options.get('watermark_position', 'bottom-right')
            if pos == 'bottom-right':
                position = (img.width - watermark.width - 10, img.height - watermark.height - 10)
            elif pos == 'bottom-left':
                position = (10, img.height - watermark.height - 10)
            elif pos == 'top-left':
                position = (10, 10)
            elif pos == 'top-right':
                position = (img.width - watermark.width - 10, 10)
            elif pos == 'center':
                position = ((img.width - watermark.width) // 2, (img.height - watermark.height) // 2)
            else:
                position = (img.width - watermark.width - 10, img.height - watermark.height - 10)

            img.paste(watermark, position, watermark)
        except Exception as e:
            print("⚠️ Failed to apply watermark:", e)

    if options['format'] != 'png':
        img = img.convert('RGB')

    unique_id = str(uuid.uuid4())
    filename = os.path.basename(img_path).rsplit('.', 1)[0]
    output_path = os.path.join(CONVERTED_FOLDER, f"{filename}_{unique_id}.{options['format']}")

    img.save(output_path, format=options['format'].upper(), quality=options['quality'], optimize=True)
    return output_path


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        files = request.files.getlist('images')
        format = request.form['format']
        width = request.form.get('width')
        height = request.form.get('height')
        resize = (int(width), int(height)) if width and height else None
        quality = int(request.form.get('quality', 85))
        grayscale = 'grayscale' in request.form
        watermark = request.form.get('watermark')
        remove_bg = 'remove_bg' in request.form
        watermark_file = request.files.get('watermark_logo')
        watermark_position = request.form.get('watermark_position', 'bottom-right')

        options = {
            'format': format,
            'resize': resize,
            'quality': quality,
            'grayscale': grayscale,
            'watermark_logo': watermark_file if watermark_file and watermark_file.filename != '' else None,
            'watermark_position': watermark_position,
            'remove_bg': remove_bg
        }

        output_files = []
        for f in files:
            filename = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(filename)
            out_path = process_image(filename, options)
            output_files.append(out_path)

        if len(output_files) == 1:
            return send_file(output_files[0], as_attachment=True)
        else:
            zip_path = os.path.join(CONVERTED_FOLDER, f"converted_{uuid.uuid4()}.zip")
            with ZipFile(zip_path, 'w') as zipf:
                for file in output_files:
                    zipf.write(file, os.path.basename(file))
            return send_file(zip_path, as_attachment=True)

    return render_template('index.html', rembg_available=rembg_available)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)
    