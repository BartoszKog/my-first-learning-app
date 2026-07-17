"""Coordinate route views, shared chrome, and responsive layout state."""

import flet as ft

from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.body_registry import BodyRegistry
from learning_app.ui.chrome_config import SHELL_CHROME
from learning_app.ui.layout_host import (
    build_bottom_inset_shell_body,
    build_deep_body,
    build_search_body,
    build_shell_body,
    sync_body_column_width,
)
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore
from learning_app.ui.route_url import route_params, route_path, routes_match
from learning_app.ui.route_paths import HOME_ROUTE, IMPORT_EXPORT_ROUTE, SET_LEARN_ROUTE
from learning_app.ui.route_registry import (
    BodyWrapperKind,
    DEEP_ROUTES,
    DRAWER_ROUTES,
    KNOWN_ROUTES,
    LayoutKind,
    ROUTE_TO_DRAWER_INDEX,
    RouteDef,
    RouteKind,
    get_route,
)
from learning_app.ui.routable_screen import call_apply_layout, find_routable_in_active_view
from learning_app.ui.components.word_definition_field import WordDefinitionField
from learning_app.ui.components.word_fields import WordFields
from learning_app.utils.greetings import Greetings


def is_current_route(page: ft.Page, route: str) -> bool:
    """Return whether the page's current route path matches a path.

    Query parameters on ``page.route`` are ignored.

    Args:
        page: Page whose current route should be inspected.
        route: Canonical route path to compare.

    Returns:
        ``True`` when the current route path equals ``route``.
    """
    return route_path(page.route) == route


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


def _apply_routable_layout(
    page: ft.Page,
    metrics: LayoutMetrics,
    *,
    sync: str,
    control_type: type | tuple[type, ...] | None = None,
):
    if sync == "shell":
        _sync_shell_body_layout(page)
    elif sync == "deep":
        _sync_deep_body_layout(page)

    control = find_routable_in_active_view(page, control_type=control_type)
    call_apply_layout(control, metrics)


def _layout_home(_page: ft.Page, _route_def):
    _apply_home_flex_layout(_page)


def _layout_routable_shell(page: ft.Page, route_def, *, control_type=None):
    metrics = LayoutMetricsStore.refresh(page)
    _apply_routable_layout(page, metrics, sync="shell", control_type=control_type)


def _layout_import_export(page: ft.Page, _route_def):
    _layout_routable_shell(page, _route_def)


def _layout_search(page: ft.Page, route_def):
    _layout_routable_shell(page, route_def)


def _layout_shell(page: ft.Page, route_def):
    _layout_routable_shell(page, route_def, control_type=route_def.shell_layout_control)


def _layout_deep_form(page: ft.Page, _route_def):
    metrics = LayoutMetricsStore.refresh(page)
    _apply_routable_layout(page, metrics, sync="deep")


_LAYOUT_DISPATCH = {
    LayoutKind.HOME: _layout_home,
    LayoutKind.IMPORT_EXPORT: _layout_import_export,
    LayoutKind.SEARCH: _layout_search,
    LayoutKind.SHELL: _layout_shell,
    LayoutKind.DEEP_FORM: _layout_deep_form,
}


def _apply_layout_for_route(page: ft.Page, path: str):
    route_def = get_route(path)
    if route_def is None:
        return
    handler = _LAYOUT_DISPATCH.get(route_def.layout_kind)
    if handler is not None:
        handler(page, route_def)


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

    control = find_routable_in_active_view(page, control_type=(WordFields, WordDefinitionField))
    if control is None:
        return

    control.menu_control.refresh_content()
    control.words.refresh()
    if call_apply_layout(control):
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


def _wrap_shell_body(
    page: ft.Page,
    controls: list[ft.Control],
    _route_def: RouteDef,
) -> ft.Control:
    return build_shell_body(page, *controls)


def _wrap_bottom_inset_shell_body(
    page: ft.Page,
    controls: list[ft.Control],
    _route_def: RouteDef,
) -> ft.Control:
    return build_bottom_inset_shell_body(page, *controls)


def _wrap_deep_body(
    page: ft.Page,
    controls: list[ft.Control],
    route_def: RouteDef,
) -> ft.Control:
    return build_deep_body(
        page,
        *controls,
        content_alignment=route_def.body_content_alignment,
    )


def _wrap_search_body(
    page: ft.Page,
    controls: list[ft.Control],
    _route_def: RouteDef,
) -> ft.Control:
    return build_search_body(page, *controls)


_BODY_WRAPPER_DISPATCH = {
    BodyWrapperKind.SHELL: _wrap_shell_body,
    BodyWrapperKind.BOTTOM_INSET_SHELL: _wrap_bottom_inset_shell_body,
    BodyWrapperKind.DEEP: _wrap_deep_body,
    BodyWrapperKind.SEARCH: _wrap_search_body,
}


def _wrap_route_controls(
    page: ft.Page,
    controls: list[ft.Control],
    route_def: RouteDef,
) -> list[ft.Control]:
    wrapper = _BODY_WRAPPER_DISPATCH[route_def.body_wrapper]
    return [wrapper(page, controls, route_def)]


def _build_route_view(full_route: str, page: ft.Page) -> ft.View:
    path = route_path(full_route)
    params = route_params(full_route)
    route_def = get_route(path)

    if route_def is None:
        return _build_route_view(HOME_ROUTE, page)

    controls = route_def.build_factory(page, params)
    if controls is None:
        fallback = route_def.fallback_path or HOME_ROUTE
        return _build_route_view(fallback, page)

    wrapped_controls = _wrap_route_controls(page, controls, route_def)

    if route_def.kind is RouteKind.DEEP:
        _configure_deep_chrome(page)
        if route_def.body_wrapper is BodyWrapperKind.SEARCH:
            return ft.View(
                route=full_route,
                controls=wrapped_controls,
                horizontal_alignment=AppChrome.get_horizontal_alignment(),
                vertical_alignment=ft.MainAxisAlignment.START,
                padding=ft.Padding.all(0),
                bgcolor=AppTheme.current_bgcolor(),
            )
        return _build_deep_view(
            page,
            full_route,
            wrapped_controls,
            vertical_alignment=route_def.vertical_alignment,
        )

    return _build_shell_view(
        page,
        full_route,
        wrapped_controls,
        vertical_alignment=route_def.vertical_alignment,
    )


def _resolve_path(path: str) -> str:
    return path if path in KNOWN_ROUTES else HOME_ROUTE


def _normalize_full_route(full_route: str) -> str:
    path = _resolve_path(route_path(full_route))
    if path != route_path(full_route):
        return path
    return full_route


async def reset_to_route(page: ft.Page, full_route: str):
    """Replace the view stack with one normalized route.

    Unknown paths resolve to the home route. The operation rebuilds the target
    view, updates the browser/page route, reapplies the theme, and refreshes the
    page.

    Args:
        page: Page whose view stack should be replaced.
        full_route: Route path with optional encoded query parameters.
    """
    full_route = _normalize_full_route(full_route)

    LayoutMetricsStore.refresh(page)
    _update_drawer_selection(full_route)
    _detach_shared_chrome_from_views(page)
    page.views[:] = [_build_route_view(full_route, page)]
    await page.push_route(full_route)
    AppTheme.apply_to_page(page)
    page.update()


async def push_route_view(page: ft.Page, full_route: str):
    """Push a normalized deep route or reset to a shell route.

    An already-active complete route is not duplicated. Unknown routes and
    registered shell routes are handled as stack replacements.

    Args:
        page: Page whose view stack should be updated.
        full_route: Route path with optional encoded query parameters.
    """
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
    """Remove the active view and restore state for the revealed route.

    When no previous view exists, the page is reset to the home route.

    Args:
        page: Page whose active route view should be removed.
    """
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
    """Initialize a page with the home route.

    Args:
        page: Page whose route stack should be initialized.
    """
    await reset_to_route(page, HOME_ROUTE)


def _index_of_route_in_views(page: ft.Page, full_route: str) -> int | None:
    for index, view in enumerate(page.views):
        if routes_match(view.route, full_route):
            return index
    return None


def handle_route_change(e: ft.RouteChangeEvent):
    """Synchronize or schedule navigation after a Flet route change.

    Active routes are refreshed in place. Routes already present below the top
    of the view stack (typical browser back/forward) pop down to that view
    instead of pushing a duplicate. Drawer routes replace the stack, and new
    deep routes are pushed above the active shell view.

    Args:
        e: Route-change event containing the affected page.
    """
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

    # Browser history moved to a route that is already under the top view.
    existing_index = _index_of_route_in_views(page, full_route)
    if existing_index is not None:
        del page.views[existing_index + 1 :]
        _restore_active_view_state(page, full_route)
        AppTheme.apply_to_page(page)
        page.update()
        return

    if path in DRAWER_ROUTES:
        page.run_task(reset_to_route, page, full_route)
    elif path in DEEP_ROUTES:
        page.run_task(push_route_view, page, full_route)


async def handle_view_pop(e: ft.ViewPopEvent):
    """Restore route state after Flet removes a view.

    Args:
        e: View-pop event containing the affected page.
    """
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
    """Reapply route layout and theme after a page resize.

    Args:
        e: Resize event containing the affected page.
    """
    page = e.page
    _apply_layout_for_route(page, route_path(page.route or HOME_ROUTE))
    AppTheme.apply_to_page(page)
