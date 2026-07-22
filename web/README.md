# yt-dlp UI — version web (mobile + hebergement public)

Meme fonctionnalites que l'appli desktop, accessible depuis un lien web (telephone compris).

**Pourquoi pas tout sur Vercel ?** Vercel = serverless, timeout court (10-60s) et pas de ffmpeg dispo facilement. Un telechargement video peut prendre plusieurs minutes -> ca ne marcherait pas de facon fiable. Architecture retenue :

- `frontend/` (page web statique, mobile-friendly) -> **Vercel**
- `backend/` (FastAPI + yt-dlp + ffmpeg, process long OK) -> **Render** (ou Railway / Fly.io / VPS)

## 1. Deployer le backend (Render, gratuit)

1. Cree un compte sur https://render.com
2. Pousse ce repo sur GitHub (ou GitLab).
3. Sur Render : **New +** -> **Web Service** -> connecte ton repo.
4. Renseigne :
   - **Root Directory** : `web/backend`
   - **Runtime** : Docker (Render detecte le `Dockerfile` automatiquement)
   - **Instance Type** : Free
5. Variables d'environnement (onglet Environment) :
   - `FRONTEND_ORIGIN` = URL de ton site Vercel une fois deploye (ex: `https://yt-dlp-ui.vercel.app`), ou `*` pour tester
   - `ACCESS_TOKEN` = un mot de passe simple si tu veux proteger l'acces (recommande, sinon n'importe qui qui trouve le lien peut l'utiliser et consommer ton quota gratuit)
6. Deploie. Note l'URL fournie par Render, ex : `https://yt-dlp-ui-backend.onrender.com`

Note : le tier gratuit Render se met en veille apres 15 min d'inactivite ; le premier appel apres veille prend ~30-50s a redemarrer (normal).

## 2. Deployer le frontend (Vercel, gratuit)

1. Cree un compte sur https://vercel.com
2. **Add New** -> **Project** -> importe ce repo.
3. **Root Directory** : `web/frontend`
4. Framework preset : **Other** (site statique, aucun build necessaire)
5. Deploie. Vercel donne une URL, ex : `https://yt-dlp-ui.vercel.app`

## 3. Connecter les deux

1. Ouvre le site Vercel sur ton telephone.
2. Clique sur l'icone ⚙ (reglages) en haut.
3. Renseigne :
   - **URL du backend** : l'URL Render de l'etape 1 (ex `https://yt-dlp-ui-backend.onrender.com`)
   - **Token d'acces** : le meme mot de passe que `ACCESS_TOKEN` sur Render (si defini)
4. Enregistre. C'est stocke dans le navigateur (localStorage), pas besoin de le refaire a chaque visite.

Partage juste le lien Vercel (+ le token si tu en as mis un) a ton pote qui part en vacances.

## Local (test avant deploiement)

Backend :
```bash
cd web/backend
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

Frontend : ouvre `web/frontend/index.html` directement dans un navigateur (ou sers-le avec `python -m http.server` dans le dossier), puis mets `http://localhost:8000` comme URL backend dans les reglages ⚙.

## Limites a connaitre

- Free tier Render : stockage ephemere (les fichiers sont supprimes 30 min apres generation ou au redemarrage), RAM/CPU limites -> ok pour un usage perso/petit groupe, pas pour du gros volume.
- Playlists : tous les fichiers sont zippes automatiquement avant telechargement.
- Pense a garder yt-dlp a jour cote backend (`pip install -U yt-dlp`) : YouTube change regulierement son systeme.
