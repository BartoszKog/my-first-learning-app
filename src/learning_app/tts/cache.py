"""Content-addressed MP3 cache for generated pronunciation audio."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from learning_app.data.file_path_manager import FilePathManager
from learning_app.tts.texts import normalize_text

_SIDECAR_ENCODING = "utf-8"


class TtsCache:
    """Store MP3 files keyed by provider, voice, language, and text.

    Files live under ``FilePathManager.get_tts_cache_dir()``. Each object is
    ``<hash[:2]>/<hash>.mp3`` plus a JSON sidecar used by garbage collection
    so recordings stay as long as the phrase still exists in any set.
    """

    def __init__(self, root: Path | str | None = None):
        """Create a cache rooted at ``root`` or the app TTS directory.

        Args:
            root: Cache directory. ``None`` uses ``get_tts_cache_dir()``.
        """
        self.root = Path(root) if root is not None else Path(FilePathManager.get_tts_cache_dir())
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(provider: str, language: str, text: str, voice: str = "") -> str:
        """Return a hex digest for the cache object.

        Args:
            provider: Provider id such as ``gtts``.
            language: IETF language tag.
            text: Phrase to speak (will be normalized).
            voice: Optional voice id; empty for providers without voices.

        Returns:
            SHA-256 hex digest used as the filename stem.
        """
        normalized = normalize_text(text)
        payload = "\0".join((provider, voice, language, normalized)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def get_path(self, key: str) -> Path | None:
        """Return the MP3 path when a non-empty file and sidecar exist.

        Args:
            key: Digest from ``make_key``.

        Returns:
            Path to the MP3, or ``None`` on a cache miss or empty file.
        """
        mp3_path = self._mp3_path(key)
        if (
            mp3_path.is_file()
            and mp3_path.stat().st_size > 0
            and self._sidecar_path(key).is_file()
        ):
            return mp3_path
        return None

    def put(
        self,
        key: str,
        data: bytes,
        *,
        text: str,
        language: str,
        provider: str,
        voice: str = "",
    ) -> Path:
        """Write MP3 bytes and a sidecar describing the phrase.

        Args:
            key: Digest from ``make_key``.
            data: MP3 bytes.
            text: Normalized phrase stored for garbage collection.
            language: IETF language tag.
            provider: Provider id that produced ``data``.
            voice: Optional voice id.

        Returns:
            Path to the written MP3.

        Raises:
            ValueError: If ``data`` is empty.
        """
        if not data:
            raise ValueError("Cannot cache empty audio.")

        mp3_path = self._mp3_path(key)
        mp3_path.parent.mkdir(parents=True, exist_ok=True)
        mp3_path.write_bytes(data)
        sidecar = {
            "text": normalize_text(text),
            "language": language,
            "provider": provider,
            "voice": voice,
        }
        self._sidecar_path(key).write_text(
            json.dumps(sidecar, ensure_ascii=False),
            encoding=_SIDECAR_ENCODING,
        )
        return mp3_path

    def garbage_collect(self, live_texts: Iterable[str]) -> int:
        """Delete recordings whose phrase is no longer in ``live_texts``.

        Language and provider are ignored: if the phrase still exists in any
        set, every cached rendering of it is kept.

        Args:
            live_texts: Phrases still present in learning sets.

        Returns:
            Number of MP3 files removed.
        """
        live = {normalize_text(text) for text in live_texts}
        live.discard("")
        removed = 0

        for sidecar_path in self.root.rglob("*.json"):
            mp3_path = sidecar_path.with_suffix(".mp3")
            text = self._text_from_sidecar(sidecar_path)
            if text is not None and text in live:
                continue
            if mp3_path.is_file():
                mp3_path.unlink()
                removed += 1
            sidecar_path.unlink(missing_ok=True)

        for mp3_path in self.root.rglob("*.mp3"):
            if not mp3_path.with_suffix(".json").is_file():
                mp3_path.unlink()
                removed += 1

        return removed

    def _mp3_path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.mp3"

    def _sidecar_path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    @staticmethod
    def _text_from_sidecar(path: Path) -> str | None:
        try:
            payload = json.loads(path.read_text(encoding=_SIDECAR_ENCODING))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str):
            return None
        return normalize_text(text)
