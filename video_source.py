"""
Descarga de videos desde enlaces (YouTube, Shorts, etc.) con yt-dlp
"""
import logging
import os
import tempfile
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

MAX_FILESIZE_MB = 100
MAX_DURATION_SECONDS = 600


def is_valid_url(url: str) -> bool:
    """Verifica que el texto sea una URL http(s) con host."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def download_video(url: str, output_dir: Optional[str] = None) -> str:
    """
    Descarga un video desde un enlace (p. ej. YouTube Shorts) como MP4.

    Args:
        url: Enlace al video
        output_dir: Carpeta de destino (si None, se crea una temporal)

    Returns:
        Ruta al archivo MP4 descargado

    Raises:
        ValueError: Si la URL no es válida o el video excede los límites
        RuntimeError: Si la descarga falla
    """
    url = url.strip()
    if not is_valid_url(url):
        raise ValueError("El enlace no es una URL válida (debe iniciar con http:// o https://)")

    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import DownloadError
    except ImportError as e:
        raise RuntimeError("Falta la dependencia 'yt-dlp' (pip install yt-dlp)") from e

    output_dir = output_dir or tempfile.mkdtemp(prefix="ciclistas_")
    options = {
        # Máx. 720p en MP4: suficiente para detección y liviano de procesar
        "format": "best[height<=720][ext=mp4]/best[height<=720]/best",
        "outtmpl": os.path.join(output_dir, "video_descargado.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "max_filesize": MAX_FILESIZE_MB * 1024 * 1024,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get("duration") or 0
            if duration > MAX_DURATION_SECONDS:
                raise ValueError(
                    f"El video dura {duration // 60} min; el máximo permitido es "
                    f"{MAX_DURATION_SECONDS // 60} min"
                )
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
    except DownloadError as e:
        raise RuntimeError(f"No se pudo descargar el video: {e}") from e

    if not os.path.exists(path) or os.path.getsize(path) == 0:
        raise RuntimeError(
            f"La descarga no produjo un archivo (¿supera {MAX_FILESIZE_MB} MB?)"
        )

    logger.info(f"✅ Video descargado: {path}")
    return path
