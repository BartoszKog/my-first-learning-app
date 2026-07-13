"""Declarative registry of route factories, layouts, wrappers, and chrome.

Public surface for authors and maintainers:

* Enums ``RouteKind``, ``BodyWrapperKind``, and ``LayoutKind`` classify routes.
* ``RouteDef`` describes one registered route.
* ``ROUTE_REGISTRY`` is the authoritative ordered tuple of route definitions.
* ``get_route`` looks up a ``RouteDef`` by path.
* ``build_drawer_controls`` builds drawer destinations from shell routes.
* ``DRAWER_ROUTES``, ``DEEP_ROUTES``, and ``KNOWN_ROUTES`` expose path lists.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import flet as ft

from learning_app.ui.chrome_config import SHELL_CHROME, ShellChromeConfig
from learning_app.ui.route_paths import (
    CREATE_SET_ROUTE,
    HOME_ROUTE,
    IMPORT_EXPORT_ROUTE,
    INFO_ROUTE,
    SEARCH_ROUTE,
    SET_EDIT_ROUTE,
    SET_LEARN_ROUTE,
    SET_LEARN_SESSION_ROUTE,
    SETTINGS_ROUTE,
)
from learning_app.ui.screens.info_control import InfoControl
from learning_app.ui.screens.settings_control import SettingsControl

RouteBuildFactory = Callable[[ft.Page, dict[str, str]], list[ft.Control] | None]


class RouteKind(Enum):
    """Describe how a route participates in the page view stack.

    Attributes:
        SHELL: Root destination that replaces the current view stack.
        DEEP: Destination that may be pushed above a shell view.
    """

    SHELL = "shell"
    DEEP = "deep"


class BodyWrapperKind(Enum):
    """Select the host wrapper applied to route body controls.

    Attributes:
        SHELL: Width-constrained shell column without an added safe area.
        BOTTOM_INSET_SHELL: Shell column protected from side and bottom
            intrusions while allowing the app bar to own the top inset.
        DEEP: Width-constrained form container for a deep route.
        SEARCH: Shell-width column protected on every safe-area edge.
    """

    SHELL = "shell"
    BOTTOM_INSET_SHELL = "bottom_inset_shell"
    DEEP = "deep"
    SEARCH = "search"


class LayoutKind(Enum):
    """Select the resize-layout strategy for a route.

    Attributes:
        HOME: Refresh the home tile collection's flex layout.
        IMPORT_EXPORT: Apply routable shell sizing to import/export content.
        SEARCH: Apply routable shell sizing to search content.
        SHELL: Apply shell sizing to the route's declared layout control.
        DEEP_FORM: Apply form sizing to a routable deep-screen control.
    """

    HOME = "home"
    IMPORT_EXPORT = "import_export"
    SEARCH = "search"
    SHELL = "shell"
    DEEP_FORM = "deep_form"


def _content_width(page: ft.Page) -> float:
    from learning_app.ui.layout_metrics import LayoutMetricsStore

    return LayoutMetricsStore.refresh(page).form_width


def _build_learn_control(page: ft.Page, file_name: str, *, session: bool = False):
    from learning_app.data.app_data import get_kind_of_file_and_validate
    from learning_app.ui.components.word_definition_field import WordDefinitionField
    from learning_app.ui.components.word_fields import WordFields

    width = _content_width(page)
    kind = get_kind_of_file_and_validate(file_name)
    if kind == "words":
        return WordFields(file_name, page=page, width=width, session=session)
    return WordDefinitionField(file_name, page=page, width=width, session=session)


def _build_home_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.body_registry import BodyRegistry
    from learning_app.ui.components.tiles_container import TilesContainer

    body = TilesContainer(page)
    BodyRegistry.set_home(body)
    return [body]


def _build_import_export_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.screens.import_export_control import ImportExportControl

    return [ImportExportControl(page)]


def _build_settings_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.screens.settings_control import SettingsControl

    return [SettingsControl(page)]


def _build_info_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.screens.info_control import InfoControl

    return [InfoControl()]


def _build_create_set_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.screens.create_set_menu import CreateSetMenu

    return [CreateSetMenu(width=_content_width(page))]


def _build_edit_set_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.screens.edit_set_menu import EditSetMenu

    file_name = params.get("file")
    if not file_name:
        return None
    edit = EditSetMenu(
        file_name,
        title=params.get("title"),
        subtitle=params.get("subtitle"),
        width=_content_width(page),
    )
    return [edit]


def _build_learn_set_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    file_name = params.get("file")
    if not file_name:
        return None
    learn = _build_learn_control(page, file_name)
    return [learn]


def _build_learn_session_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    file_name = params.get("file")
    if not file_name:
        return None
    session = _build_learn_control(page, file_name, session=True)
    return [session]


def _build_search_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.body_registry import BodyRegistry
    from learning_app.ui.screens.search_screen import SearchScreen

    mode = params.get("mode", "home")
    if mode == "export" and BodyRegistry.has_export():
        tiles_container = BodyRegistry.get_export()
    elif BodyRegistry.has_home():
        tiles_container = BodyRegistry.get_home()
    else:
        return None
    search = SearchScreen(page, tiles_container)
    return [search]


@dataclass(frozen=True)
class RouteDef:
    """Describe all routing and presentation behavior for one route.

    Attributes:
        path: Canonical route path without query parameters.
        kind: Whether the route replaces the shell or is pushed as a deep view.
        body_wrapper: Wrapper used to host controls returned by the factory.
        layout_kind: Layout strategy applied initially and after resize events.
        chrome: Shared shell chrome configuration, or ``None`` for deep routes.
        build_factory: Callable that builds body controls from a page and
            decoded route parameters. Returning ``None`` triggers fallback.
        body_content_alignment: Main-axis alignment inside deep body columns.
        vertical_alignment: Main-axis alignment assigned to the Flet view.
        shell_layout_control: Optional control type used to identify the
            routable shell body during layout updates.
        drawer_label: Navigation drawer label, or ``None`` to omit the route.
        drawer_icon: Name of the corresponding ``ft.Icons`` member.
        drawer_divider_before: Whether to add a divider before this drawer item.
        fallback_path: Route used when the body factory returns ``None``.
    """

    path: str
    kind: RouteKind
    body_wrapper: BodyWrapperKind
    layout_kind: LayoutKind
    chrome: ShellChromeConfig | None
    build_factory: RouteBuildFactory
    body_content_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    vertical_alignment: ft.MainAxisAlignment = ft.MainAxisAlignment.START
    shell_layout_control: type | None = None
    drawer_label: str | None = None
    drawer_icon: str | None = None
    drawer_divider_before: bool = False
    fallback_path: str | None = None


ROUTE_REGISTRY: tuple[RouteDef, ...] = (
    RouteDef(
        path=HOME_ROUTE,
        kind=RouteKind.SHELL,
        body_wrapper=BodyWrapperKind.SHELL,
        layout_kind=LayoutKind.HOME,
        chrome=SHELL_CHROME[HOME_ROUTE],
        build_factory=_build_home_controls,
        vertical_alignment=ft.MainAxisAlignment.START,
        drawer_label="Learning sets",
        drawer_icon="BOOK",
    ),
    RouteDef(
        path=IMPORT_EXPORT_ROUTE,
        kind=RouteKind.SHELL,
        body_wrapper=BodyWrapperKind.SHELL,
        layout_kind=LayoutKind.IMPORT_EXPORT,
        chrome=SHELL_CHROME[IMPORT_EXPORT_ROUTE],
        build_factory=_build_import_export_controls,
        vertical_alignment=ft.MainAxisAlignment.START,
        drawer_label="Importing and exporting",
        drawer_icon="IMPORT_EXPORT",
        drawer_divider_before=True,
    ),
    RouteDef(
        path=SETTINGS_ROUTE,
        kind=RouteKind.SHELL,
        body_wrapper=BodyWrapperKind.BOTTOM_INSET_SHELL,
        layout_kind=LayoutKind.SHELL,
        chrome=SHELL_CHROME[SETTINGS_ROUTE],
        build_factory=_build_settings_controls,
        shell_layout_control=SettingsControl,
        drawer_label="Settings",
        drawer_icon="SETTINGS",
    ),
    RouteDef(
        path=INFO_ROUTE,
        kind=RouteKind.SHELL,
        body_wrapper=BodyWrapperKind.BOTTOM_INSET_SHELL,
        layout_kind=LayoutKind.SHELL,
        chrome=SHELL_CHROME[INFO_ROUTE],
        build_factory=_build_info_controls,
        shell_layout_control=InfoControl,
        drawer_label="Info",
        drawer_icon="INFO",
        drawer_divider_before=True,
    ),
    RouteDef(
        path=CREATE_SET_ROUTE,
        kind=RouteKind.DEEP,
        body_wrapper=BodyWrapperKind.DEEP,
        layout_kind=LayoutKind.DEEP_FORM,
        chrome=None,
        build_factory=_build_create_set_controls,
        body_content_alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    ),
    RouteDef(
        path=SET_EDIT_ROUTE,
        kind=RouteKind.DEEP,
        body_wrapper=BodyWrapperKind.DEEP,
        layout_kind=LayoutKind.DEEP_FORM,
        chrome=None,
        build_factory=_build_edit_set_controls,
        fallback_path=HOME_ROUTE,
    ),
    RouteDef(
        path=SET_LEARN_ROUTE,
        kind=RouteKind.DEEP,
        body_wrapper=BodyWrapperKind.DEEP,
        layout_kind=LayoutKind.DEEP_FORM,
        chrome=None,
        build_factory=_build_learn_set_controls,
        fallback_path=HOME_ROUTE,
    ),
    RouteDef(
        path=SET_LEARN_SESSION_ROUTE,
        kind=RouteKind.DEEP,
        body_wrapper=BodyWrapperKind.DEEP,
        layout_kind=LayoutKind.DEEP_FORM,
        chrome=None,
        build_factory=_build_learn_session_controls,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        fallback_path=HOME_ROUTE,
    ),
    RouteDef(
        path=SEARCH_ROUTE,
        kind=RouteKind.DEEP,
        body_wrapper=BodyWrapperKind.SEARCH,
        layout_kind=LayoutKind.SEARCH,
        chrome=None,
        build_factory=_build_search_controls,
        fallback_path=HOME_ROUTE,
    ),
)

ROUTES_BY_PATH: dict[str, RouteDef] = {route.path: route for route in ROUTE_REGISTRY}

DRAWER_ROUTE_DEFS: tuple[RouteDef, ...] = tuple(
    route for route in ROUTE_REGISTRY if route.drawer_label is not None
)
DRAWER_ROUTES: list[str] = [route.path for route in DRAWER_ROUTE_DEFS]
DEEP_ROUTES: list[str] = [route.path for route in ROUTE_REGISTRY if route.kind is RouteKind.DEEP]
KNOWN_ROUTES: list[str] = [route.path for route in ROUTE_REGISTRY]
ROUTE_TO_DRAWER_INDEX: dict[str, int] = {
    route.path: index for index, route in enumerate(DRAWER_ROUTE_DEFS)
}


def _drawer_icon(icon_name: str | None):
    if not icon_name:
        return None
    return getattr(ft.Icons, icon_name)


def build_drawer_controls() -> list[ft.Control]:
    """Build drawer destinations from registered drawer routes.

    Returns:
        A spacer followed by registered destinations and configured dividers.
    """
    controls: list[ft.Control] = [ft.Container(height=24)]
    for route in DRAWER_ROUTE_DEFS:
        if route.drawer_divider_before:
            controls.append(ft.Divider(thickness=2))
        controls.append(
            ft.NavigationDrawerDestination(
                label=route.drawer_label,
                icon=_drawer_icon(route.drawer_icon),
            )
        )
    return controls


def get_route(path: str) -> RouteDef | None:
    """Look up a route definition by canonical path.

    Args:
        path: Route path without query parameters.

    Returns:
        The matching route definition, or ``None`` when the path is unknown.
    """
    return ROUTES_BY_PATH.get(path)
