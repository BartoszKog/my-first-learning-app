import flet as ft

from learning_app.data.file_path_manager import FilePathManager
from learning_app.ui.app_drawer import AppDrawer
from learning_app.ui.page_functions import set_theme_from_bgcolor
from learning_app.ui.navigation import go_create_set, go_search
from learning_app.ui.router import (
    handle_page_resize,
    handle_route_change,
    handle_view_pop,
    initialize_routes,
    is_current_route,
)
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.app_chrome import AppChrome
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.app_session import AppSession
from learning_app.ui.preferences import get_shared_preferences
from learning_app.ui.routes import IMPORT_EXPORT_ROUTE
from learning_app.utils.greetings import Greetings

# dictionary with colors
colors = {
    "floating_action_button_bg": ft.Colors.TEAL_800,
    "appbar_bg": ft.Colors.TEAL_800,
    "bottom_appbar_bg": ft.Colors.TEAL_900,
    "icon_color": ft.Colors.WHITE,
    "font_color": ft.Colors.WHITE,
}


async def main(page: ft.Page):
    # Initialize FilePathManager at the beginning of the application
    FilePathManager.initialize()

    page.padding = ft.Padding(left=25, right=25, top=0, bottom=0)

    AppSession.set_page(page)
    AppSession.get_export_csv_picker()

    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    page.title = "Leaning App"

    drawer = AppDrawer(page)
    page.drawer = drawer
    AppChrome.set_drawer(drawer)

    def on_add_click(e):
        LayoutMetricsStore.refresh(page)
        go_create_set(page)

    async def on_menu_click(e):
        await page.show_drawer()

    async def on_appbar_menu_click(e):
        await page.show_drawer()

    page.on_resized = handle_page_resize

    def on_search_click(e):
        if is_current_route(page, IMPORT_EXPORT_ROUTE):
            go_search(page, mode="export")
        else:
            go_search(page, mode="home")

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=on_add_click,
        bgcolor=colors["floating_action_button_bg"],
        foreground_color=colors["icon_color"],
    )
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED

    bottom_menu_button = ft.IconButton(icon=ft.Icons.MENU, icon_color=colors["icon_color"], on_click=on_menu_click)
    search_button = ft.IconButton(icon=ft.Icons.SEARCH, icon_color=colors["icon_color"], on_click=on_search_click)
    appbar_menu_button = ft.IconButton(icon=ft.Icons.MENU, icon_color=colors["icon_color"], on_click=on_appbar_menu_click)

    page.appbar = ft.AppBar(
        title=ft.Text(Greetings.get_greeting(), size=40, weight=ft.FontWeight.BOLD, color=colors["font_color"]),
        center_title=True,
        bgcolor=colors["appbar_bg"],
        toolbar_height=100,
        automatically_imply_leading=False,
    )
    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=colors["bottom_appbar_bg"],
        height=80,
        shape=ft.CircularRectangleNotchShape(),
        content=ft.Row(
            controls=[
                bottom_menu_button,
                ft.Container(expand=True),
                search_button,
            ]
        ),
    )

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    AppChrome.register(
        appbar=page.appbar,
        bottom_appbar=page.bottom_appbar,
        floating_action_button=page.floating_action_button,
        floating_action_button_location=page.floating_action_button_location,
        horizontal_alignment=page.horizontal_alignment,
        vertical_alignment=page.vertical_alignment,
        appbar_menu_button=appbar_menu_button,
        search_button=search_button,
    )

    storage = get_shared_preferences()
    if not await storage.contains_key("light_theme_bgcolor"):
        await storage.set("light_theme_bgcolor", ft.Colors.SURFACE.value)
        await storage.set("light_theme_slider_value", "2")
    if not await storage.contains_key("dark_theme_bgcolor"):
        await storage.set("dark_theme_bgcolor", ft.Colors.SURFACE.value)
        await storage.set("dark_theme_slider_value", "2")
    if not await storage.contains_key("theme_mode"):
        await storage.set("theme_mode", ft.ThemeMode.DARK.value)

    if await storage.get("theme_mode") == ft.ThemeMode.LIGHT.value:
        page.theme_mode = ft.ThemeMode.LIGHT
        set_theme_from_bgcolor(page, await storage.get("light_theme_bgcolor"))
    else:
        page.theme_mode = ft.ThemeMode.DARK
        set_theme_from_bgcolor(page, await storage.get("dark_theme_bgcolor"))

    await AppTheme.load_from_preferences()
    AppTheme.sync_from_page(page)
    await initialize_routes(page)
