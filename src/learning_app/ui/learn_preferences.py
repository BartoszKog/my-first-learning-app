"""Process-wide learn-session flags backed by preferences."""

from learning_app.ui.preferences import get_shared_preferences

RETRY_UNTIL_CORRECT_KEY = "learn_retry_until_correct"
WORD_FORMATIONS_QUEUE_SIZE_KEY = "learn_word_formations_queue_size"
DEFINITIONS_QUEUE_SIZE_KEY = "learn_definitions_queue_size"
EXAMPLE_MODE_KEY = "learn_example_mode"

EXAMPLE_MODE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("off", "Off"),
    ("after_check", "After Check"),
    ("hint", "Hint (before answer)"),
)
"""Stored example mode and its dropdown label."""


class LearnPreferences:
    """Runtime learn settings loaded at startup and edited from Settings.

    Attributes:
        retry_until_correct: When ``True``, a wrong Check requires a correct
            retype before the queue advances. Extra attempts do not change
            set statistics.
        word_formations_queue_size: Max items ``draw_index_group`` draws for
            a word-formation set (``kind == "words"``).
        definitions_queue_size: Max items ``draw_index_group`` draws for a
            definitions set (``kind == "definitions"``).
        example_mode: When a definition card shows its example sentence.
            ``"off"`` hides it, ``"after_check"`` shows it after Check, and
            ``"hint"`` shows it with blank gaps before Check.
    """

    RETRY_UNTIL_CORRECT_DEFAULT = True
    WORD_FORMATIONS_QUEUE_MIN = 3
    WORD_FORMATIONS_QUEUE_MAX = 10
    WORD_FORMATIONS_QUEUE_DEFAULT = 5
    DEFINITIONS_QUEUE_MIN = 4
    DEFINITIONS_QUEUE_MAX = 15
    DEFINITIONS_QUEUE_DEFAULT = 10
    EXAMPLE_MODES = ("off", "after_check", "hint")
    EXAMPLE_MODE_DEFAULT = "hint"

    retry_until_correct: bool = RETRY_UNTIL_CORRECT_DEFAULT
    word_formations_queue_size: int = WORD_FORMATIONS_QUEUE_DEFAULT
    definitions_queue_size: int = DEFINITIONS_QUEUE_DEFAULT
    example_mode: str = EXAMPLE_MODE_DEFAULT

    @classmethod
    def parse_example_mode(cls, raw: object) -> str:
        """Parse a stored example mode; missing or unknown means Hint."""
        if raw is None:
            return cls.EXAMPLE_MODE_DEFAULT
        text = str(raw).strip().lower()
        return text if text in cls.EXAMPLE_MODES else cls.EXAMPLE_MODE_DEFAULT

    @classmethod
    def parse_retry_until_correct(cls, raw: object) -> bool:
        """Parse a stored retry flag; missing or unknown means on."""
        if raw is None:
            return True
        text = str(raw).strip().lower()
        return text not in {"false", "0", "off", "no"}

    @classmethod
    def parse_word_formations_queue_size(cls, raw: object) -> int:
        """Parse a word-formation queue size; missing or unparseable means 5."""
        return cls._parse_queue_size(
            raw,
            default=cls.WORD_FORMATIONS_QUEUE_DEFAULT,
            minimum=cls.WORD_FORMATIONS_QUEUE_MIN,
            maximum=cls.WORD_FORMATIONS_QUEUE_MAX,
        )

    @classmethod
    def parse_definitions_queue_size(cls, raw: object) -> int:
        """Parse a definitions queue size; missing or unparseable means 10."""
        return cls._parse_queue_size(
            raw,
            default=cls.DEFINITIONS_QUEUE_DEFAULT,
            minimum=cls.DEFINITIONS_QUEUE_MIN,
            maximum=cls.DEFINITIONS_QUEUE_MAX,
        )

    @classmethod
    def _parse_queue_size(
        cls,
        raw: object,
        *,
        default: int,
        minimum: int,
        maximum: int,
    ) -> int:
        """Read a stored integer string, clamp it, or return ``default``."""
        if isinstance(raw, bool) or raw is None:
            return default
        if isinstance(raw, str):
            raw = raw.strip()
            if raw == "":
                return default
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        if value < minimum:
            return minimum
        if value > maximum:
            return maximum
        return value

    @classmethod
    async def load_from_preferences(cls) -> None:
        """Load learn settings from ``SharedPreferences``.

        Missing keys are seeded with retry enabled, the default queue sizes,
        and examples shown as Hint. Unparseable queue sizes become the
        default; values outside the slider range are clamped.
        """
        storage = get_shared_preferences()
        if not await storage.contains_key(RETRY_UNTIL_CORRECT_KEY):
            await storage.set(RETRY_UNTIL_CORRECT_KEY, "true")
        cls.retry_until_correct = cls.parse_retry_until_correct(
            await storage.get(RETRY_UNTIL_CORRECT_KEY)
        )
        cls.word_formations_queue_size = await cls._load_queue_size(
            storage,
            WORD_FORMATIONS_QUEUE_SIZE_KEY,
            parse=cls.parse_word_formations_queue_size,
            default=cls.WORD_FORMATIONS_QUEUE_DEFAULT,
        )
        cls.definitions_queue_size = await cls._load_queue_size(
            storage,
            DEFINITIONS_QUEUE_SIZE_KEY,
            parse=cls.parse_definitions_queue_size,
            default=cls.DEFINITIONS_QUEUE_DEFAULT,
        )
        if not await storage.contains_key(EXAMPLE_MODE_KEY):
            await storage.set(EXAMPLE_MODE_KEY, cls.EXAMPLE_MODE_DEFAULT)
        cls.example_mode = cls.parse_example_mode(await storage.get(EXAMPLE_MODE_KEY))

    @classmethod
    async def _load_queue_size(cls, storage, key: str, *, parse, default: int) -> int:
        if not await storage.contains_key(key):
            await storage.set(key, str(default))
        return parse(await storage.get(key))

    @classmethod
    async def save_retry_until_correct(cls, enabled: bool) -> None:
        """Persist and apply the retry-until-correct switch."""
        cls.retry_until_correct = bool(enabled)
        await get_shared_preferences().set(
            RETRY_UNTIL_CORRECT_KEY,
            "true" if cls.retry_until_correct else "false",
        )

    @classmethod
    async def save_word_formations_queue_size(cls, size: int) -> None:
        """Persist and apply the word-formation practice-queue size."""
        cls.word_formations_queue_size = cls.parse_word_formations_queue_size(size)
        await get_shared_preferences().set(
            WORD_FORMATIONS_QUEUE_SIZE_KEY,
            str(cls.word_formations_queue_size),
        )

    @classmethod
    async def save_definitions_queue_size(cls, size: int) -> None:
        """Persist and apply the definitions practice-queue size."""
        cls.definitions_queue_size = cls.parse_definitions_queue_size(size)
        await get_shared_preferences().set(
            DEFINITIONS_QUEUE_SIZE_KEY,
            str(cls.definitions_queue_size),
        )

    @classmethod
    async def save_example_mode(cls, mode: str) -> None:
        """Persist and apply when definition cards show their example."""
        cls.example_mode = cls.parse_example_mode(mode)
        await get_shared_preferences().set(EXAMPLE_MODE_KEY, cls.example_mode)
