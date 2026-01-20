from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import textwrap
import os
import sys

app = Flask(__name__)

# --- Configuration ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = "Anton-Regular.ttf"
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350
JPEG_QUALITY = 95

# --- 1. Gestion de la compatibilité Pillow (Le Crash Fix) ---
try:
    # Versions récentes de Pillow (10+)
    RESAMPLE_METHOD = Image.Resampling.LANCZOS
    print("Mode: Pillow Recent (Resampling.LANCZOS)")
except AttributeError:
    # Vieilles versions de Pillow
    # On utilise ANTIALIAS qui est l'ancien nom de LANCZOS
    RESAMPLE_METHOD = Image.ANTIALIAS
    print("Mode: Pillow Ancien (ANTIALIAS)")

# --- 2. Téléchargement Police ---
if not os.path.exists(FONT_PATH):
    print(f"Téléchargement police...")
    try:
        response = requests.get(FONT_URL)
        with open(FONT_PATH, 'wb') as f:
            f.write(response.content)
    except Exception as e:
        print(f"Erreur police: {e}")

@app.route('/generate', methods=['POST'])
def generate_image():
    print("--- Nouvelle requête reçue ---")
    data = request.get_json()
    image_url = data.get('image_url')
    headline_text = data.get('headline', '').upper()

    if not image_url:
        return {"error": "image_url missing"}, 400

    try:
        # 1. Télécharger l'image
        print(f"Téléchargement image: {image_url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        img_source = Image.open(io.BytesIO(response.content)).convert("RGB")
        print("Image ouverte avec succès")

        # 2. Création du fond flouté (Optimisé)
        # On utilise BoxBlur au lieu de GaussianBlur (beaucoup plus léger pour le CPU/RAM)
        background = ImageOps.fit(img_source, (TARGET_WIDTH, TARGET_HEIGHT), method=RESAMPLE_METHOD)
        background = background.filter(ImageFilter.BoxBlur(20)) 
        print("Fond flouté généré")

        # 3. Image principale (Fit sans couper)
        img_foreground = img_source.copy()
        img_foreground.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), RESAMPLE_METHOD)
        
        # Centrage
        x_pos = (TARGET_WIDTH - img_foreground.width) // 2
        y_pos = (TARGET_HEIGHT - img_foreground.height) // 2
        background.paste(img_foreground, (x_pos, y_pos))
        
        final_image = background
        print("Composition terminée")

        # 4. Texte
        draw = ImageDraw.Draw(final_image)
        font_size = 120
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()

        padding_x = 50
        padding_y = 50
        
        # Wrapper le texte
        lines = textwrap.wrap(headline_text, width=15)

        # Calcul hauteur
        total_text_height = 0
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            h = bbox[3] - bbox[1]
            line_heights.append(h)
            total_text_height += h + 10

        current_y = TARGET_HEIGHT - total_text_height - padding_y - 80

        # Dessiner
        for i, line in enumerate(lines):
            # Ombre portée (Shadow)
            draw.text((padding_x + 4, current_y + 4), line, font=font, fill=(0,0,0))
            # Texte Blanc
            draw.text((padding_x, current_y), line, font=font, fill=(255, 255, 255))
            current_y += line_heights[i] + 10

        print("Texte ajouté")

        # 5. Sauvegarde
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=JPEG_QUALITY)
        img_byte_arr.seek(0)
        
        print("Envoi de l'image...")
        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        print(f"ERREUR CRITIQUE: {str(e)}")
        # On imprime l'erreur complète dans la console docker
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500

if __name__ == '__main__':
    # Threaded=True permet de gérer plusieurs requêtes sans bloquer
    app.run(debug=True, host='0.0.0.0', port=5050, threaded=True)