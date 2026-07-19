"""Shared navigation drawer for Shell destinations."""

import flet as ft

from learning_app.ui.app_session import AppSession
from learning_app.ui.navigation import navigate_to_async
from learning_app.ui.route_registry import DRAWER_ROUTES, build_drawer_controls
from learning_app.ui.route_url import route_path


class AppDrawer(ft.NavigationDrawer):
    """Navigation drawer built from ``DRAWER_ROUTES`` / ``build_drawer_controls``.

    On selection, closes the drawer and navigates to the matching Shell route
    unless that route is already active. Honors
    ``AppSession.is_navigation_disabled`` so import/export and similar flows
    can lock drawer navigation. Registered on ``AppChrome`` at startup.
    """

    def __init__(self, host_page: ft.Page):
        """Create the drawer bound to the application page.

        Args:
            host_page: Page used for close-drawer and navigation calls.
        """
        self._host_page = host_page
        super().__init__(
            tile_padding=ft.Padding(top=10),
            on_change=self.__handle_change,
            controls=build_drawer_controls(),
        )

    async def __handle_change(self, e: ft.ControlEvent):
        if AppSession.is_navigation_disabled():
            return

        page = self._host_page
        target_route = DRAWER_ROUTES[self.selected_index]

        if route_path(page.route) == target_route:
            await page.close_drawer()
            return

        await page.close_drawer()
        await navigate_to_async(page, target_route)
