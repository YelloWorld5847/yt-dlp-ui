"""
yt-dlp UI - interface graphique moderne pour telecharger des videos (YouTube et 1000+ autres sites)
Utilise yt-dlp comme moteur de telechargement, customtkinter pour l'interface.
"""

import os
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT = "#FF3B3B"
ACCENT_HOVER = "#D62F2F"
BG = "#12141A"
CARD = "#1B1E27"
SUBTEXT = "#8B8FA3"

DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "yt-dlp-UI")

FORMAT_OPTIONS = {
    "Meilleure qualite video (mp4)": {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    },
    "Video 1080p max": {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    },
    "Video 720p max": {
        "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
    },
    "Audio seul (mp3)": {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    },
}


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("yt-dlp UI")
        self.geometry("760x680")
        self.minsize(680, 600)
        self.configure(fg_color=BG)

        self.log_queue = queue.Queue()
        self.output_dir = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.format_var = tk.StringVar(value=list(FORMAT_OPTIONS.keys())[0])
        self.playlist_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=False)

        self._build_ui()
        self.after(100, self._poll_log_queue)

    # ---------- UI ----------

    def _card(self, parent, title=None):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14)
        if title:
            ctk.CTkLabel(
                card, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                text_color=SUBTEXT, anchor="w"
            ).pack(fill="x", padx=16, pady=(14, 4))
        return card

    def _build_ui(self):
        root = ctk.CTkScrollableFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=22, pady=20)

        # Header
        header = ctk.CTkFrame(root, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        ctk.CTkLabel(
            header, text="▶ yt-dlp UI", font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white"
        ).pack(side="left")
        ctk.CTkLabel(
            header, text="YouTube & 1000+ sites", font=ctk.CTkFont(size=13),
            text_color=SUBTEXT
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        # URL card
        url_card = self._card(root, "LIENS  –  un par ligne (video ou playlist)")
        url_card.pack(fill="x", pady=(0, 16))
        self.url_text = ctk.CTkTextbox(
            url_card, height=110, fg_color="#11131A", corner_radius=10,
            border_width=1, border_color="#2A2E3B", font=ctk.CTkFont(size=13)
        )
        self.url_text.pack(fill="x", padx=16, pady=(0, 16))

        # Options card
        opts_card = self._card(root, "OPTIONS")
        opts_card.pack(fill="x", pady=(0, 16))

        row1 = ctk.CTkFrame(opts_card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(row1, text="Format", text_color="white").pack(side="left")
        format_menu = ctk.CTkOptionMenu(
            row1, values=list(FORMAT_OPTIONS.keys()), variable=self.format_var,
            fg_color="#2A2E3B", button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            dropdown_fg_color="#1B1E27", width=260
        )
        format_menu.pack(side="right")

        row2 = ctk.CTkFrame(opts_card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 4))
        ctk.CTkSwitch(
            row2, text="Telecharger toute la playlist", variable=self.playlist_var,
            progress_color=ACCENT, button_color="white"
        ).pack(side="left", expand=True, anchor="w")

        row3 = ctk.CTkFrame(opts_card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkSwitch(
            row3, text="Sous-titres (fr/en) si disponibles", variable=self.subtitles_var,
            progress_color=ACCENT, button_color="white"
        ).pack(side="left", expand=True, anchor="w")

        # Output dir card
        out_card = self._card(root, "DOSSIER DE DESTINATION")
        out_card.pack(fill="x", pady=(0, 16))
        out_row = ctk.CTkFrame(out_card, fg_color="transparent")
        out_row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkEntry(
            out_row, textvariable=self.output_dir, fg_color="#11131A",
            border_width=1, border_color="#2A2E3B"
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(
            out_row, text="Parcourir", width=100, command=self._choose_dir,
            fg_color="#2A2E3B", hover_color="#363B4A"
        ).pack(side="left")

        # Action row
        action_row = ctk.CTkFrame(root, fg_color="transparent")
        action_row.pack(fill="x", pady=(0, 16))
        self.download_btn = ctk.CTkButton(
            action_row, text="⬇  Telecharger", height=46, corner_radius=12,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._start_download
        )
        self.download_btn.pack(fill="x")

        progress_row = ctk.CTkFrame(root, fg_color="transparent")
        progress_row.pack(fill="x", pady=(0, 16))
        self.progress = ctk.CTkProgressBar(
            progress_row, height=14, corner_radius=8, progress_color=ACCENT,
            fg_color="#2A2E3B"
        )
        self.progress.set(0)
        self.progress.pack(fill="x", side="left", expand=True, padx=(0, 10))
        self.progress_label = ctk.CTkLabel(progress_row, text="0%", text_color=SUBTEXT, width=44)
        self.progress_label.pack(side="left")

        # Log card
        log_card = self._card(root, "JOURNAL")
        log_card.pack(fill="both", expand=True)
        self.log_text = ctk.CTkTextbox(
            log_card, fg_color="#0E1015", corner_radius=10, border_width=1,
            border_color="#2A2E3B", font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#B7F5C6"
        )
        self.log_text.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log_text.configure(state="disabled")

    # ---------- Logic ----------

    def _choose_dir(self):
        chosen = filedialog.askdirectory(initialdir=self.output_dir.get() or os.getcwd())
        if chosen:
            self.output_dir.set(chosen)

    def _log(self, message):
        self.log_queue.put(message)

    def _poll_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", message + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)

    def _set_progress(self, fraction, label):
        self.progress.set(fraction)
        self.progress_label.configure(text=label)

    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                fraction = downloaded / total
                pct_text = f"{int(fraction * 100)}%"
                self.after(0, lambda: self._set_progress(fraction, pct_text))
            speed = d.get("_speed_str", "").strip()
            self._log(f"Telechargement... {d.get('_percent_str', '').strip()} {speed}")
        elif d["status"] == "finished":
            self.after(0, lambda: self._set_progress(1, "100%"))
            self._log("Telechargement termine, post-traitement en cours...")

    def _start_download(self):
        raw = self.url_text.get("1.0", "end").strip()
        urls = [line.strip() for line in raw.splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning("Lien manquant", "Colle au moins un lien de video ou de playlist.")
            return

        out_dir = self.output_dir.get().strip() or DEFAULT_OUTPUT_DIR
        os.makedirs(out_dir, exist_ok=True)

        self.download_btn.configure(state="disabled", text="Telechargement...")
        self._set_progress(0, "0%")
        self._log(f"File d'attente : {len(urls)} lien(s)")

        thread = threading.Thread(target=self._run_queue, args=(urls, out_dir), daemon=True)
        thread.start()

    def _run_queue(self, urls, out_dir):
        total = len(urls)
        for index, url in enumerate(urls, start=1):
            self._log(f"[{index}/{total}] Demarrage : {url}")
            self.after(0, lambda: self._set_progress(0, "0%"))
            self._run_download(url, out_dir)
        self._log(f"File d'attente terminee ({total} lien(s)).")
        self.after(0, lambda: self.download_btn.configure(state="normal", text="⬇  Telecharger"))

    def _run_download(self, url, out_dir):
        chosen_format = FORMAT_OPTIONS[self.format_var.get()]

        ydl_opts = {
            "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
            "noplaylist": not self.playlist_var.get(),
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": True,
            "format": chosen_format["format"],
        }
        if "postprocessors" in chosen_format:
            ydl_opts["postprocessors"] = chosen_format["postprocessors"]
        if self.subtitles_var.get():
            ydl_opts["writesubtitles"] = True
            ydl_opts["writeautomaticsub"] = True
            ydl_opts["subtitleslangs"] = ["fr", "en"]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self._log("Termine avec succes.")
        except Exception as exc:
            self._log(f"Erreur sur {url} : {exc}")


def main():
    app = DownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
