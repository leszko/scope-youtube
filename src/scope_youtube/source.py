"""YouTube input source.

Downloads a YouTube video to a local cache via yt-dlp, then reuses the
built-in ``VideoFileInputSource`` to decode and loop frames.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import ClassVar

import numpy as np

from scope.core.inputs.interface import InputSource, InputSourceInfo
from scope.core.inputs.video_file import VideoFileInputSource

logger = logging.getLogger(__name__)

# Single-file selectors only — no `+` merge step, so ffmpeg isn't required.
# The InputSource interface only exposes video frames, so we don't need audio;
# pulling a video-only stream gives us up to 1080p without any muxing.
_YTDLP_FORMAT = (
    "bv*[ext=mp4][height<=1080]"
    "/bv*[height<=1080]"
    "/b[ext=mp4][height<=1080]"
    "/best[height<=1080]"
)

# Only accept URLs on these hosts. Guards against yt-dlp's generic extractor
# being abused as an SSRF oracle.
_ALLOWED_HOSTS = re.compile(
    r"^(?:https?://)?(?:www\.|m\.)?(?:youtube\.com|youtu\.be)(?:/|$)",
    re.IGNORECASE,
)

_VIDEO_ID_PATTERN = re.compile(
    r"(?:v=|/shorts/|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})(?:[?&/]|$)"
)

# Per-video-id lock so concurrent connects don't double-download the same file.
_download_locks_guard = threading.Lock()
_download_locks: dict[str, threading.Lock] = {}


def _extract_video_id(url: str) -> str | None:
    if not isinstance(url, str) or not url.strip():
        return None
    url = url.strip()
    if not _ALLOWED_HOSTS.search(url):
        return None
    m = _VIDEO_ID_PATTERN.search(url)
    return m.group(1) if m else None


def _get_cache_path(video_id: str) -> Path:
    """Return a cache file path, preferring Scope's asset cache dir."""
    try:
        from scope.server.models_config import get_assets_dir

        cache_dir = get_assets_dir().parent / "cache" / "youtube"
    except Exception:
        cache_dir = (
            Path(
                os.environ.get("DAYDREAM_SCOPE_HOME")
                or (Path.home() / ".daydream-scope")
            )
            / "cache"
            / "youtube"
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{video_id}.mp4"


def _get_download_lock(video_id: str) -> threading.Lock:
    with _download_locks_guard:
        lock = _download_locks.get(video_id)
        if lock is None:
            lock = threading.Lock()
            _download_locks[video_id] = lock
        return lock


def _download(url: str, cache_path: Path) -> bool:
    """Download ``url`` to ``cache_path``. Returns True on success.

    Retries once on HTTP 429 after a 5s backoff.
    """
    try:
        import yt_dlp
    except ImportError:
        logger.error("yt-dlp is not installed; install it to use YouTube sources")
        return False

    ydl_opts = {
        "format": _YTDLP_FORMAT,
        "outtmpl": str(cache_path),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
    }

    def _run() -> tuple[bool, str]:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True, ""
        except yt_dlp.utils.DownloadError as e:
            return False, str(e)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    ok, err = _run()
    if not ok and ("429" in err.lower() or "too many requests" in err.lower()):
        logger.warning(f"YouTube rate-limited; retrying after 5s: {err}")
        time.sleep(5.0)
        ok, err = _run()

    if not ok:
        logger.error(f"YouTube download failed: {err}")
        return False

    if not cache_path.exists() or cache_path.stat().st_size == 0:
        logger.error(
            f"YouTube download reported success but file missing: {cache_path}"
        )
        return False

    logger.info(
        f"YouTube download complete: {cache_path.name} "
        f"({cache_path.stat().st_size // 1024} KB)"
    )
    return True


class YouTubeInputSource(InputSource):
    """Input source that downloads a YouTube video and plays it on loop."""

    source_id: ClassVar[str] = "youtube"
    source_name: ClassVar[str] = "YouTube"
    source_description: ClassVar[str] = (
        "Paste a YouTube URL (e.g. https://www.youtube.com/watch?v=...) "
        "to download the video and play it on loop."
    )

    def __init__(self):
        self._inner: VideoFileInputSource | None = None

    @classmethod
    def is_available(cls) -> bool:
        try:
            import av  # noqa: F401
            import yt_dlp  # noqa: F401

            return True
        except ImportError:
            return False

    def list_sources(self, timeout_ms: int = 5000) -> list[InputSourceInfo]:
        # YouTube can't be enumerated; the URL is the identifier.
        return []

    def connect(self, identifier: str) -> bool:
        self.disconnect()

        video_id = _extract_video_id(identifier)
        if video_id is None:
            logger.error(f"Invalid YouTube URL: {identifier!r}")
            return False

        cache_path = _get_cache_path(video_id)

        with _get_download_lock(video_id):
            if not cache_path.exists() or cache_path.stat().st_size == 0:
                if not _download(identifier, cache_path):
                    return False

            inner = VideoFileInputSource()
            if inner.connect(str(cache_path)):
                self._inner = inner
                logger.info(
                    f"YouTubeInputSource connected: {identifier} (cache={cache_path.name})"
                )
                return True

            # Cache may be corrupted — re-download once and retry.
            logger.warning(
                f"Cached file failed to open ({cache_path.name}), redownloading"
            )
            try:
                cache_path.unlink(missing_ok=True)
            except OSError as e:
                logger.error(f"Could not delete cached {cache_path}: {e}")
                return False
            if not _download(identifier, cache_path):
                return False
            inner = VideoFileInputSource()
            if inner.connect(str(cache_path)):
                self._inner = inner
                return True
            logger.error(f"Failed to open YouTube video after redownload: {identifier}")
            return False

    def receive_frame(self, timeout_ms: int = 100) -> np.ndarray | None:
        if self._inner is None:
            return None
        return self._inner.receive_frame(timeout_ms=timeout_ms)

    def disconnect(self):
        if self._inner is not None:
            try:
                self._inner.close()
            except Exception as e:
                logger.error(f"Error closing inner video source: {e}")
            finally:
                self._inner = None
