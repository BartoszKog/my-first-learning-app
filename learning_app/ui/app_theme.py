"""Runtime theme mode and page background shade backed by preferences."""

import flet as ft
from flet import ThemeMode

from learning_app.ui.preferences import get_shared_preferences


class AppTheme:
    """Process-wide theme mode and content background colors.

    Settings updates these class attributes and persists keys through
    ``SharedPreferences``. Startup loads them before the first route so the
    first frame matches saved preferences. Shell chrome colors in ``app.py``
    are separate and are not stored here.

    Attributes:
        theme_mode: Current ``ThemeMode``, synced from ``page.theme_mode``.
        dark_theme_slider_value: Shade index (1–4) for dark mode.
        light_theme_slider_value: Shade index (1–4) for light mode.
        dark_theme_bgcolor: Resolved dark page/view background color.
        light_theme_bgcolor: Resolved light page/view background color.
    """

    theme_mode: ThemeMode | None = None
    dark_theme_slider_value = 2
    light_theme_slider_value = 2
    dark_theme_bgcolor = None
    light_theme_bgcolor = None

    @classmethod
    def is_dark_mode(cls) -> bool:
        """Return whether the active theme mode is dark."""
        return cls.theme_mode == ThemeMode.DARK

    @classmethod
    def sync_from_page(cls, page: ft.Page):
        """Copy ``page.theme_mode`` into ``theme_mode``.

        Args:
            page: Application page whose theme mode is authoritative.
        """
        cls.theme_mode = page.theme_mode

    @classmethod
    def set_slider_value(cls, theme_mode: ThemeMode, value):
        """Store the shade slider index for one theme mode.

        Args:
            theme_mode: Light or dark mode the value belongs to.
            value: Slider position (typically 1–4).
        """
        value = int(value)
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_slider_value = value
        else:
            cls.light_theme_slider_value = value

    @classmethod
    def get_slider_value(cls, theme_mode=""):
        """Return the shade slider index for a mode or the active mode.

        Args:
            theme_mode: ``ThemeMode.DARK``, ``ThemeMode.LIGHT``, or ``""``
                for the current ``theme_mode``.

        Returns:
            Integer slider value for that mode.
        """
        if theme_mode == ThemeMode.DARK:
            return cls.dark_theme_slider_value
        if theme_mode == "":
            return (
                cls.light_theme_slider_value
                if cls.theme_mode == ThemeMode.LIGHT
                else cls.dark_theme_slider_value
            )
        return cls.light_theme_slider_value

    @classmethod
    def _normalize_color(cls, color):
        return color.value if hasattr(color, "value") else color

    @classmethod
    def set_bgcolor(cls, theme_mode: ThemeMode, color):
        """Store the content background color for one theme mode.

        Args:
            theme_mode: Light or dark mode the color belongs to.
            color: Flet color enum or string value.
        """
        normalized = cls._normalize_color(color)
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_bgcolor = normalized
        else:
            cls.light_theme_bgcolor = normalized

    @classmethod
    def resolve_bgcolor(cls):
        """Return the active mode bgcolor, or ``SURFACE`` if unset.

        Returns:
            Normalized color string for page and view backgrounds.
        """
        bgcolor = cls.get_bgcolor()
        if bgcolor is not None:
            return bgcolor
        return ft.Colors.SURFACE.value

    @classmethod
    def apply_bgcolor(cls, page: ft.Page, bgcolor):
        """Set ``page.bgcolor`` and every stacked view's bgcolor.

        Args:
            page: Application page.
            bgcolor: Color to apply (enum or string).
        """
        normalized = cls._normalize_color(bgcolor)
        page.bgcolor = normalized
        for view in page.views:
            view.bgcolor = normalized

    @classmethod
    def apply_to_page(cls, page: ft.Page):
        """Apply the resolved current bgcolor to the page and views.

        Args:
            page: Application page.
        """
        cls.apply_bgcolor(page, cls.resolve_bgcolor())

    @classmethod
    def current_bgcolor(cls):
        """Return the bgcolor currently used for new views and layouts."""
        return cls.resolve_bgcolor()

    @classmethod
    async def save_slider_settings(cls, theme_mode_value: str, value: int, color):
        """Persist slider index and bgcolor for one theme mode string.

        Writes ``{mode}_theme_slider_value`` and ``{mode}_theme_bgcolor``.

        Args:
            theme_mode_value: ``ThemeMode`` ``.value`` (``"dark"`` / ``"light"``).
            value: Slider index to store.
            color: Background color to store.
        """
        storage = get_shared_preferences()
        await storage.set(f"{theme_mode_value}_theme_slider_value", str(value))
        await storage.set(f"{theme_mode_value}_theme_bgcolor", cls._normalize_color(color))

    @classmethod
    def get_bgcolor(cls, theme_mode=""):
        """Return the stored bgcolor for a mode or the active mode.

        Args:
            theme_mode: ``ThemeMode.DARK``, ``ThemeMode.LIGHT``, or ``""``
                for the current ``theme_mode``.

        Returns:
            Stored color value, or ``None`` if not set.
        """
        if theme_mode == ThemeMode.DARK:
            return cls.dark_theme_bgcolor
        if theme_mode == "":
            return (
                cls.light_theme_bgcolor
                if cls.theme_mode == ThemeMode.LIGHT
                else cls.dark_theme_bgcolor
            )
        return cls.light_theme_bgcolor

    @classmethod
    async def load_from_preferences(cls):
        """Load light/dark slider values and bgcolors from preferences.

        Does not set ``theme_mode``; call ``sync_from_page`` after the page
        theme mode is restored at startup.
        """
        storage = get_shared_preferences()
        cls.dark_theme_slider_value = int(await storage.get("dark_theme_slider_value"))
        cls.light_theme_slider_value = int(await storage.get("light_theme_slider_value"))
        cls.dark_theme_bgcolor = await storage.get("dark_theme_bgcolor")
        cls.light_theme_bgcolor = await storage.get("light_theme_bgcolor")
