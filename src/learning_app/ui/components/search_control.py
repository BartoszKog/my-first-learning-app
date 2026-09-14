import flet as ft

from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore


class SearchControl(ft.Row):
    """Search field and next/previous controls over a shared ``TilesContainer``.

    Used by in-place search on Home/Export. Closing calls ``on_close`` when
    provided (preferred), otherwise does nothing.

    Args:
        page: Page used to measure the initial search width.
        tiles_container: Home or export tile list to filter.
        on_close: Optional callback invoked by the close button.
    """

    FIELD_FILL = ft.Colors.TEAL_700
    ICON_COLOR = ft.Colors.WHITE
    ICON_SIZE = 32

    def __init__(self, page, tiles_container: TilesContainer, on_close=None):
        super().__init__()
        self.tiles_container = tiles_container
        self._on_close = on_close

        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.tight = True
        self.spacing = 8
        self.search_field = ft.TextField(
            hint_text="Search",
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.7, self.ICON_COLOR),
                size=16,
            ),
            text_size=16,
            text_style=ft.TextStyle(color=self.ICON_COLOR, weight=ft.FontWeight.W_500),
            prefix_icon=ft.Icon(ft.Icons.SEARCH, color=self.ICON_COLOR, size=22),
            expand=True,
            autofocus=True,
            on_change=self.change_text_field,
            filled=True,
            fill_color=self.FIELD_FILL,
            focused_bgcolor=self.FIELD_FILL,
            color=self.ICON_COLOR,
            cursor_color=self.ICON_COLOR,
            border=ft.InputBorder.OUTLINE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.with_opacity(0.65, self.ICON_COLOR),
            border_width=1.5,
            focused_border_width=2,
            border_radius=28,
            dense=True,
            content_padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        )

        self.next_pattern_button = self._icon_button(
            ft.Icons.ARROW_CIRCLE_DOWN,
            self.on_next_pattern_click,
        )
        self.previous_pattern_button = self._icon_button(
            ft.Icons.ARROW_CIRCLE_UP,
            self.on_previous_pattern_click,
        )
        self.close_button = self._icon_button(
            ft.Icons.CLOSE,
            self.on_close_click,
        )

        self.controls.extend([
            self.search_field,
            self.next_pattern_button,
            self.previous_pattern_button,
            self.close_button,
        ])
        self.apply_flex_layout(
            LayoutMetricsStore.refresh(page) if page is not None else None
        )

    def apply_flex_layout(self, metrics: LayoutMetrics | None = None) -> None:
        """Match tile width on roomy screens; fill the app bar on compact ones."""
        if metrics is None:
            metrics = LayoutMetricsStore.get()
        self.width = None if metrics.breakpoint == "compact" else metrics.body_width
        if control_is_on_page(self):
            self.update()

    def _icon_button(self, icon, on_click) -> ft.IconButton:
        return ft.IconButton(
            icon=icon,
            on_click=on_click,
            icon_color=self.ICON_COLOR,
            icon_size=self.ICON_SIZE,
        )

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
