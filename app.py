from flask import Flask, request, send_file
import requests
from PIL import Image, Image
Draw, ImageFont, ImageFilter, ImageOps
import io
import textwrap
import os

app = Flask(__name__)

# --- Configuration ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
FONT_PATH = "Anton-Regular.ttf"
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350
# On augmente la qualité JPEG (max 100, 95 est excellent)
JPEG_QUALITY = 95

# Télécharger la police si elle n'existe pas
if not os.path.exists(FONT_PATH):
    print(f"Téléchargement de la police {FONT_PATH}...")
    response = requests.get(FONT_URL)
    with open(FONT_PATH, 'wb') as f:
        f.write(response.content)

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

        # --- NOUVELLE LOGIQUE DE REDIMENSIONNEMENT (Fit & Blur) ---

        # A. Créer le fond flouté (Canvas)
        # On redimensionne l'image source pour remplir le cadre cible, puis on floute.
        background = ImageOps.fit(img_source, (TARGET_WIDTH, TARGET_HEIGHT), method=Image.Resampling.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(radius=40)) # Radius = intensité du flou

        # B. Préparer l'image principale (Foreground)
        img_foreground = img_source.copy()
        # .thumbnail redimensionne pour que l'image RENTRE dans la boîte sans être coupée ni déformée.
        # On utilise LANCZOS pour une meilleure qualité de redimensionnement.
        img_foreground.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

        # C. Coller l'image principale au centre du fond flouté
        # Calcul de la position centrale
        x_pos = (TARGET_WIDTH - img_foreground.width) // 2
        y_pos = (TARGET_HEIGHT - img_foreground.height) // 2
        background.paste(img_foreground, (x_pos, y_pos))

        # L'image finale est le résultat de cette composition
        final_image = background

        # --- FIN NOUVELLE LOGIQUE ---


        # 4. Ajouter le texte (Typography "Anton")
        draw = ImageDraw.Draw(final_image)

        # Configuration du texte
        font_size = 120
        text_color = (255, 255, 255) # Blanc
        padding_x = 50
        padding_y = 50
        max_text_width = TARGET_WIDTH - (padding_x * 2)

        font = ImageFont.truetype(FONT_PATH, font_size)

        # Wrapper le texte (retour à la ligne auto)
        lines = textwrap.wrap(headline_text, width=15) # Ajuster le width selon tes besoins

        # Calculer la hauteur totale du bloc de texte pour le placer en bas
        total_text_height = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            total_text_height += bbox[3] - bbox[1] + 10 # +10 pour l'interligne

        # Position de départ Y (en bas)
        current_y = TARGET_HEIGHT - total_text_height - padding_y - 100 # -100 pour remonter un peu

        # Dessiner chaque ligne
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = padding_x # Aligné à gauche
            
            # Optionnel : Petit contour noir pour lisibilité si le fond est clair
            shadow_offset = 3
            draw.text((x + shadow_offset, current_y + shadow_offset), line, font=font, fill=(0,0,0))
            
            draw.text((x, current_y), line, font=font, fill=text_color)
            current_y += text_height + 10

        # 5. Sauvegarder en mémoire avec HAUTE QUALITÉ
        img_byte_arr = io.BytesIO()
        # quality=95 assure une très bonne qualité JPEG (par défaut c'est souvent 75)
        # optimize=True aide à réduire la taille sans perdre de qualité
        final_image.save(img_byte_arr, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        img_byte_arr.seek(0)

        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    # Pour le dev local
    app.run(debug=True, host='0.0.0.0', port=5050)
    # Pour la prod avec Gunicorn :
    # gunicorn -w 4 -b 0.0.0.0:5050 app:app