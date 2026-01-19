# ⚽️ Chrono Ballon - Image Generator.

Il prend en entrée une URL d'image et un titre court, et retourne une image formatée (4:5), filtrée et titrée, prête à être publiée sur les réseaux sociaux.

## 🚀 Fonctionnalités

* **Téléchargement automatique** de l'image source depuis une URL.
* **Redimensionnement intelligent** au format Portrait Instagram (1080x1350 / Ratio 4:5).
* **Design Automatique** : Ajout d'un vignettage sombre (dégradé) pour la lisibilité.
* **Typography** : Utilisation de la police **Anton** (téléchargée automatiquement) pour un style "Breaking News".
* **API REST** : Simple endpoint accessible via HTTP POST.

## 🛠️ Stack Technique

* **Langage** : Python 3.9
* **Serveur Web** : Flask (avec Gunicorn pour la prod)
* **Traitement Image** : Pillow (PIL)
* **Déploiement** : Docker & Docker Compose

---

## 📦 Installation & Déploiement

Ce projet est conçu pour être déployé via **Docker** (par exemple sur Portainer / TrueNAS).

### 1. Structure des fichiers
Assurez-vous que votre dépôt GitHub contient :
* `app.py` (Le code source)
* `requirements.txt` (Les dépendances)
* `Dockerfile` (La construction de l'image)
* `docker-compose.yml` (La configuration du service)

### 2. Déploiement sur Portainer (Recommandé)
1.  Allez dans **Stacks** > **Add stack**.
2.  Nommez la stack (ex: `chrono-generator`).
3.  Sélectionnez **Repository** et collez l'URL de ce dépôt GitHub.
4.  Cliquez sur **Deploy the stack**.

Le service sera accessible sur le port **5050** de votre serveur (configurable dans le `docker-compose.yml`).

---

## 🔌 Utilisation de l'API

### Endpoint
`POST /generate`

### Exemple de Requête (JSON)
Envoyez une requête POST à `http://IP-DE-VOTRE-SERVEUR:5050/generate` avec le corps suivant :

```json
{
  "image_url": "[https://exemple.com/photo-joueur.jpg](https://exemple.com/photo-joueur.jpg)",
  "headline": "SCANDALE AU REAL !"
}