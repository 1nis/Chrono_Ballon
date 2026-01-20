from flask import Flask, request, send_file
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import textwrap
import os

app = Flask(__name__)

# --- Configuration ---
# On utilise une URL stable pour la police Anton
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = "Anton-Regular.ttf"
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350
JPEG_QUALITY = 95

# Télécharger la police au démarrage si absente
if not os.path.exists(FONT_PATH):
    print(f"Téléchargement de la police {FONT_PATH}...")
    try:
        response = requests.get(FONT_URL)
        response.raise_for_status()
        with open(FONT_PATH, 'wb') as f:
            f.write(response.content)
        print("Police téléchargée avec succès.")
    except Exception as e:
        print(f"Erreur téléchargement police: {e}")

@app.route('/generate', methods=['POST'])
def generate_image():
    data = request.get_json()
    image_url = data.get('image_url')
    headline_text = data.get('headline', '').upper()

    if not image_url:
        return {"error": "image_url is required"}, 400

    try:
        # 1. Télécharger l'image source
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        img_source = Image.open(io.BytesIO(response.content)).convert("RGB")

        # --- LOGIQUE FIT & BLUR ---
        
        # A. Créer le fond flouté
        # On remplit tout l'espace 1080x1350 avec l'image (quitte à couper)
        background = ImageOps.fit(img_source, (TARGET_WIDTH, TARGET_HEIGHT), method=Image.Resampling.LANCZOS)
        # On applique un flou puissant
        background = background.filter(ImageFilter.GaussianBlur(radius=40))

        # B. Préparer l'image principale (nette)
        img_foreground = img_source.copy()
        # On la redimensionne pour qu'elle tienne ENTIÈREMENT dans le cadre (sans couper)
        img_foreground.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

        # C. Centrer l'image nette sur le fond flou
        x_pos = (TARGET_WIDTH - img_foreground.width) // 2
        y_pos = (TARGET_HEIGHT - img_foreground.height) // 2
        background.paste(img_foreground, (x_pos, y_pos))

        final_image = background
        # --- FIN LOGIQUE ---

        # 2. Ajouter le texte
        draw = ImageDraw.Draw(final_image)
        
        # Réglages texte
        font_size = 120
        # On charge la police (ou une police par défaut si échec)
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()

        padding_x = 50
        padding_y = 50
        
        # Wrapper le texte pour qu'il ne dépasse pas
        # On estime grossièrement : environ 15 caractères pour cette taille de police
        lines = textwrap.wrap(headline_text, width=15)

        # Calculer la hauteur totale du bloc de texte pour le placer en bas
        total_text_height = 0
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            h = bbox[3] - bbox[1]
            line_heights.append(h)
            total_text_height += h + 10 # +10 padding entre lignes

        # Position de départ Y (Aligné en bas avec une marge)
        current_y = TARGET_HEIGHT - total_text_height - padding_y - 80

        # Dessiner le texte ligne par ligne
        for i, line in enumerate(lines):
            # Centrer le texte horizontalement ? (Optionnel, ici aligné gauche + marge)
            # Pour centrer : x = (TARGET_WIDTH - draw.textlength(line, font)) // 2
            x = padding_x 
            
            # Effet "Ombre portée" noire pour lisibilité sur fond clair
            shadow_offset = 4
            draw.text((x + shadow_offset, current_y + shadow_offset), line, font=font, fill=(0,0,0))
            
            # Texte blanc
            draw.text((x, current_y), line, font=font, fill=(255, 255, 255))
            
            current_y += line_heights[i] + 10

        # 3. Sauvegarder
        img_byte_arr = io.BytesIO()
        final_image.save(img_byte_arr, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        img_byte_arr.seek(0)

        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        print(f"Erreur: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)