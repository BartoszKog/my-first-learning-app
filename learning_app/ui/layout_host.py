import flet as ft

from learning_app.ui.app_theme import AppTheme
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.layout_tokens import DEEP_FORM_VERTICAL_INSET


def control_is_on_page(control: ft.Control) -> bool:
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
    metrics = LayoutMetricsStore.refresh(page)
    return ft.Column(
        controls=list(controls),
        expand=True,
        width=metrics.body_width,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_search_body(page: ft.Page, *controls: ft.Control) -> ft.SafeArea:
    return wrap_safe_area(build_shell_body(page, *controls))


def build_bottom_inset_shell_body(page: ft.Page, *controls: ft.Control) -> ft.SafeArea:
    """Shell routes with AppBar but no bottom bar (Settings, Info)."""
    return wrap_safe_area(
        build_shell_body(page, *controls),
        avoid_intrusions_top=False,
    )


def build_deep_body(
    page: ft.Page,
    *controls: ft.Control,
    content_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START,
) -> ft.Container:
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
