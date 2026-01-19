# app.py
from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import requests
import io
import textwrap
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# URL directe de la font Anton sur Google Fonts
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = "Anton-Regular.ttf"
FONT_SIZE = 110
TEXT_COLOR = (255, 255, 255) # Blanc
SHADOW_COLOR = (0, 0, 0) # Noir

# Télécharge la police si elle n'existe pas
if not os.path.exists(FONT_PATH):
    print("Téléchargement de la police Anton...")
    try:
        r = requests.get(FONT_URL)
        with open(FONT_PATH, 'wb') as f:
            f.write(r.content)
    except Exception as e:
        print(f"Erreur téléchargement police: {e}")

def download_image(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    return Image.open(io.BytesIO(response.content)).convert("RGBA")

def add_design(image, headline):
    # 1. Resize en 4:5 (Format Insta Portrait : 1080x1350)
    target_width, target_height = 1080, 1350
    
    img_ratio = image.width / image.height
    target_ratio = target_width / target_height
    
    if img_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * img_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / img_ratio)
        
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Centre l'image
    left = (new_width - target_width) / 2
    top = (new_height - target_height) / 2
    image = image.crop((left, top, left + target_width, top + target_height))

    # 2. Ajout du dégradé noir (Vignettage bas)
    gradient = Image.new('L', (1, target_height), color=0xFF)
    for y in range(target_height):
        if y > target_height * 0.4: # Commence à 40% de la hauteur
            ratio = (y - target_height * 0.4) / (target_height * 0.6)
            gradient.putpixel((0, y), int(255 * (1 - ratio)))
            
    alpha = gradient.resize((target_width, target_height))
    black_overlay = Image.new('RGBA', (target_width, target_height), color=(0, 0, 0, 220))
    black_overlay.putalpha(Image.eval(alpha, lambda x: 255 - x))
    image = Image.alpha_composite(image, black_overlay)

    # 3. Ajout du texte
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except:
        font = ImageFont.load_default()

    lines = textwrap.wrap(headline.upper(), width=13) 
    
    # Position (En bas à gauche)
    text_height_total = len(lines) * (FONT_SIZE + 10)
    start_y = 1250 - text_height_total 
    
    for line in lines:
        draw.text((65, start_y + 8), line, font=font, fill=SHADOW_COLOR)
        draw.text((60, start_y), line, font=font, fill=TEXT_COLOR)
        start_y += FONT_SIZE + 15

    return image

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        image_url = data.get('image_url')
        headline = data.get('headline', 'BREAKING NEWS')

        if not image_url:
            return {"error": "No image_url provided"}, 400

        img = download_image(image_url)
        final_img = add_design(img, headline)

        img_io = io.BytesIO()
        final_img.convert("RGB").save(img_io, 'JPEG', quality=95)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)