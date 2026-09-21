"""Process-wide TTS language and auto-speak flags backed by preferences."""

from learning_app.ui.preferences import get_shared_preferences

LANGUAGE_KEY = "tts_language"
AUTO_SPEAK_DEFINITIONS_KEY = "tts_auto_speak_definitions"
SPEAKERS_WORD_FORMATIONS_KEY = "tts_speakers_word_formations"
SPEAKERS_WORD_KEY = "tts_speakers_word"
SPEAKERS_DEFINITION_KEY = "tts_speakers_definition"
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
        speakers_word_formations: When ``True``, word-list cards show speakers
            on verb/person/thing/adjective/adverb fields.
        speakers_word: When ``True``, definition-list cards show a speaker on
            the word field.
        speakers_definition: When ``True``, definition-list cards show a
            speaker on the definition field.
    """

    language: str = DEFAULT_LANGUAGE
    auto_speak_definitions: bool = True
    speakers_word_formations: bool = True
    speakers_word: bool = True
    speakers_definition: bool = False

    @classmethod
    def normalize_language(cls, language: object) -> str:
        """Return a supported language code, or English when unknown."""
        if isinstance(language, str) and language in LANGUAGE_CODES:
            return language
        return DEFAULT_LANGUAGE

    @classmethod
    def parse_auto_speak(cls, raw: object) -> bool:
        """Parse a stored auto-speak value; missing or unknown means on."""
        return cls._parse_bool(raw, default=True)

    @classmethod
    def parse_speakers_word_formations(cls, raw: object) -> bool:
        """Parse word-formation speaker switch; missing or unknown means on."""
        return cls._parse_bool(raw, default=True)

    @classmethod
    def parse_speakers_word(cls, raw: object) -> bool:
        """Parse word-field speaker switch; missing or unknown means on."""
        return cls._parse_bool(raw, default=True)

    @classmethod
    def parse_speakers_definition(cls, raw: object) -> bool:
        """Parse definition-field speaker switch; missing or unknown means off."""
        return cls._parse_bool(raw, default=False)

    @classmethod
    def _parse_bool(cls, raw: object, *, default: bool) -> bool:
        if raw is None:
            return default
        text = str(raw).strip().lower()
        if default:
            return text not in {"false", "0", "off", "no"}
        return text in {"true", "1", "on", "yes"}

    @classmethod
    async def load_from_preferences(cls) -> None:
        """Load language, auto-speak, and list-speaker flags from storage.

        Missing keys are seeded with English, auto-speak on, word-formation
        and word speakers on, and definition speakers off.
        """
        storage = get_shared_preferences()
        if not await storage.contains_key(LANGUAGE_KEY):
            await storage.set(LANGUAGE_KEY, DEFAULT_LANGUAGE)
        if not await storage.contains_key(AUTO_SPEAK_DEFINITIONS_KEY):
            await storage.set(AUTO_SPEAK_DEFINITIONS_KEY, "true")
        if not await storage.contains_key(SPEAKERS_WORD_FORMATIONS_KEY):
            await storage.set(SPEAKERS_WORD_FORMATIONS_KEY, "true")
        if not await storage.contains_key(SPEAKERS_WORD_KEY):
            await storage.set(SPEAKERS_WORD_KEY, "true")
        if not await storage.contains_key(SPEAKERS_DEFINITION_KEY):
            await storage.set(SPEAKERS_DEFINITION_KEY, "false")
        cls.language = cls.normalize_language(await storage.get(LANGUAGE_KEY))
        cls.auto_speak_definitions = cls.parse_auto_speak(
            await storage.get(AUTO_SPEAK_DEFINITIONS_KEY)
        )
        cls.speakers_word_formations = cls.parse_speakers_word_formations(
            await storage.get(SPEAKERS_WORD_FORMATIONS_KEY)
        )
        cls.speakers_word = cls.parse_speakers_word(
            await storage.get(SPEAKERS_WORD_KEY)
        )
        cls.speakers_definition = cls.parse_speakers_definition(
            await storage.get(SPEAKERS_DEFINITION_KEY)
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

    @classmethod
    async def save_speakers_word_formations(cls, enabled: bool) -> None:
        """Persist and apply speakers on word-formation list cards."""
        cls.speakers_word_formations = bool(enabled)
        await get_shared_preferences().set(
            SPEAKERS_WORD_FORMATIONS_KEY,
            "true" if cls.speakers_word_formations else "false",
        )

    @classmethod
    async def save_speakers_word(cls, enabled: bool) -> None:
        """Persist and apply speakers on definition-list word fields."""
        cls.speakers_word = bool(enabled)
        await get_shared_preferences().set(
            SPEAKERS_WORD_KEY,
            "true" if cls.speakers_word else "false",
        )

    @classmethod
    async def save_speakers_definition(cls, enabled: bool) -> None:
        """Persist and apply speakers on definition-list definition fields."""
        cls.speakers_definition = bool(enabled)
        await get_shared_preferences().set(
            SPEAKERS_DEFINITION_KEY,
            "true" if cls.speakers_definition else "false",
        )
