"""Compute and cache responsive dimensions for route body controls."""

from dataclasses import dataclass

import flet as ft

from learning_app.ui.chrome_config import SHELL_CHROME
from learning_app.ui.layout_tokens import (
    BODY_WIDTH_RATIO,
    BREAKPOINT_COMPACT,
    BREAKPOINT_WIDE,
    CONTENT_MAX_WIDTH,
    DEFAULT_APPBAR_HEIGHT,
    DEFAULT_BOTTOM_APPBAR_HEIGHT,
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    FORM_WIDTH_RATIO,
    LEARN_DEFINITION_FIELD_WIDTH_RATIO,
    LEARN_DEFINITION_FIELD_WIDTH_RATIO_WINDOWS,
    LEARN_WORDS_FIELD_WIDTH_RATIO,
    LEARN_WORDS_FIELD_WIDTH_RATIO_WINDOWS,
    SETTINGS_WIDTH_RATIO,
)
from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.route_url import route_path


@dataclass(frozen=True)
class LayoutMetrics:
    """Snapshot of dimensions used by responsive route layouts.

    Attributes:
        viewport_width: Current page or window width in logical pixels.
        viewport_height: Current page or window height in logical pixels.
        body_width: Width allocated to general shell content.
        form_width: Width allocated to deep forms.
        settings_width: Width allocated to settings content.
        content_height: Viewport height remaining after visible chrome and
            configured padding are subtracted.
        breakpoint: Responsive category: ``"compact"``, ``"normal"``, or
            ``"wide"``.
        platform: Current Flet page platform when known.
    """

    viewport_width: float
    viewport_height: float
    body_width: float
    form_width: float
    settings_width: float
    content_height: float
    breakpoint: str
    platform: ft.PagePlatform | None = None


def _viewport_width(page: ft.Page) -> float:
    if page.width:
        return page.width
    if getattr(page, "window", None) and page.window.width:
        return page.window.width
    return DEFAULT_VIEWPORT_WIDTH


def _viewport_height(page: ft.Page) -> float:
    if page.height:
        return page.height
    if getattr(page, "window", None) and page.window.height:
        return page.window.height
    return DEFAULT_VIEWPORT_HEIGHT


def _bounded_width(viewport_width: float, ratio: float) -> float:
    return min(viewport_width * ratio, CONTENT_MAX_WIDTH * ratio / BODY_WIDTH_RATIO)


def _breakpoint(viewport_width: float) -> str:
    if viewport_width < BREAKPOINT_COMPACT:
        return "compact"
    if viewport_width >= BREAKPOINT_WIDE:
        return "wide"
    return "normal"


def _chrome_occupied_height(page: ft.Page) -> float:
    occupied = 0.0
    path = route_path(page.route)

    appbar = AppChrome.get_appbar()
    if appbar and getattr(appbar, "visible", True):
        occupied += (
            getattr(appbar, "toolbar_height", None)
            or getattr(appbar, "height", None)
            or DEFAULT_APPBAR_HEIGHT
        )

    bottom_appbar = AppChrome.get_bottom_appbar()
    shell_config = SHELL_CHROME.get(path)
    bottom_visible = shell_config.bottom_appbar_visible if shell_config else False
    if bottom_appbar and bottom_visible and getattr(bottom_appbar, "visible", True):
        occupied += getattr(bottom_appbar, "height", None) or DEFAULT_BOTTOM_APPBAR_HEIGHT

    padding = page.padding
    if padding:
        occupied += (padding.top or 0) + (padding.bottom or 0)

    if page.views:
        view_padding = page.views[-1].padding
        if view_padding:
            occupied += (view_padding.top or 0) + (view_padding.bottom or 0)

    return occupied


def compute_layout_metrics(page: ft.Page) -> LayoutMetrics:
    """Calculate a responsive layout snapshot for a page.

    Visible shared chrome, page padding, and active-view padding are subtracted
    from viewport height. Widths are ratio-based and capped by layout tokens.

    Args:
        page: Page supplying viewport, platform, route, chrome, and padding
            state.

    Returns:
        The calculated immutable layout metrics.
    """
    viewport_width = _viewport_width(page)
    viewport_height = _viewport_height(page)
    content_height = max(viewport_height - _chrome_occupied_height(page), 0)

    return LayoutMetrics(
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        body_width=_bounded_width(viewport_width, BODY_WIDTH_RATIO),
        form_width=_bounded_width(viewport_width, FORM_WIDTH_RATIO),
        settings_width=_bounded_width(viewport_width, SETTINGS_WIDTH_RATIO),
        content_height=content_height,
        breakpoint=_breakpoint(viewport_width),
        platform=page.platform,
    )


class LayoutMetricsStore:
    """Process-wide cache of the most recently computed layout metrics."""

    _current: LayoutMetrics | None = None

    @classmethod
    def refresh(cls, page: ft.Page) -> LayoutMetrics:
        """Recompute and cache metrics for a page.

        Args:
            page: Page whose current layout state should be measured.

        Returns:
            The newly computed metrics.
        """
        cls._current = compute_layout_metrics(page)
        return cls._current

    @classmethod
    def get(cls) -> LayoutMetrics:
        """Return cached metrics or a default pre-layout snapshot.

        Returns:
            The latest metrics, or token-based defaults before the first
            refresh.
        """
        if cls._current is None:
            return LayoutMetrics(
                viewport_width=DEFAULT_VIEWPORT_WIDTH,
                viewport_height=DEFAULT_VIEWPORT_HEIGHT,
                body_width=DEFAULT_VIEWPORT_WIDTH * BODY_WIDTH_RATIO,
                form_width=DEFAULT_VIEWPORT_WIDTH * FORM_WIDTH_RATIO,
                settings_width=DEFAULT_VIEWPORT_WIDTH * SETTINGS_WIDTH_RATIO,
                content_height=DEFAULT_VIEWPORT_HEIGHT,
                breakpoint="normal",
            )
        return cls._current


def _resolve_platform(page: ft.Page | None = None) -> ft.PagePlatform | None:
    if page is not None and page.platform is not None:
        return page.platform
    return LayoutMetricsStore.get().platform


def is_windows_platform(page: ft.Page | None = None) -> bool:
    """Return whether the explicit or cached platform is Windows.

    Args:
        page: Optional page whose platform takes precedence over cached
            metrics.

    Returns:
        ``True`` when the resolved platform is Windows.
    """
    return _resolve_platform(page) == ft.PagePlatform.WINDOWS


def is_android_platform(page: ft.Page | None = None) -> bool:
    """Return whether the explicit or cached platform is Android.

    Args:
        page: Optional page whose platform takes precedence over cached
            metrics.

    Returns:
        ``True`` when the resolved platform is Android.
    """
    return _resolve_platform(page) == ft.PagePlatform.ANDROID


def learn_words_field_width(form_width: float, page: ft.Page | None = None) -> float:
    """Calculate the words exercise field width for a platform.

    Args:
        form_width: Available form width in logical pixels.
        page: Optional page used to resolve the platform.

    Returns:
        The field width after applying the platform-specific ratio.
    """
    ratio = (
        LEARN_WORDS_FIELD_WIDTH_RATIO_WINDOWS
        if is_windows_platform(page)
        else LEARN_WORDS_FIELD_WIDTH_RATIO
    )
    return form_width * ratio


def learn_definition_field_width(form_width: float, page: ft.Page | None = None) -> float:
    """Calculate the definition exercise field width for a platform.

    Args:
        form_width: Available form width in logical pixels.
        page: Optional page used to resolve the platform.

    Returns:
        The field width after applying the platform-specific ratio.
    """
    ratio = (
        LEARN_DEFINITION_FIELD_WIDTH_RATIO_WINDOWS
        if is_windows_platform(page)
        else LEARN_DEFINITION_FIELD_WIDTH_RATIO
    )
    return form_width * ratio
