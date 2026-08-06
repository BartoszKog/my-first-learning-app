"""High-level navigation commands for route-aware UI controls."""

import flet as ft

from learning_app.ui.route_url import build_route
from learning_app.ui.route_paths import SET_EDIT_ROUTE


def navigate_to(page: ft.Page, route: str, **params: object) -> None:
    """Replace the view stack with a route in a scheduled page task.

    Args:
        page: Page whose route stack should be replaced.
        route: Route path without query parameters.
        **params: Query parameters to encode in the route URL. Values set to
            ``None`` are omitted.
    """
    from learning_app.ui.router import reset_to_route

    page.run_task(reset_to_route, page, build_route(route, **params))


async def navigate_to_async(page: ft.Page, route: str, **params: object) -> None:
    """Replace the view stack with a route and wait for completion.

    Args:
        page: Page whose route stack should be replaced.
        route: Route path without query parameters.
        **params: Query parameters to encode in the route URL. Values set to
            ``None`` are omitted.
    """
    from learning_app.ui.router import reset_to_route

    await reset_to_route(page, build_route(route, **params))


def push_view(page: ft.Page, route: str, **params: object) -> None:
    """Push a deep-route view in a scheduled page task.

    Non-deep routes are handled by the router as stack replacements.

    Args:
        page: Page whose route stack should be updated.
        route: Route path without query parameters.
        **params: Query parameters to encode in the route URL. Values set to
            ``None`` are omitted.
    """
    from learning_app.ui.router import push_route_view

    page.run_task(push_route_view, page, build_route(route, **params))


def go_back(page: ft.Page) -> None:
    """Pop the active route view, or close in-place search when it is open.

    Args:
        page: Page whose active view should be popped.
    """
    from learning_app.ui.inplace_search import close_inplace_search, is_inplace_search_active
    from learning_app.ui.router import pop_route_view

    if is_inplace_search_active(page):
        close_inplace_search(page)
        return

    page.run_task(pop_route_view, page)


def reanchor_edit_on_home(page: ft.Page, file_name: str) -> None:
    """Rebuild Home under the active edit view after creating a new set.

    Drops intermediate views such as create-set and refreshes the home tile
    catalog so Back / system back land on an up-to-date list.

    Args:
        page: Page whose view stack should be rewritten.
        file_name: Set file used to build the canonical edit route URL.
    """
    from learning_app.ui.router import reanchor_active_deep_view_on_home

    page.run_task(
        reanchor_active_deep_view_on_home,
        page,
        build_route(SET_EDIT_ROUTE, file=file_name),
    )


def go_search(page: ft.Page, mode: str = "home") -> None:
    """Open in-place search over the selected tile collection.

    Search UI is inserted above the tiles in their existing shell column so the
    tile body is never reparented (which breaks the sort dropdown after return).

    When the chosen body has no content tiles, the call returns without changes.

    Args:
        page: Page on which to open search.
        mode: Tile collection to search. ``"export"`` selects the export
            collection; every other value selects the home collection.
    """
    from learning_app.ui.body_registry import BodyRegistry
    from learning_app.ui.inplace_search import ensure_inplace_search

    body = BodyRegistry.get_export() if mode == "export" else BodyRegistry.get_home()
    if not body.has_content_tiles():
        return
    ensure_inplace_search(page, body)
