import flet as ft

from learning_app.ui.components.search_control import SearchControl
from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore


class SearchScreen(ft.Column):
    def __init__(self, page, tiles_container: TilesContainer):
        super().__init__()
        self.expand = True
        self.spacing = 0
        self.tiles_container = tiles_container
        self.search_control = SearchControl(page, tiles_container)
        self.tiles_container.expand = True
        self.controls = [self.search_control, tiles_container]

    def did_mount(self):
        self.apply_layout(LayoutMetricsStore.refresh(self.page))

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        if metrics is None:
            metrics = LayoutMetricsStore.get()
        self.tiles_container.apply_flex_layout(metrics)
