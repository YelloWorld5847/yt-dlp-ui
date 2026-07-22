"""
yt-dlp UI - backend web (FastAPI).
Recoit une URL, telecharge via yt-dlp dans un dossier temporaire, sert le fichier au client.
Concu pour tourner sur un host qui supporte des process longs + ffmpeg (Render, Railway, Fly.io, VPS...).
"""

import os
import shutil
import threading
import time
import uuid
import zipfile
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")
JOB_TTL_SECONDS = 30 * 60

BASE_TMP_DIR = Path(os.environ.get("TMP_DIR", "/tmp/yt-dlp-ui"))
BASE_TMP_DIR.mkdir(parents=True, exist_ok=True)

FORMAT_OPTIONS = {
    "video_best": {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    },
    "video_1080": {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    },
    "video_720": {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    },
    "audio_mp3": {
        "format": "bestaudio/best",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ],
    },
}

app = FastAPI(title="yt-dlp UI backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# job_id -> dict(status, progress, message, filepath, filename, created_at)
JOBS = {}
JOBS_LOCK = threading.Lock()


class JobRequest(BaseModel):
    url: str
    format: str = "video_best"
    playlist: bool = False
    subtitles: bool = False


def check_token(x_access_token: str | None):
    if ACCESS_TOKEN and x_access_token != ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Token d'acces invalide")


def _update_job(job_id, **fields):
    with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(fields)


def _run_job(job_id, req: JobRequest):
    job_dir = BASE_TMP_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    chosen = FORMAT_OPTIONS.get(req.format, FORMAT_OPTIONS["video_best"])

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            fraction = (downloaded / total) if total else 0
            _update_job(job_id, progress=fraction, message=d.get("_percent_str", "").strip())
        elif d["status"] == "finished":
            _update_job(job_id, progress=1.0, message="Post-traitement...")

    ydl_opts = {
        "outtmpl": str(job_dir / "%(title)s.%(ext)s"),
        "noplaylist": not req.playlist,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "format": chosen["format"],
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    if "postprocessors" in chosen:
        ydl_opts["postprocessors"] = chosen["postprocessors"]
    if req.subtitles:
        ydl_opts["writesubtitles"] = True
        ydl_opts["writeautomaticsub"] = True
        ydl_opts["subtitleslangs"] = ["fr", "en"]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([req.url])

        files = [f for f in job_dir.iterdir() if f.is_file()]
        if not files:
            raise RuntimeError("Aucun fichier produit")

        if len(files) > 1:
            zip_path = job_dir / "telechargement.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for f in files:
                    zf.write(f, arcname=f.name)
            final_path, final_name = zip_path, "telechargement.zip"
        else:
            final_path, final_name = files[0], files[0].name

        _update_job(
            job_id, status="ready", progress=1.0, message="Termine",
            filepath=str(final_path), filename=final_name,
        )
    except Exception as exc:
        _update_job(job_id, status="error", message=str(exc))


def _cleanup_loop():
    while True:
        time.sleep(300)
        cutoff = time.time() - JOB_TTL_SECONDS
        with JOBS_LOCK:
            expired = [jid for jid, j in JOBS.items() if j["created_at"] < cutoff]
        for jid in expired:
            shutil.rmtree(BASE_TMP_DIR / jid, ignore_errors=True)
            with JOBS_LOCK:
                JOBS.pop(jid, None)


threading.Thread(target=_cleanup_loop, daemon=True).start()


@app.post("/api/jobs")
def create_job(req: JobRequest, x_access_token: str | None = Header(default=None)):
    check_token(x_access_token)
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL manquante")

    job_id = uuid.uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "running", "progress": 0.0, "message": "Demarrage...",
            "filepath": None, "filename": None, "created_at": time.time(),
        }
    thread = threading.Thread(target=_run_job, args=(job_id, req), daemon=True)
    thread.start()
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, x_access_token: str | None = Header(default=None)):
    check_token(x_access_token)
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job inconnu ou expire")
    return {
        "status": job["status"], "progress": job["progress"], "message": job["message"],
        "filename": job["filename"],
    }


@app.get("/api/jobs/{job_id}/file")
def job_file(job_id: str, x_access_token: str | None = Header(default=None)):
    check_token(x_access_token)
    with JOBS_LOCK:
        job = JOBS.get(job_id)
    if not job or job["status"] != "ready" or not job["filepath"]:
        raise HTTPException(status_code=404, detail="Fichier pas pret")
    return FileResponse(job["filepath"], filename=job["filename"], media_type="application/octet-stream")


@app.get("/api/health")
def health():
    return {"ok": True}
