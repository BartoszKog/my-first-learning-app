"""Process-wide TTS language and auto-speak flags backed by preferences."""

from learning_app.ui.preferences import get_shared_preferences

LANGUAGE_KEY = "tts_language"
AUTO_SPEAK_DEFINITIONS_KEY = "tts_auto_speak_definitions"
DEFAULT_LANGUAGE = "en"

TTS_LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("pl", "Polish"),
    ("ru", "Russian"),
    ("ja", "Japanese"),
    ("zh-CN", "Chinese"),
)
LANGUAGE_CODES = frozenset(code for code, _label in TTS_LANGUAGES)


class TtsPreferences:
    """Runtime TTS settings loaded at startup and edited from Settings.

    Attributes:
        language: gTTS language code used by ``AppSession.speak``.
        auto_speak_definitions: When ``True``, definitions Check auto-plays
            the word without error snackbars.
    """

    language: str = DEFAULT_LANGUAGE
    auto_speak_definitions: bool = True

    @classmethod
    def normalize_language(cls, language: object) -> str:
        """Return a supported language code, or English when unknown."""
        if isinstance(language, str) and language in LANGUAGE_CODES:
            return language
        return DEFAULT_LANGUAGE

    @classmethod
    def parse_auto_speak(cls, raw: object) -> bool:
        """Parse a stored auto-speak value; missing or unknown means on."""
        if raw is None:
            return True
        return str(raw).strip().lower() not in {"false", "0", "off", "no"}

    @classmethod
    async def load_from_preferences(cls) -> None:
        """Load language and auto-speak from ``SharedPreferences``.

        Missing keys are seeded with English and auto-speak enabled.
        """
        storage = get_shared_preferences()
        if not await storage.contains_key(LANGUAGE_KEY):
            await storage.set(LANGUAGE_KEY, DEFAULT_LANGUAGE)
        if not await storage.contains_key(AUTO_SPEAK_DEFINITIONS_KEY):
            await storage.set(AUTO_SPEAK_DEFINITIONS_KEY, "true")
        cls.language = cls.normalize_language(await storage.get(LANGUAGE_KEY))
        cls.auto_speak_definitions = cls.parse_auto_speak(
            await storage.get(AUTO_SPEAK_DEFINITIONS_KEY)
        )

    @classmethod
    async def save_language(cls, language: str) -> None:
        """Persist and apply a language code."""
        cls.language = cls.normalize_language(language)
        await get_shared_preferences().set(LANGUAGE_KEY, cls.language)

    @classmethod
    async def save_auto_speak_definitions(cls, enabled: bool) -> None:
        """Persist and apply the definitions auto-speak switch."""
        cls.auto_speak_definitions = bool(enabled)
        await get_shared_preferences().set(
            AUTO_SPEAK_DEFINITIONS_KEY,
            "true" if cls.auto_speak_definitions else "false",
        )
