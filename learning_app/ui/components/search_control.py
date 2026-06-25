import flet as ft

from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.navigation import go_back_from_search


class SearchControl(ft.Row):
    COLOR = ft.Colors.CYAN

    def __init__(self, page, tiles_container: TilesContainer):
        super().__init__()
        self._app_page = page
        self.tiles_container = tiles_container

        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.tight = True
        self.search_field = ft.TextField(
            label="Search",
            expand=True,
            autofocus=True,
            on_change=self.change_text_field,
            border_color=self.COLOR,
        )

        self.next_pattern_button = ft.IconButton(
            icon=ft.Icons.ARROW_CIRCLE_DOWN,
            on_click=self.on_next_pattern_click,
            icon_color=self.COLOR,
        )

        self.previous_pattern_button = ft.IconButton(
            icon=ft.Icons.ARROW_CIRCLE_UP,
            on_click=self.on_previous_pattern_click,
            icon_color=self.COLOR,
        )

        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            on_click=self.on_close_click,
            icon_color=self.COLOR,
        )

        self.controls.extend([
            self.search_field,
            self.next_pattern_button,
            self.previous_pattern_button,
            self.close_button,
        ])

    def _get_page(self):
        return self.page or self._app_page

    def on_next_pattern_click(self, e):
        self.tiles_container.scroll_to_next()

    def on_previous_pattern_click(self, e):
        self.tiles_container.scroll_to_previous()

    def on_close_click(self, e):
        go_back_from_search(self._get_page())

    def change_text_field(self, e):
        pattern = self.search_field.value
        self.tiles_container.indicate_patterns_and_scroll_to_first(pattern)

    def did_mount(self):
        self.tiles_container.trigger_searching_mode()

    def will_unmount(self):
        self.tiles_container.turn_off_searching_mode()
