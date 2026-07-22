# yt-dlp UI

Interface graphique moderne (theme sombre, style YouTube) pour telecharger videos/audio (YouTube + 1000+ sites) via [yt-dlp](https://github.com/yt-dlp/yt-dlp), avec [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

Fonctions : plusieurs liens a la fois (un par ligne, telechargement en chaine), choix format (video mp4, 1080p, 720p, audio mp3), playlists, sous-titres, dossier de sortie, barre de progression, journal.

## Prerequis

- Python 3.9+
- ffmpeg (requis pour fusion video+audio et conversion mp3)

## Installation

1. Cree et active un environnement virtuel (recommande) :

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Installe les dependances Python :

```bash
pip install -r requirements.txt
```

3. Installe ffmpeg (Windows) :

- Via winget :
```bash
winget install ffmpeg
```
- Ou via choco :
```bash
choco install ffmpeg
```
- Ou manuel : telecharge sur https://www.gyan.dev/ffmpeg/builds/, extrait, ajoute le dossier `bin` au PATH.

Verifie l'installation :
```bash
ffmpeg -version
```

## Lancer l'appli

```bash
python main.py
```

## Utilisation

1. Colle le lien video/playlist.
2. Choisis le format (video ou audio mp3).
3. Coche "playlist" si tu veux tout telecharger d'un coup.
4. Choisis le dossier de destination (par defaut `Downloads/yt-dlp-UI`).
5. Clique "Telecharger".

## Mettre a jour yt-dlp

Sites changent souvent leur systeme -> yt-dlp doit rester a jour :

```bash
pip install -U yt-dlp
```
