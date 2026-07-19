"""High-level navigation commands for route-aware UI controls."""

import flet as ft

from learning_app.ui.route_url import build_route
from learning_app.ui.route_paths import SEARCH_ROUTE


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
    """Pop the active route view in a scheduled page task.

    Args:
        page: Page whose active view should be popped.
    """
    from learning_app.ui.router import pop_route_view

    page.run_task(pop_route_view, page)


def go_search(page: ft.Page, mode: str = "home") -> None:
    """Open search for the selected tile collection when it has content.

    When the chosen body has no content tiles, the call returns without
    changing the route.

    Args:
        page: Page on which to open the search route.
        mode: Tile collection to search. ``"export"`` selects the export
            collection; every other value selects the home collection.
    """
    from learning_app.ui.body_registry import BodyRegistry

    body = BodyRegistry.get_export() if mode == "export" else BodyRegistry.get_home()
    if not body.has_content_tiles():
        return
    push_view(page, SEARCH_ROUTE, mode=mode)
