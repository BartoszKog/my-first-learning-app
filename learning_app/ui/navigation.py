import flet as ft

from learning_app.ui.body_registry import BodyRegistry
from learning_app.ui.route_url import build_route
from learning_app.ui.routes import (
    CREATE_SET_ROUTE,
    HOME_ROUTE,
    SEARCH_ROUTE,
    SET_EDIT_ROUTE,
    SET_LEARN_ROUTE,
    SET_LEARN_SESSION_ROUTE,
)


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


def go_home(page: ft.Page):
    navigate_to(page, HOME_ROUTE)


def go_create_set(page: ft.Page):
    push_view(page, CREATE_SET_ROUTE)


def go_edit_set(page: ft.Page, file_name: str, title=None, subtitle=None):
    push_view(page, SET_EDIT_ROUTE, file=file_name, title=title, subtitle=subtitle)


def go_learn_set(page: ft.Page, file_name: str):
    push_view(page, SET_LEARN_ROUTE, file=file_name)


def go_learn_session(page: ft.Page, file_name: str):
    push_view(page, SET_LEARN_SESSION_ROUTE, file=file_name)


def go_search(page: ft.Page, mode: str = "home"):
    if mode == "export":
        body = BodyRegistry.get_export()
    else:
        body = BodyRegistry.get_home()

    if not body.has_content_tiles():
        return

    push_view(page, SEARCH_ROUTE, mode=mode)


def go_back_from_search(page: ft.Page):
    go_back(page)
