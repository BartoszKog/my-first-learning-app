"""Text-to-speech backend: providers, disk cache, and synthesis service."""

from learning_app.tts.cache import TtsCache
from learning_app.tts.gtts_provider import GttsProvider
from learning_app.tts.provider import TtsError, TtsNetworkError, TtsProvider
from learning_app.tts.service import TtsService, garbage_collect_tts_cache
from learning_app.tts.texts import collect_speakable_texts, normalize_text, speakable_phrases

__all__ = [
    "GttsProvider",
    "TtsCache",
    "TtsError",
    "TtsNetworkError",
    "TtsProvider",
    "TtsService",
    "collect_speakable_texts",
    "garbage_collect_tts_cache",
    "normalize_text",
    "speakable_phrases",
]
