import flet as ft

from learning_app.ui.app_session import AppSession
from learning_app.ui.navigation import navigate_to_async
from learning_app.ui.route_url import route_path
from learning_app.ui.routes import DRAWER_ROUTES


class AppDrawer(ft.NavigationDrawer):
    def __init__(self, host_page: ft.Page):
        self._host_page = host_page
        super().__init__(
            tile_padding=ft.Padding(top=10),
            on_change=self.__handle_change,
            controls=[
                ft.Container(height=24),
                ft.NavigationDrawerDestination(
                    label="Learning sets",
                    icon=ft.Icons.BOOK,
                ),
                ft.Divider(thickness=2),
                ft.NavigationDrawerDestination(
                    label="Importing and exporting",
                    icon=ft.Icons.IMPORT_EXPORT,
                ),
                ft.NavigationDrawerDestination(
                    label="Settings",
                    icon=ft.Icons.SETTINGS,
                ),
                ft.Divider(thickness=2),
                ft.NavigationDrawerDestination(
                    label="Info",
                    icon=ft.Icons.INFO,
                ),
            ],
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
