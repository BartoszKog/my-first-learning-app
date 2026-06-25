import flet as ft

from learning_app.data.app_data import get_kind_of_file_and_validate
from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.components.word_definition_field import WordDefinitionField
from learning_app.ui.components.word_fields import WordFields
from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.body_registry import BodyRegistry
from learning_app.ui.chrome_config import SHELL_CHROME
from learning_app.ui.layout_host import (
    build_bottom_inset_shell_body,
    build_deep_body,
    build_search_body,
    build_shell_body,
    control_is_on_page,
    sync_body_column_width,
)
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.route_url import route_params, route_path, routes_match
from learning_app.ui.routes import (
    CREATE_SET_ROUTE,
    DEEP_ROUTES,
    DRAWER_ROUTES,
    HOME_ROUTE,
    IMPORT_EXPORT_ROUTE,
    INFO_ROUTE,
    KNOWN_ROUTES,
    ROUTE_TO_DRAWER_INDEX,
    SEARCH_ROUTE,
    SET_EDIT_ROUTE,
    SET_LEARN_ROUTE,
    SET_LEARN_SESSION_ROUTE,
    SETTINGS_ROUTE,
)
from learning_app.ui.screens.create_set_menu import CreateSetMenu
from learning_app.ui.screens.edit_set_menu import EditSetMenu
from learning_app.ui.screens.import_export_control import ImportExportControl
from learning_app.ui.screens.info_control import InfoControl
from learning_app.ui.screens.search_screen import SearchScreen
from learning_app.ui.screens.settings_control import SettingsControl
from learning_app.utils.greetings import Greetings

FORM_LAYOUT_ROUTES = {
    CREATE_SET_ROUTE,
    SET_EDIT_ROUTE,
    SET_LEARN_ROUTE,
    SET_LEARN_SESSION_ROUTE,
}


def is_current_route(page: ft.Page, route: str) -> bool:
    return route_path(page.route) == route


def _content_width(page: ft.Page) -> float:
    return LayoutMetricsStore.refresh(page).form_width


def _sync_shell_body_layout(page: ft.Page):
    metrics = LayoutMetricsStore.get()
    sync_body_column_width(page, metrics.body_width)


def _sync_deep_body_layout(page: ft.Page):
    metrics = LayoutMetricsStore.get()
    sync_body_column_width(page, metrics.form_width)


def _apply_home_flex_layout(page: ft.Page):
    if not BodyRegistry.has_home():
        return
    metrics = LayoutMetricsStore.refresh(page)
    BodyRegistry.get_home().apply_flex_layout(metrics)
    _sync_shell_body_layout(page)


def _find_in_active_view(page: ft.Page, control_type: type | tuple[type, ...]):
    if not page.views or not page.views[-1].controls:
        return None
    types = control_type if isinstance(control_type, tuple) else (control_type,)
    stack = list(page.views[-1].controls)
    while stack:
        control = stack.pop()
        if isinstance(control, types):
            return control
        nested = getattr(control, "controls", None)
        if nested:
            stack.extend(nested)
        content = getattr(control, "content", None)
        if content is not None and not isinstance(content, (str, bytes)):
            if isinstance(content, list):
                stack.extend(content)
            else:
                stack.append(content)
    return None


def _apply_import_export_layout(page: ft.Page):
    LayoutMetricsStore.refresh(page)
    _sync_shell_body_layout(page)
    control = _find_in_active_view(page, ImportExportControl)
    if control and control_is_on_page(control):
        control.apply_layout()


def _apply_search_layout(page: ft.Page):
    metrics = LayoutMetricsStore.refresh(page)
    _sync_shell_body_layout(page)
    search = _find_in_active_view(page, SearchScreen)
    if search:
        search.apply_layout(metrics)


def _apply_shell_screen_layout(page: ft.Page, control_type: type):
    metrics = LayoutMetricsStore.refresh(page)
    _sync_shell_body_layout(page)
    control = _find_in_active_view(page, control_type)
    if control and control_is_on_page(control):
        control.apply_layout(metrics)


def _apply_deep_form_layout(page: ft.Page):
    metrics = LayoutMetricsStore.refresh(page)
    _sync_deep_body_layout(page)

    for control_type in (EditSetMenu, CreateSetMenu):
        control = _find_in_active_view(page, control_type)
        if control and control_is_on_page(control):
            control.apply_layout(metrics)
            return

    word_field = _find_in_active_view(page, (WordFields, WordDefinitionField))
    if word_field and control_is_on_page(word_field):
        word_field.apply_layout(metrics)


def _apply_layout_for_route(page: ft.Page, path: str):
    if path == HOME_ROUTE:
        _apply_home_flex_layout(page)
    elif path == IMPORT_EXPORT_ROUTE:
        _apply_import_export_layout(page)
    elif path == SEARCH_ROUTE:
        _apply_search_layout(page)
    elif path == SETTINGS_ROUTE:
        _apply_shell_screen_layout(page, SettingsControl)
    elif path == INFO_ROUTE:
        _apply_shell_screen_layout(page, InfoControl)
    elif path in FORM_LAYOUT_ROUTES:
        _apply_deep_form_layout(page)


def _restore_active_view_state(page: ft.Page, full_route: str):
    LayoutMetricsStore.refresh(page)
    _update_drawer_selection(full_route)
    _sync_chrome_for_route(full_route, page)
    _refresh_learn_menu_view(page, full_route)
    _apply_layout_for_route(page, route_path(full_route))


def _apply_shell_chrome(path: str):
    config = SHELL_CHROME[path]
    appbar = AppChrome.get_appbar()
    appbar.visible = True
    appbar.leading = AppChrome.get_appbar_menu_button() if config.appbar_menu_leading else None
    appbar.title.value = Greetings.get_greeting() if config.appbar_title == "__greeting__" else config.appbar_title

    bottom_appbar = AppChrome.get_bottom_appbar()
    bottom_appbar.visible = config.bottom_appbar_visible
    if config.bottom_appbar_visible:
        bottom_appbar.height = config.bottom_appbar_height
        if path != IMPORT_EXPORT_ROUTE:
            AppChrome.get_search_button().visible = config.search_button_visible

    AppChrome.get_floating_action_button().visible = config.fab_visible


def _configure_deep_chrome(page: ft.Page):
    AppChrome.get_appbar().visible = False
    AppChrome.get_bottom_appbar().visible = False
    AppChrome.get_floating_action_button().visible = False


def _sync_chrome_for_route(full_route: str, page: ft.Page):
    path = route_path(full_route)
    if path in SHELL_CHROME:
        _apply_shell_chrome(path)
    else:
        _configure_deep_chrome(page)
    AppTheme.apply_to_page(page)


def _update_drawer_selection(full_route: str):
    path = route_path(full_route)
    AppChrome.get_drawer().selected_index = ROUTE_TO_DRAWER_INDEX.get(path, 0)


def _route_already_active(page: ft.Page, full_route: str) -> bool:
    return bool(page.views) and routes_match(page.views[-1].route, full_route)


def _refresh_learn_menu_view(page: ft.Page, full_route: str):
    if route_path(full_route) != SET_LEARN_ROUTE or not page.views:
        return

    control = _find_in_active_view(page, (WordFields, WordDefinitionField))
    if control:
        control.menu_control.refresh_content()
        control.words.refresh()
        if control_is_on_page(control):
            control.apply_layout()
            control.update()


def _detach_shared_chrome_from_views(page: ft.Page):
    appbar = AppChrome.get_appbar()
    bottom_appbar = AppChrome.get_bottom_appbar()
    fab = AppChrome.get_floating_action_button()
    drawer = AppChrome.get_drawer()

    for view in page.views:
        if getattr(view, "appbar", None) is appbar:
            view.appbar = None
        if getattr(view, "bottom_appbar", None) is bottom_appbar:
            view.bottom_appbar = None
        if getattr(view, "floating_action_button", None) is fab:
            view.floating_action_button = None
        if getattr(view, "drawer", None) is drawer:
            view.drawer = None


def _build_shell_view(
    page: ft.Page,
    full_route: str,
    controls: list,
    *,
    vertical_alignment: ft.MainAxisAlignment | None = None,
) -> ft.View:
    _apply_shell_chrome(route_path(full_route))
    return ft.View(
        route=full_route,
        controls=controls,
        appbar=AppChrome.get_appbar(),
        bottom_appbar=AppChrome.get_bottom_appbar(),
        floating_action_button=AppChrome.get_floating_action_button(),
        floating_action_button_location=AppChrome.get_floating_action_button_location(),
        drawer=AppChrome.get_drawer(),
        horizontal_alignment=AppChrome.get_horizontal_alignment(),
        vertical_alignment=vertical_alignment or AppChrome.get_vertical_alignment(),
        padding=page.padding,
        bgcolor=AppTheme.current_bgcolor(),
    )


def _build_deep_view(
    page: ft.Page,
    full_route: str,
    controls: list,
    *,
    vertical_alignment: ft.MainAxisAlignment | None = None,
) -> ft.View:
    return ft.View(
        route=full_route,
        controls=controls,
        horizontal_alignment=AppChrome.get_horizontal_alignment(),
        vertical_alignment=vertical_alignment or ft.MainAxisAlignment.START,
        padding=page.padding,
        bgcolor=AppTheme.current_bgcolor(),
    )


def _build_learn_control(page: ft.Page, file_name: str, *, session: bool = False):
    width = _content_width(page)
    kind = get_kind_of_file_and_validate(file_name)
    if kind == "words":
        return WordFields(file_name, page=page, width=width, session=session)
    return WordDefinitionField(file_name, page=page, width=width, session=session)


def _build_route_view(full_route: str, page: ft.Page) -> ft.View:
    path = route_path(full_route)
    params = route_params(full_route)

    if path == HOME_ROUTE:
        body = TilesContainer(page)
        BodyRegistry.set_home(body)
        return _build_shell_view(
            page,
            full_route,
            [build_shell_body(page, body)],
            vertical_alignment=ft.MainAxisAlignment.START,
        )

    if path == IMPORT_EXPORT_ROUTE:
        return _build_shell_view(
            page,
            full_route,
            [build_shell_body(page, ImportExportControl(page))],
            vertical_alignment=ft.MainAxisAlignment.START,
        )

    if path == SETTINGS_ROUTE:
        return _build_shell_view(
            page,
            full_route,
            [build_bottom_inset_shell_body(page, SettingsControl(page))],
        )

    if path == INFO_ROUTE:
        return _build_shell_view(
            page,
            full_route,
            [build_bottom_inset_shell_body(page, InfoControl())],
        )

    if path == CREATE_SET_ROUTE:
        _configure_deep_chrome(page)
        return _build_deep_view(
            page,
            full_route,
            [
                build_deep_body(
                    page,
                    CreateSetMenu(width=_content_width(page)),
                    content_alignment=ft.MainAxisAlignment.CENTER,
                )
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )

    if path == SET_EDIT_ROUTE:
        file_name = params.get("file")
        if not file_name:
            return _build_route_view(HOME_ROUTE, page)
        _configure_deep_chrome(page)
        title = params.get("title")
        subtitle = params.get("subtitle")
        edit = EditSetMenu(
            file_name,
            title=title,
            subtitle=subtitle,
            width=_content_width(page),
        )
        return _build_deep_view(page, full_route, [build_deep_body(page, edit)])

    if path == SET_LEARN_ROUTE:
        file_name = params.get("file")
        if not file_name:
            return _build_route_view(HOME_ROUTE, page)
        _configure_deep_chrome(page)
        learn = _build_learn_control(page, file_name)
        return _build_deep_view(page, full_route, [build_deep_body(page, learn)])

    if path == SET_LEARN_SESSION_ROUTE:
        file_name = params.get("file")
        if not file_name:
            return _build_route_view(HOME_ROUTE, page)
        _configure_deep_chrome(page)
        session = _build_learn_control(page, file_name, session=True)
        return _build_deep_view(
            page,
            full_route,
            [build_deep_body(page, session)],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
        )

    if path == SEARCH_ROUTE:
        mode = params.get("mode", "home")
        if mode == "export" and BodyRegistry.has_export():
            tiles_container = BodyRegistry.get_export()
        elif BodyRegistry.has_home():
            tiles_container = BodyRegistry.get_home()
        else:
            return _build_route_view(HOME_ROUTE, page)
        _configure_deep_chrome(page)
        search = SearchScreen(page, tiles_container)
        return ft.View(
            route=full_route,
            controls=[build_search_body(page, search)],
            horizontal_alignment=AppChrome.get_horizontal_alignment(),
            vertical_alignment=ft.MainAxisAlignment.START,
            padding=ft.Padding.all(0),
            bgcolor=AppTheme.current_bgcolor(),
        )

    body = TilesContainer(page)
    BodyRegistry.set_home(body)
    return _build_shell_view(
        page,
        HOME_ROUTE,
        [build_shell_body(page, body)],
        vertical_alignment=ft.MainAxisAlignment.START,
    )


def _resolve_path(path: str) -> str:
    return path if path in KNOWN_ROUTES else HOME_ROUTE


def _normalize_full_route(full_route: str) -> str:
    path = _resolve_path(route_path(full_route))
    if path != route_path(full_route):
        return path
    return full_route


async def reset_to_route(page: ft.Page, full_route: str):
    full_route = _normalize_full_route(full_route)

    LayoutMetricsStore.refresh(page)
    _update_drawer_selection(full_route)
    _detach_shared_chrome_from_views(page)
    page.views[:] = [_build_route_view(full_route, page)]
    await page.push_route(full_route)
    AppTheme.apply_to_page(page)
    page.update()


async def push_route_view(page: ft.Page, full_route: str):
    full_route = _normalize_full_route(full_route)
    path = route_path(full_route)

    if path not in DEEP_ROUTES:
        await reset_to_route(page, full_route)
        return

    if _route_already_active(page, full_route):
        AppTheme.apply_to_page(page)
        page.update()
        return

    LayoutMetricsStore.refresh(page)
    page.views.append(_build_route_view(full_route, page))
    await page.push_route(full_route)
    AppTheme.apply_to_page(page)
    page.update()


async def pop_route_view(page: ft.Page):
    if len(page.views) <= 1:
        await reset_to_route(page, HOME_ROUTE)
        return

    page.views.pop()
    top_view = page.views[-1]
    full_route = top_view.route or HOME_ROUTE

    _restore_active_view_state(page, full_route)
    AppTheme.apply_to_page(page)
    await page.push_route(full_route)
    page.update()


async def initialize_routes(page: ft.Page):
    await reset_to_route(page, HOME_ROUTE)


def handle_route_change(e: ft.RouteChangeEvent):
    page = e.page
    full_route = page.route or HOME_ROUTE
    path = _resolve_path(route_path(full_route))

    if _route_already_active(page, full_route):
        _update_drawer_selection(full_route)
        _sync_chrome_for_route(full_route, page)
        _apply_layout_for_route(page, path)
        AppTheme.apply_to_page(page)
        page.update()
        return

    if path in DRAWER_ROUTES:
        page.run_task(reset_to_route, page, full_route)
    elif path in DEEP_ROUTES:
        page.run_task(push_route_view, page, full_route)


async def handle_view_pop(e: ft.ViewPopEvent):
    page = e.page
    if not page.views:
        await initialize_routes(page)
        return

    top_view = page.views[-1]
    full_route = top_view.route or HOME_ROUTE

    _restore_active_view_state(page, full_route)
    AppTheme.apply_to_page(page)
    if not routes_match(page.route, full_route):
        await page.push_route(full_route)
    page.update()


def handle_page_resize(e: ft.ControlEvent):
    page = e.page
    _apply_layout_for_route(page, route_path(page.route or HOME_ROUTE))
    AppTheme.apply_to_page(page)
