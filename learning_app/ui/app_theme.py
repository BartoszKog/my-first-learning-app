import flet as ft
from flet import ThemeMode

from learning_app.ui.preferences import get_shared_preferences


class AppTheme:
    theme_mode: ThemeMode | None = None
    dark_theme_slider_value = 2
    light_theme_slider_value = 2
    dark_theme_bgcolor = None
    light_theme_bgcolor = None

    @classmethod
    def is_dark_mode(cls) -> bool:
        return cls.theme_mode == ThemeMode.DARK

    @classmethod
    def sync_from_page(cls, page: ft.Page):
        cls.theme_mode = page.theme_mode

    @classmethod
    def set_slider_value(cls, theme_mode: ThemeMode, value):
        value = int(value)
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_slider_value = value
        else:
            cls.light_theme_slider_value = value

    @classmethod
    def get_slider_value(cls, theme_mode=""):
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
        normalized = cls._normalize_color(color)
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_bgcolor = normalized
        else:
            cls.light_theme_bgcolor = normalized

    @classmethod
    def resolve_bgcolor(cls):
        bgcolor = cls.get_bgcolor()
        if bgcolor is not None:
            return bgcolor
        return ft.Colors.SURFACE.value

    @classmethod
    def apply_bgcolor(cls, page: ft.Page, bgcolor):
        normalized = cls._normalize_color(bgcolor)
        page.bgcolor = normalized
        for view in page.views:
            view.bgcolor = normalized

    @classmethod
    def apply_to_page(cls, page: ft.Page):
        cls.apply_bgcolor(page, cls.resolve_bgcolor())

    @classmethod
    def current_bgcolor(cls):
        return cls.resolve_bgcolor()

    @classmethod
    async def save_slider_settings(cls, theme_mode_value: str, value: int, color):
        storage = get_shared_preferences()
        await storage.set(f"{theme_mode_value}_theme_slider_value", str(value))
        await storage.set(f"{theme_mode_value}_theme_bgcolor", cls._normalize_color(color))

    @classmethod
    def get_bgcolor(cls, theme_mode=""):
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
        storage = get_shared_preferences()
        cls.dark_theme_slider_value = int(await storage.get("dark_theme_slider_value"))
        cls.light_theme_slider_value = int(await storage.get("light_theme_slider_value"))
        cls.dark_theme_bgcolor = await storage.get("dark_theme_bgcolor")
        cls.light_theme_bgcolor = await storage.get("light_theme_bgcolor")
