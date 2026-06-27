from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import flet as ft

from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore


@runtime_checkable
class RoutableScreen(Protocol):
    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None: ...


def has_apply_layout(control) -> bool:
    return callable(getattr(control, "apply_layout", None))


def is_routable(control) -> bool:
    return isinstance(control, RoutableScreen) or has_apply_layout(control)


def call_apply_layout(control, metrics: LayoutMetrics | None = None) -> bool:
    if control is None:
        return False
    apply_layout = getattr(control, "apply_layout", None)
    if not callable(apply_layout) or not control_is_on_page(control):
        return False
    apply_layout(metrics)
    return True


def iter_active_view_controls(page: ft.Page) -> Iterator[ft.Control]:
    if not page.views or not page.views[-1].controls:
        return
    stack = list(page.views[-1].controls)
    while stack:
        control = stack.pop()
        yield control
        nested = getattr(control, "controls", None)
        if nested:
            stack.extend(nested)
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, bytes)):
            if isinstance(content, list):
                stack.extend(content)
            else:
                stack.append(content)


def find_routable_in_active_view(
    page: ft.Page,
    control_type: type | tuple[type, ...] | None = None,
) -> ft.Control | None:
    types = None
    if control_type is not None:
        types = control_type if isinstance(control_type, tuple) else (control_type,)

    for control in iter_active_view_controls(page):
        if not is_routable(control):
            continue
        if types is not None and not isinstance(control, types):
            continue
        return control
    return None


class RoutableScreenMixin:
    """Shared layout lifecycle for controls used as route bodies."""

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:        raise NotImplementedError

    def resolve_layout_metrics(self, metrics: LayoutMetrics | None = None) -> LayoutMetrics:
        if metrics is not None:
            return metrics
        if control_is_on_page(self):
            return LayoutMetricsStore.refresh(self.page)
        app_page = getattr(self, "_app_page", None)
        if app_page is not None:
            return LayoutMetricsStore.refresh(app_page)
        return LayoutMetricsStore.get()

    def update_if_mounted(self) -> None:
        if control_is_on_page(self):
            self.update()

    def did_mount(self):
        self.apply_layout()
