"""Process-wide learn-session flags backed by preferences."""

from learning_app.ui.preferences import get_shared_preferences

RETRY_UNTIL_CORRECT_KEY = "learn_retry_until_correct"


class LearnPreferences:
    """Runtime learn settings loaded at startup and edited from Settings.

    Attributes:
        retry_until_correct: When ``True``, a wrong Check requires a correct
            retype before the queue advances. Extra attempts do not change
            set statistics.
    """

    retry_until_correct: bool = False

    @classmethod
    def parse_retry_until_correct(cls, raw: object) -> bool:
        """Parse a stored retry flag; missing or unknown means off."""
        if raw is None:
            return False
        return str(raw).strip().lower() in {"true", "1", "on", "yes"}

    @classmethod
    async def load_from_preferences(cls) -> None:
        """Load retry-until-correct from ``SharedPreferences``.

        Missing keys are seeded with the flag disabled.
        """
        storage = get_shared_preferences()
        if not await storage.contains_key(RETRY_UNTIL_CORRECT_KEY):
            await storage.set(RETRY_UNTIL_CORRECT_KEY, "false")
        cls.retry_until_correct = cls.parse_retry_until_correct(
            await storage.get(RETRY_UNTIL_CORRECT_KEY)
        )

    @classmethod
    async def save_retry_until_correct(cls, enabled: bool) -> None:
        """Persist and apply the retry-until-correct switch."""
        cls.retry_until_correct = bool(enabled)
        await get_shared_preferences().set(
            RETRY_UNTIL_CORRECT_KEY,
            "true" if cls.retry_until_correct else "false",
        )
