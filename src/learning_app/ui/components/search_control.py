import flet as ft

from learning_app.ui.components.tiles_container import TilesContainer


class SearchControl(ft.Row):
    """Search field and next/previous controls over a shared ``TilesContainer``.

    Used by in-place search on Home/Export. Closing calls ``on_close`` when
    provided (preferred), otherwise does nothing.

    Args:
        page: Unused; kept for call-site compatibility.
        tiles_container: Home or export tile list to filter.
        on_close: Optional callback invoked by the close button.
    """

    COLOR = ft.Colors.CYAN

    def __init__(self, page, tiles_container: TilesContainer, on_close=None):
        super().__init__()
        _ = page
        self.tiles_container = tiles_container
        self._on_close = on_close

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

    def on_next_pattern_click(self, e):
        self.tiles_container.scroll_to_next()

    def on_previous_pattern_click(self, e):
        self.tiles_container.scroll_to_previous()

    def on_close_click(self, e):
        if self._on_close is not None:
            self._on_close(e)

    def change_text_field(self, e):
        pattern = self.search_field.value
        self.tiles_container.indicate_patterns_and_scroll_to_first(pattern)
