import flet as ft

from learning_app.ui.components.search_control import SearchControl
from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.routable_screen import RoutableScreenMixin


class SearchScreen(RoutableScreenMixin, ft.Column):
    def __init__(self, page, tiles_container: TilesContainer):
        super().__init__()
        self.expand = True
        self.spacing = 0
        self.tiles_container = tiles_container
        self.search_control = SearchControl(page, tiles_container)
        self.tiles_container.expand = True
        self.controls = [self.search_control, tiles_container]

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        metrics = self.resolve_layout_metrics(metrics)
        self.tiles_container.apply_flex_layout(metrics)
