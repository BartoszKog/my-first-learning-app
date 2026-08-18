"""Orchestrate TTS cache lookup, synthesis, and garbage collection."""

from __future__ import annotations

import asyncio
from pathlib import Path

from learning_app.tts.cache import TtsCache
from learning_app.tts.provider import TtsError, TtsProvider
from learning_app.tts.texts import collect_speakable_texts, speakable_phrases


def garbage_collect_tts_cache(cache: TtsCache | None = None) -> int:
    """Remove cached MP3s whose phrases no longer appear in any set CSV.

    Uses the default app TTS directory when ``cache`` is omitted. Safe to call
    after deleting or rewriting set content. Do not call after progress-only
    saves.

    Args:
        cache: Cache to prune. ``None`` uses ``FilePathManager.get_tts_cache_dir()``.

    Returns:
        Number of MP3 files removed.
    """
    store = cache if cache is not None else TtsCache()
    return store.garbage_collect(collect_speakable_texts())


class TtsService:
    """Resolve a phrase to a cached MP3 path, generating it when missing.

    One service instance should be reused for the app session. Playback stays
    outside this class so a later UI layer can feed the path into Flet Audio.
    """

    def __init__(self, provider: TtsProvider, cache: TtsCache | None = None):
        """Bind a provider and optional cache.

        Args:
            provider: Backend used on a cache miss.
            cache: Disk cache. ``None`` uses the default app TTS directory.
        """
        self.provider = provider
        self.cache = cache if cache is not None else TtsCache()
        self._locks: dict[str, asyncio.Lock] = {}
        self._locks_guard = asyncio.Lock()

    async def resolve_path(self, text: str, language: str) -> Path:
        """Return the MP3 path for ``text``, synthesizing on a cache miss.

        Args:
            text: Phrase to speak. Whitespace is normalized.
            language: IETF language tag passed to the provider.

        Returns:
            Path to the MP3 on disk.

        Raises:
            TtsError: ``text`` is empty after normalization, contains more
                than one slash-separated member (use ``resolve_paths``), or
                synthesis fails.
        """
        phrases = speakable_phrases(text)
        if not phrases:
            raise TtsError("Cannot synthesize empty text.")
        if len(phrases) > 1:
            raise TtsError("Slash-separated cells need resolve_paths().")

        normalized = phrases[0]
        key = self.cache.make_key(
            provider=self.provider.name,
            voice=self.provider.voice,
            language=language,
            text=normalized,
        )
        cached = self.cache.get_path(key)
        if cached is not None:
            return cached

        lock = await self._lock_for(key)
        async with lock:
            cached = self.cache.get_path(key)
            if cached is not None:
                return cached
            data = await self.provider.synthesize(normalized, language)
            return self.cache.put(
                key,
                data,
                text=normalized,
                language=language,
                provider=self.provider.name,
                voice=self.provider.voice,
            )

    async def resolve_paths(self, text: str, language: str) -> list[Path]:
        """Return an MP3 path for every slash-separated member of ``text``.

        ``go/goes/went`` yields three cached files so the UI can play each
        form in order. Members share the cache with the same phrase in other
        cells.

        Args:
            text: Cell value, possibly containing ``/``.
            language: IETF language tag passed to the provider.

        Returns:
            Paths in speak order, one per distinct member.

        Raises:
            TtsError: ``text`` has no speakable members, or synthesis fails.
        """
        phrases = speakable_phrases(text)
        if not phrases:
            raise TtsError("Cannot synthesize empty text.")
        return [await self.resolve_path(phrase, language) for phrase in phrases]

    async def get_mp3_bytes(self, text: str, language: str) -> bytes:
        """Return MP3 bytes for ``text``, using the cache when possible.

        Args:
            text: Phrase to speak.
            language: IETF language tag.

        Returns:
            MP3 audio bytes.
        """
        path = await self.resolve_path(text, language)
        return path.read_bytes()

    def garbage_collect(self) -> int:
        """Remove cached audio for phrases that no longer appear in any set.

        Returns:
            Number of MP3 files removed.
        """
        return garbage_collect_tts_cache(self.cache)

    async def _lock_for(self, key: str) -> asyncio.Lock:
        async with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[key] = lock
            return lock
