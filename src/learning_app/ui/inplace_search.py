"""In-place set search over the Home/Export tile column (no tile reparenting)."""

from __future__ import annotations

import flet as ft

from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.chrome_config import SHELL_CHROME
from learning_app.ui.components.search_control import SearchControl
from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.route_paths import HOME_ROUTE
from learning_app.ui.route_url import route_path
from learning_app.utils.greetings import Greetings

_PAGE_STATE_ATTR = "_inplace_search"


def is_inplace_search_active(page: ft.Page) -> bool:
    return getattr(page, _PAGE_STATE_ATTR, None) is not None


def _apply_search_chrome(search: SearchControl) -> None:
    """Keep the app bar as the search host; hide bottom bar and FAB."""
    appbar = AppChrome.get_appbar()
    appbar.visible = True
    appbar.leading = None
    appbar.title = search
    AppChrome.get_bottom_appbar().visible = False
    AppChrome.get_floating_action_button().visible = False


def sync_inplace_search_layout(page: ft.Page) -> None:
    """Keep SearchControl width aligned with tiles after open or resize."""
    state = getattr(page, _PAGE_STATE_ATTR, None)
    if not state:
        return
    search = state["control"]
    if not isinstance(search, SearchControl):
        return
    metrics = LayoutMetricsStore.refresh(page)
    search.apply_flex_layout(metrics)
    AppChrome.get_appbar().center_title = metrics.breakpoint != "compact"


def _restore_shell_chrome(page: ft.Page, full_route: str | None = None) -> None:
    """Restore Home/Export shell chrome after leaving in-place search."""
    from learning_app.ui.route_paths import IMPORT_EXPORT_ROUTE

    path = route_path(full_route or page.route or HOME_ROUTE)
    config = SHELL_CHROME.get(path)
    if config is None:
        return

    appbar = AppChrome.get_appbar()
    appbar.visible = True
    appbar.leading = AppChrome.get_appbar_menu_button() if config.appbar_menu_leading else None
    AppChrome.show_appbar_title(
        Greetings.get_greeting() if config.appbar_title == "__greeting__" else config.appbar_title
    )

    bottom_appbar = AppChrome.get_bottom_appbar()
    bottom_appbar.visible = config.bottom_appbar_visible
    if config.bottom_appbar_visible:
        AppChrome.set_bottom_appbar_height(config.bottom_appbar_height)
        # Import/Export enables search only on the Export tab; search opens from
        # that tab, so restore the button even though SHELL_CHROME defaults False.
        if path == IMPORT_EXPORT_ROUTE:
            AppChrome.get_search_button().visible = True
        else:
            AppChrome.get_search_button().visible = config.search_button_visible

    AppChrome.get_floating_action_button().visible = config.fab_visible


def _find_import_export_control(body: TilesContainer):
    """Walk parents to find ``ImportExportControl`` when searching export tiles."""
    from learning_app.ui.screens.import_export_control import ImportExportControl

    current = body.parent
    while current is not None:
        if isinstance(current, ImportExportControl):
            return current
        current = getattr(current, "parent", None)
    return None


def ensure_inplace_search(page: ft.Page, body: TilesContainer) -> bool:
    """Show SearchControl in the shared app bar without reparenting tiles.

    Returns:
        ``True`` when search UI was shown (or already active).
    """
    if is_inplace_search_active(page):
        return True

    def on_close(_e=None):
        close_inplace_search(page)

    search = SearchControl(page, body, on_close=on_close)
    body.trigger_searching_mode()
    _apply_search_chrome(search)

    import_export = _find_import_export_control(body) if body.export_mode else None
    if import_export is not None:
        import_export.set_tab_bar_visible(False)

    setattr(
        page,
        _PAGE_STATE_ATTR,
        {
            "control": search,
            "body": body,
            "route": page.route or HOME_ROUTE,
            "import_export": import_export,
        },
    )
    sync_inplace_search_layout(page)

    page.update()
    return True


def close_inplace_search(page: ft.Page) -> bool:
    """Remove in-place SearchControl and restore the sort bar. Returns True if closed."""
    state = getattr(page, _PAGE_STATE_ATTR, None)
    if not state:
        return False

    body: TilesContainer = state["body"]
    opened_from_route = state.get("route") or page.route or HOME_ROUTE
    import_export = state.get("import_export")

    if body.searching:
        body.turn_off_searching_mode()

    if import_export is not None:
        import_export.set_tab_bar_visible(True)

    setattr(page, _PAGE_STATE_ATTR, None)
    _restore_shell_chrome(page, opened_from_route)

    page.update()
    return True
