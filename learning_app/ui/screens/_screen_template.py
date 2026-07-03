"""Reference template for new routable screens — not wired to production.

Copy this file when adding a screen, then follow the checklist in comments below.

Checklist (shell screen):
  1. Add path constant to route_paths.py
  2. Add ShellChromeConfig entry in chrome_config.py (if drawer / app bar)
  3. Implement screen control (see ShellScreenTemplate)
  4. Add build factory + RouteDef in route_registry.py
  5. Navigate with: push_view(page, MY_ROUTE) or navigate_to(page, MY_ROUTE)

Checklist (deep screen):
  1. Add path constant to route_paths.py
  2. Implement screen control (see DeepScreenTemplate)
  3. Add build factory + RouteDef in route_registry.py
  4. Navigate with: push_view(page, MY_ROUTE, file=..., title=...)
  5. Use go_back(page) for cancel / back actions

See also: docs/adding-a-screen.md (when available)
"""

from __future__ import annotations

import flet as ft

from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.navigation import go_back
from learning_app.ui.routable_screen import RoutableScreenMixin

# ---------------------------------------------------------------------------
# Example path constant (add to route_paths.py, not here):
# MY_SHELL_ROUTE = "/my-shell"
# MY_DEEP_ROUTE = "/my-deep"
# ---------------------------------------------------------------------------


class ShellScreenTemplate(RoutableScreenMixin, ft.Container):
    """Minimal shell body — sits inside AppBar + bottom bar chrome.

    Use with build_shell_body or build_bottom_inset_shell_body in route_registry.
    Reference: InfoControl, SettingsControl, ImportExportControl.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self._app_page = page
        self.expand = True
        self.padding = 16

        self._width_label = ft.Text()
        self.content = ft.Column(
            controls=[
                ft.Text("ShellScreenTemplate demo", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "This route is wired temporarily so you can see how a shell screen "
                    "registers in route_paths, chrome_config, and route_registry.",
                ),
                ft.Divider(),
                self._width_label,
                ft.Text(
                    "Resize the window — body width below should update via apply_layout().",
                    italic=True,
                ),
                # Optional navigation example:
                # ft.Button(
                #     content="Open DeepScreenTemplate",
                #     on_click=lambda e: push_view(e.page, MY_DEEP_ROUTE, file="demo-label"),
                # ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        metrics = self.resolve_layout_metrics(metrics)
        self.width = metrics.body_width
        self._width_label.value = f"body_width: {metrics.body_width:.0f}px"
        self.update_if_mounted()


class DeepScreenTemplate(RoutableScreenMixin, ft.Column):
    """Minimal deep (full-screen) form — no drawer / bottom bar.

    Use with build_deep_body in route_registry.
    Reference: CreateSetMenu, EditSetMenu.
    """

    def __init__(self, width: float = 300, *, label: str = "Example"):
        super().__init__()
        self._form_width = width
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 12

        self.label_field = ft.TextField(label=label, width=width)
        self._width_label = ft.Text()
        self.controls = [
            ft.Text("DeepScreenTemplate demo", size=20, weight=ft.FontWeight.BOLD),
            ft.Text(
                "Full-screen deep route — no drawer or bottom bar. "
                "Cancel / Save call go_back() to return to the previous view.",
            ),
            self._width_label,
            self.label_field,
            ft.Row(
                controls=[
                    ft.Button(content="Cancel", on_click=lambda e: go_back(e.page)),
                    ft.Button(content="Save", on_click=self._on_save),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ]

    def apply_layout(self, metrics: LayoutMetrics | None = None) -> None:
        metrics = self.resolve_layout_metrics(metrics)
        self._form_width = metrics.form_width
        self.label_field.width = metrics.form_width
        self._width_label.value = f"form_width: {metrics.form_width:.0f}px"
        self.update_if_mounted()

    def _on_save(self, e: ft.ControlEvent) -> None:
        # Persist data, then return to previous view.
        go_back(e.page)


# ---------------------------------------------------------------------------
# Registration in route_registry.py (copy-paste starting point)
# ---------------------------------------------------------------------------
#
# def _build_my_shell_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
#     from learning_app.ui.layout_host import build_bottom_inset_shell_body
#     from learning_app.ui.screens.my_shell_screen import ShellScreenTemplate
#
#     return [build_bottom_inset_shell_body(page, ShellScreenTemplate(page))]
#
#
# def _build_my_deep_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
#     from learning_app.ui.layout_host import build_deep_body
#     from learning_app.ui.screens.my_deep_screen import DeepScreenTemplate
#
#     file_name = params.get("file")
#     if not file_name:
#         return None  # router falls back to fallback_path (usually HOME_ROUTE)
#     return [
#         build_deep_body(
#             page,
#             DeepScreenTemplate(width=_content_width(page), label=file_name),
#         )
#     ]
#
#
# Add to ROUTE_REGISTRY tuple:
#
# RouteDef(
#     path=MY_SHELL_ROUTE,
#     kind=RouteKind.SHELL,
#     body_wrapper=BodyWrapperKind.BOTTOM_INSET_SHELL,  # or BodyWrapperKind.SHELL
#     layout_kind=LayoutKind.SHELL,
#     chrome=SHELL_CHROME[MY_SHELL_ROUTE],
#     build_factory=_build_my_shell_controls,
#     shell_layout_control=ShellScreenTemplate,  # enables resize dispatch
#     drawer_label="My screen",                    # omit for non-drawer routes
#     drawer_icon="STAR",
# ),
#
# RouteDef(
#     path=MY_DEEP_ROUTE,
#     kind=RouteKind.DEEP,
#     body_wrapper=BodyWrapperKind.DEEP,
#     layout_kind=LayoutKind.DEEP_FORM,
#     chrome=None,
#     build_factory=_build_my_deep_controls,
#     fallback_path=HOME_ROUTE,
# ),
#
# Add to chrome_config.py (shell only):
#
# SHELL_CHROME[MY_SHELL_ROUTE] = ShellChromeConfig(
#     appbar_title="My screen",
#     appbar_menu_leading=True,
#     bottom_appbar_visible=False,
#     fab_visible=False,
#     search_button_visible=False,
# )
#
# Navigate from anywhere:
#
# from learning_app.ui.navigation import navigate_to, push_view
# from learning_app.ui.route_paths import MY_SHELL_ROUTE, MY_DEEP_ROUTE
#
# navigate_to(page, MY_SHELL_ROUTE)
# push_view(page, MY_DEEP_ROUTE, file="example.csv")
