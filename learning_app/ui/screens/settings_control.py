import flet as ft

from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.preferences import get_shared_preferences
from learning_app.ui.routable_screen import RoutableScreenMixin


class BackgroundShadeSlider(ft.Column):
    """Slider that maps shade index 1–4 to light or dark page backgrounds.

    Updates ``AppTheme`` in memory, applies bgcolor to the page, and persists
    the active mode's slider and color keys.
    """

    DARK_THEME_COLORS = [
        "#000000",   # 1 — AMOLED
        "#0F0F0F",   # 2
        "#171717",   # 3
        "#1F1F1F",   # 4
    ]

    LIGHT_THEME_COLORS = [
        ft.Colors.WHITE,
        ft.Colors.SURFACE,
        ft.Colors.BLUE_GREY_50,
        ft.Colors.BLUE_50,
    ]

    def __init__(self, label: str, initial_value: int, width: float):
        super().__init__()
        self.width = width
        initial_value = int(initial_value)
        max_value = len(self.DARK_THEME_COLORS)
        self.label = ft.Text(label)
        self.slider = ft.Slider(
            min=1,
            max=max_value,
            divisions=max_value - 1,
            value=initial_value,
            on_change=self.on_slider_change,
        )
        self.controls = [self.label, self.slider]

    def apply_layout(self, width: float):
        self.width = width

    def on_slider_change(self, e):
        value = int(e.control.value)
        AppTheme.set_slider_value(AppTheme.theme_mode, value)
        if AppTheme.theme_mode == ft.ThemeMode.DARK:
            color = self.DARK_THEME_COLORS[value - 1]
        else:
            color = self.LIGHT_THEME_COLORS[value - 1]

        AppTheme.set_bgcolor(AppTheme.theme_mode, color)

        AppTheme.apply_to_page(self.page)
        self.page.run_task(
            self._save_slider_settings,
            AppTheme.theme_mode.value,
            value,
            color,
        )

        self.page.update()

    async def _save_slider_settings(self, theme_mode_value, value, color):
        await AppTheme.save_slider_settings(theme_mode_value, value, color)

    def update_slider_position(self):
        self.slider.value = AppTheme.get_slider_value()
        self.slider.update()

    def did_mount(self):
        self.update_slider_position()


class SettingsControl(RoutableScreenMixin, ft.Column):
    """Settings shell screen for theme mode and background shade.

    Owns the light/dark switch and ``BackgroundShadeSlider``. Persistence goes
    through preferences and ``AppTheme``; Shell chrome colors stay in ``app.py``.
    """

    def __init__(self, page):
        super().__init__()
        self.expand = True
        self.alignment = ft.MainAxisAlignment.CENTER
        self.spacing = 60
        self._app_page = page
        self._content_width = 300

        self.theme_switch = ft.Switch(
            label="Light theme",
            label_text_style=ft.TextStyle(size=16),
            value=AppTheme.theme_mode == ft.ThemeMode.LIGHT,
            on_change=self.on_theme_change,
        )

        initial_value = AppTheme.get_slider_value()

        self.background_shade_slider = BackgroundShadeSlider(
            label="Background Shade",
            initial_value=initial_value,
            width=self._content_width,
        )

        self.theme_switch_row = ft.Row(
            [self.theme_switch],
            alignment=ft.MainAxisAlignment.START,
        )

        self.controls = [
            self.theme_switch_row,
            self.background_shade_slider,
        ]

    def _get_page(self):
        if control_is_on_page(self):
            return self.page
        return self._app_page

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        metrics = self.resolve_layout_metrics(metrics)

        self._content_width = metrics.settings_width
        self.theme_switch_row.width = metrics.settings_width
        self.background_shade_slider.apply_layout(metrics.settings_width)

        self.update_if_mounted()

    def on_theme_change(self, e):
        page = self._get_page()
        if e.control.value:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_mode_value = ft.ThemeMode.LIGHT.value
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_mode_value = ft.ThemeMode.DARK.value

        page.run_task(self._save_theme_mode, theme_mode_value)
        AppTheme.sync_from_page(page)
        AppTheme.apply_to_page(page)
        page.update()
        self.background_shade_slider.update_slider_position()

    async def _save_theme_mode(self, theme_mode_value):
        await get_shared_preferences().set("theme_mode", theme_mode_value)

    def did_mount(self):
        AppTheme.apply_to_page(self._get_page())
        super().did_mount()
        self.background_shade_slider.update_slider_position()


