import flet as ft

from learning_app.ui.page_functions import set_theme_from_bgcolor
from learning_app.ui.page_properties import PageProperties
from learning_app.ui.preferences import get_shared_preferences


class BackgroundShadeSlider(ft.Column):
    DARK_THEME_COLORS = [
        ft.Colors.BLACK,
        ft.Colors.SURFACE,
        ft.Colors.WHITE_10,
        ft.Colors.GREY_900,
    ]

    LIGHT_THEME_COLORS = [
        ft.Colors.WHITE,
        ft.Colors.SURFACE,
        ft.Colors.BLUE_GREY_50,
        ft.Colors.BLUE_50,
    ]

    def __init__(self, label: str, initial_value: int):
        super().__init__()
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

    def on_slider_change(self, e):
        value = int(e.control.value)
        PageProperties.set_slider_value(PageProperties.theme_mode, value)
        if PageProperties.theme_mode == ft.ThemeMode.DARK:
            color = self.DARK_THEME_COLORS[value - 1]
        else:
            color = self.LIGHT_THEME_COLORS[value - 1]
        PageProperties.set_bgcolor(PageProperties.theme_mode, color)
        set_theme_from_bgcolor(self.page, color)
        self.page.run_task(
            self._save_slider_settings,
            PageProperties.theme_mode.value,
            value,
            color,
        )
        self.page.update()

    async def _save_slider_settings(self, theme_mode_value, value, color):
        storage = get_shared_preferences()
        await storage.set(f"{theme_mode_value}_theme_slider_value", value)
        await storage.set(f"{theme_mode_value}_theme_bgcolor", color.value)

    def update_slider_position(self):
        self.slider.value = PageProperties.get_slider_value()
        self.slider.update()

    def did_mount(self):
        self.update_slider_position()


class SettingsControl(ft.Column):
    # BUTTON_HEIGHT = 60
    # FONT_SIZE_BUTTON = 15
    def __init__(self, page):
        super().__init__()
        self.spacing = 60

        self._app_page = page
        self.drawer = PageProperties.get_drawer()

        # menu button
        self.menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=self.on_menu_click,
            icon_color=ft.Colors.WHITE,
        )

        # theme switch
        self.theme_switch = ft.Switch(
            label="Light theme",
            label_text_style=ft.TextStyle(size=16),
            value=PageProperties.theme_mode == ft.ThemeMode.LIGHT,
            on_change=self.on_theme_change,
        )

        # background shade slider
        initial_value = PageProperties.get_slider_value()
        self.background_shade_slider = BackgroundShadeSlider(
            label="Background Shade",
            initial_value=initial_value,
        )

        # Add elements in column to container
        self.controls = [
            ft.Row(
                [self.theme_switch],
                alignment=ft.MainAxisAlignment.START,
                width=PageProperties.width * 0.7,
            ),
            self.background_shade_slider,
        ]

        self.__update_controls_width()

    def _get_page(self):
        return self.page or self._app_page

    def __update_controls_width(self):
        width = PageProperties.width * 0.7
        for control in self.controls:
            control.width = width
        self.theme_switch.width = None

    async def on_menu_click(self, e):
        await self._get_page().show_drawer()

    def on_theme_change(self, e):
        page = self._get_page()
        if e.control.value:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_mode_value = ft.ThemeMode.LIGHT.value
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_mode_value = ft.ThemeMode.DARK.value

        page.run_task(self._save_theme_mode, theme_mode_value)
        PageProperties.set_theme_from_page(page)
        bgcolor = PageProperties.get_bgcolor()
        set_theme_from_bgcolor(page, bgcolor)
        page.update()
        self.background_shade_slider.update_slider_position()

    async def _save_theme_mode(self, theme_mode_value):
        await get_shared_preferences().set("theme_mode", theme_mode_value)

    def did_mount(self):
        page = self._get_page()
        appbar = page.appbar
        appbar.leading = self.menu_button
        appbar.title.value = "Settings"

        page.bottom_appbar.visible = False
        page.floating_action_button.visible = False
        page.update()

    def will_unmount(self):
        page = self._get_page()
        self.__update_controls_width()
        appbar = page.appbar
        appbar.leading = None
        page.update()
