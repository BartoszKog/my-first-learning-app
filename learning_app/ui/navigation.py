import flet as ft

from learning_app.ui.route_url import build_route
from learning_app.ui.route_paths import SEARCH_ROUTE


def navigate_to(page: ft.Page, route: str, **params):
    from learning_app.ui.router import reset_to_route

    page.run_task(reset_to_route, page, build_route(route, **params))


async def navigate_to_async(page: ft.Page, route: str, **params):
    from learning_app.ui.router import reset_to_route

    await reset_to_route(page, build_route(route, **params))


def push_view(page: ft.Page, route: str, **params):
    from learning_app.ui.router import push_route_view

    page.run_task(push_route_view, page, build_route(route, **params))


def go_back(page: ft.Page):
    from learning_app.ui.router import pop_route_view

    page.run_task(pop_route_view, page)


def go_search(page: ft.Page, mode: str = "home"):
    from learning_app.ui.body_registry import BodyRegistry

    body = BodyRegistry.get_export() if mode == "export" else BodyRegistry.get_home()
    if not body.has_content_tiles():
        return
    push_view(page, SEARCH_ROUTE, mode=mode)
