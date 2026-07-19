"""Build route body hosts and synchronize their responsive widths."""

import flet as ft

from learning_app.ui.app_theme import AppTheme
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.layout_tokens import DEEP_FORM_VERTICAL_INSET


def control_is_on_page(control: ft.Control) -> bool:
    """Return whether a control is currently attached to a page.

    Accessing ``Control.page`` may raise while a control is detached; this
    helper treats that state as not mounted.

    Args:
        control: Control whose attachment state should be checked.

    Returns:
        ``True`` when the control exposes a non-``None`` page.
    """
    try:
        return control.page is not None
    except RuntimeError:
        return False


def wrap_safe_area(
    content: ft.Control,
    *,
    avoid_intrusions_top: bool = True,
    avoid_intrusions_bottom: bool = True,
    avoid_intrusions_left: bool = True,
    avoid_intrusions_right: bool = True,
    maintain_bottom_view_padding: bool = False,
) -> ft.SafeArea:
    """Wrap content in an expanding safe area.

    Safe-area protection prevents route content from being obscured by device
    cutouts, system bars, rounded corners, and gesture regions. Callers may
    disable an edge when shared application chrome already owns that inset.

    Args:
        content: Control to protect from system intrusions.
        avoid_intrusions_top: Whether to inset content from top intrusions.
        avoid_intrusions_bottom: Whether to inset content from bottom
            intrusions.
        avoid_intrusions_left: Whether to inset content from left intrusions.
        avoid_intrusions_right: Whether to inset content from right intrusions.
        maintain_bottom_view_padding: Whether to preserve bottom view padding
            when the on-screen keyboard is visible.

    Returns:
        An expanding safe-area control containing ``content``.
    """
    return ft.SafeArea(
        avoid_intrusions_top=avoid_intrusions_top,
        avoid_intrusions_bottom=avoid_intrusions_bottom,
        avoid_intrusions_left=avoid_intrusions_left,
        avoid_intrusions_right=avoid_intrusions_right,
        maintain_bottom_view_padding=maintain_bottom_view_padding,
        expand=True,
        content=content,
    )


def build_shell_body(page: ft.Page, *controls: ft.Control) -> ft.Column:
    """Build a centered, responsive column for shell-route content.

    Shell chrome owns its own insets, so this function only establishes body
    width and alignment.

    Args:
        page: Page used to refresh responsive layout metrics.
        *controls: Controls to place in the shell body.

    Returns:
        An expanding shell body column.
    """
    metrics = LayoutMetricsStore.refresh(page)
    return ft.Column(
        controls=list(controls),
        expand=True,
        width=metrics.body_width,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_search_body(page: ft.Page, *controls: ft.Control) -> ft.SafeArea:
    """Build search content protected on every safe-area edge.

    Search is a deep view without shared chrome, so its content must account
    for all system intrusions itself.

    Args:
        page: Page used to calculate responsive body width.
        *controls: Controls to place in the search body.

    Returns:
        A safe-area wrapper containing the responsive search column.
    """
    return wrap_safe_area(build_shell_body(page, *controls))


def build_bottom_inset_shell_body(page: ft.Page, *controls: ft.Control) -> ft.SafeArea:
    """Build shell content protected below its app bar.

    Settings and information routes retain the shared app bar but have no
    bottom app bar. The app bar owns the top inset, while the safe area keeps
    content clear of side and bottom system intrusions.

    Args:
        page: Page used to calculate responsive body width.
        *controls: Controls to place in the shell body.

    Returns:
        A safe-area wrapper with top-intrusion avoidance disabled.
    """
    return wrap_safe_area(
        build_shell_body(page, *controls),
        avoid_intrusions_top=False,
    )


def build_deep_body(
    page: ft.Page,
    *controls: ft.Control,
    content_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START,
) -> ft.Container:
    """Build a centered, width-constrained body for a deep form route.

    Deep routes do not use shared shell chrome. This host supplies consistent
    vertical form spacing; route-specific wrappers decide whether additional
    safe-area handling is required.

    Args:
        page: Page used to refresh responsive layout metrics.
        *controls: Controls to place in the form column.
        content_alignment: Main-axis alignment for controls in the form.

    Returns:
        An expanding themed container holding the form column.
    """
    metrics = LayoutMetricsStore.refresh(page)
    return ft.Container(
        content=ft.Column(
            controls=list(controls),
            expand=True,
            width=metrics.form_width,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=content_alignment,
        ),
        expand=True,
        bgcolor=AppTheme.current_bgcolor(),
        padding=ft.Padding.only(
            top=DEEP_FORM_VERTICAL_INSET,
            bottom=DEEP_FORM_VERTICAL_INSET,
        ),
    )


def sync_body_column_width(page: ft.Page, width: float):
    """Update the active route body's column width when it is mounted.

    Args:
        page: Page whose top view contains the route body.
        width: New logical-pixel width for the body column.
    """
    if not page.views:
        return
    body = page.views[-1].controls[0] if page.views[-1].controls else None
    if isinstance(body, ft.SafeArea) and isinstance(body.content, ft.Column):
        body = body.content
    if isinstance(body, ft.Container) and isinstance(body.content, ft.Column) and body.expand:
        body.content.width = width
        if control_is_on_page(body):
            body.update()
        return
    if isinstance(body, ft.Column) and body.expand:
        body.width = width
        if control_is_on_page(body):
            body.update()
