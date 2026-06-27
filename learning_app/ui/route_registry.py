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
    SHELL = "shell"
    DEEP = "deep"


class BodyWrapperKind(Enum):
    SHELL = "shell"
    BOTTOM_INSET_SHELL = "bottom_inset_shell"
    DEEP = "deep"
    SEARCH = "search"


class LayoutKind(Enum):
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
    from learning_app.ui.layout_host import build_shell_body

    body = TilesContainer(page)
    BodyRegistry.set_home(body)
    return [build_shell_body(page, body)]


def _build_import_export_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.layout_host import build_shell_body
    from learning_app.ui.screens.import_export_control import ImportExportControl

    return [build_shell_body(page, ImportExportControl(page))]


def _build_settings_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.layout_host import build_bottom_inset_shell_body
    from learning_app.ui.screens.settings_control import SettingsControl

    return [build_bottom_inset_shell_body(page, SettingsControl(page))]


def _build_info_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.layout_host import build_bottom_inset_shell_body
    from learning_app.ui.screens.info_control import InfoControl

    return [build_bottom_inset_shell_body(page, InfoControl())]


def _build_create_set_controls(page: ft.Page, _params: dict[str, str]) -> list[ft.Control]:
    from learning_app.ui.layout_host import build_deep_body
    from learning_app.ui.screens.create_set_menu import CreateSetMenu

    return [
        build_deep_body(
            page,
            CreateSetMenu(width=_content_width(page)),
            content_alignment=ft.MainAxisAlignment.CENTER,
        )
    ]


def _build_edit_set_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.layout_host import build_deep_body
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
    return [build_deep_body(page, edit)]


def _build_learn_set_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.layout_host import build_deep_body

    file_name = params.get("file")
    if not file_name:
        return None
    learn = _build_learn_control(page, file_name)
    return [build_deep_body(page, learn)]


def _build_learn_session_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.layout_host import build_deep_body

    file_name = params.get("file")
    if not file_name:
        return None
    session = _build_learn_control(page, file_name, session=True)
    return [build_deep_body(page, session)]


def _build_search_controls(page: ft.Page, params: dict[str, str]) -> list[ft.Control] | None:
    from learning_app.ui.body_registry import BodyRegistry
    from learning_app.ui.layout_host import build_search_body
    from learning_app.ui.screens.search_screen import SearchScreen

    mode = params.get("mode", "home")
    if mode == "export" and BodyRegistry.has_export():
        tiles_container = BodyRegistry.get_export()
    elif BodyRegistry.has_home():
        tiles_container = BodyRegistry.get_home()
    else:
        return None
    search = SearchScreen(page, tiles_container)
    return [build_search_body(page, search)]


@dataclass(frozen=True)
class RouteDef:
    path: str
    kind: RouteKind
    body_wrapper: BodyWrapperKind
    layout_kind: LayoutKind
    chrome: ShellChromeConfig | None
    build_factory: RouteBuildFactory
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
    return ROUTES_BY_PATH.get(path)
