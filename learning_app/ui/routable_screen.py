"""Structural layout lifecycle for controls hosted by routed views."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import flet as ft

from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore


@runtime_checkable
class RoutableScreen(Protocol):
    """Protocol implemented by controls that respond to route layout changes."""

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        """Apply a responsive layout snapshot to the control.

        Args:
            metrics: Metrics to apply, or ``None`` to resolve current metrics.
        """
        ...


def has_apply_layout(control: object) -> bool:
    """Return whether a value exposes a callable ``apply_layout`` attribute.

    Args:
        control: Value to inspect.

    Returns:
        ``True`` when ``apply_layout`` is callable.
    """
    return callable(getattr(control, "apply_layout", None))


def is_routable(control: object) -> bool:
    """Return whether a value supports the routable-screen lifecycle.

    Args:
        control: Value to inspect.

    Returns:
        ``True`` for protocol instances or objects with a callable
        ``apply_layout`` attribute.
    """
    return isinstance(control, RoutableScreen) or has_apply_layout(control)


def call_apply_layout(
    control: object,
    metrics: LayoutMetrics | None = None,
) -> bool:
    """Apply layout to a mounted routable control.

    Args:
        control: Candidate control, which may be ``None``.
        metrics: Optional responsive metrics passed to ``apply_layout``.

    Returns:
        ``True`` when ``apply_layout`` was called; otherwise ``False``.
    """
    if control is None:
        return False
    apply_layout = getattr(control, "apply_layout", None)
    if not callable(apply_layout) or not control_is_on_page(control):
        return False
    apply_layout(metrics)
    return True


def iter_active_view_controls(page: ft.Page) -> Iterator[ft.Control]:
    """Yield controls in the active view using depth-first traversal.

    Both multi-child ``controls`` collections and single-child ``content``
    relationships are traversed.

    Args:
        page: Page whose top view should be traversed.

    Yields:
        Each control reachable from the active view's root controls.
    """
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
    """Find the first routable control in the active view.

    Args:
        page: Page whose active view should be searched.
        control_type: Optional type or tuple of types used to restrict matches.

    Returns:
        The first matching routable control, or ``None`` when no match exists.
    """
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
    """Provide shared layout lifecycle helpers for route body controls."""

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        """Apply route layout metrics in a concrete screen implementation.

        Args:
            metrics: Metrics to apply, or ``None`` to resolve current metrics.

        Raises:
            NotImplementedError: Always; subclasses must implement this method.
        """
        raise NotImplementedError

    def resolve_layout_metrics(self, metrics: LayoutMetrics | None = None) -> LayoutMetrics:
        """Resolve explicit, page-derived, or cached layout metrics.

        Args:
            metrics: Explicit metrics to return unchanged when provided.

        Returns:
            Explicit metrics, freshly computed page metrics when a page is
            available, or the latest cached/default metrics.
        """
        if metrics is not None:
            return metrics
        if control_is_on_page(self):
            return LayoutMetricsStore.refresh(self.page)
        app_page = getattr(self, "_app_page", None)
        if app_page is not None:
            return LayoutMetricsStore.refresh(app_page)
        return LayoutMetricsStore.get()

    def update_if_mounted(self) -> None:
        """Request a control update only while attached to a page."""
        if control_is_on_page(self):
            self.update()

    def did_mount(self):
        """Apply the initial responsive layout after the control mounts."""
        self.apply_layout()
