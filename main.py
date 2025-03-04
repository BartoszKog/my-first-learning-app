import flet as ft
from TilesContainer import TilesContainer
from CreateSetMenu import CreateSetMenu
from AppDrawer import AppDrawer
from page_functions import quit_main_menu, is_instance_in_the_page, set_theme_from_bgcolor
from Greetings import Greetings
from SearchControl import SearchControl
from PageProperties import PageProperties # need in on_resized in isinstance
from BaseWordField import BaseWordField # need in on_resized in isinstance
from EditSetMenu import EditSetMenu # need in on_resized in isinstance
from ImportExportControl import ImportExportControl # check if it is instance of ImportExportControl in logic of search button
# dictionary with colors
colors = {
    "floating_action_button_bg": ft.Colors.TEAL_800,
    "appbar_bg": ft.Colors.TEAL_800,
    "bottom_appbar_bg": ft.Colors.TEAL_900,
    "icon_color": ft.Colors.WHITE,
    "font_color": ft.Colors.WHITE,
}


def main(page: ft.Page):
    page.padding = ft.Padding(left=25, right=25, top=0, bottom=0)
    page.window.width = 500
    page.window.height = 900
    page.window.min_width = 500
    page.window.min_height = 700
    page.window.max_width = 900
    page.window.max_height = 1000
    PageProperties.set_width_height_from_page(page)
    PageProperties.create_export_csv_picker(page)
    PageProperties.set_page(page)
    
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # set default background color and theme to client storage if it is not set
    if not page.client_storage.contains_key("light_theme_bgcolor"):
        page.client_storage.set("light_theme_bgcolor", ft.Colors.SURFACE)
        page.client_storage.set("light_theme_slider_value", 2) # 2 corresponds to position of slider for default light theme
    if not page.client_storage.contains_key("dark_theme_bgcolor"):
        page.client_storage.set("dark_theme_bgcolor", ft.Colors.SURFACE)
        page.client_storage.set("dark_theme_slider_value", 2) # 2 corresponds to position of slider for default dark theme
    if not page.client_storage.contains_key("theme_mode"):
        # default theme mode
        page.client_storage.set("theme_mode", ft.ThemeMode.DARK.value)
        
    # set theme mode and background color from client storage
    if page.client_storage.get("theme_mode") == ft.ThemeMode.LIGHT.value:
        page.theme_mode = ft.ThemeMode.LIGHT
        set_theme_from_bgcolor(page, page.client_storage.get("light_theme_bgcolor"))
    else:
        page.theme_mode = ft.ThemeMode.DARK
        set_theme_from_bgcolor(page, page.client_storage.get("dark_theme_bgcolor"))
    
    PageProperties.set_slider_and_bgcolor_values_from_page(page)
    PageProperties.set_theme_from_page(page)

    page.title = "Leaning App"
    
    drawer = AppDrawer(page)
    
    body = TilesContainer(page)
    PageProperties.set_body(body)
    PageProperties.set_drawer(drawer)

    def on_add_click(e):
        quit_main_menu(e)
        PageProperties.set_width_height_from_page(page)
        page.add(CreateSetMenu(width=PageProperties.width*0.8))

    def on_menu_click(e):
        # Logic for menu button
        page.open(drawer)
        
    def resize_page(e):
        # check that it is instance of TilesContainer in controls of page
        if isinstance(e.page.controls[0], TilesContainer):
            scale_factor = 0.65
            # Check if it is instance of SearchControl in controls of page
            #if sum([isinstance(control, SearchControl) for control in e.page.controls]) > 0 and PageProperties.platform == ft.PagePlatform.WINDOWS:
            if is_instance_in_the_page(e.page, SearchControl) and PageProperties.platform == ft.PagePlatform.WINDOWS:
                scale_factor = 0.85
            
            e.page.controls[0].scale_height_to_page(e.page, scale_factor)
        elif isinstance(e.page.controls[0], BaseWordField):
            e.page.controls[0].change_height(e.page.height*0.7)
        elif isinstance(e.page.controls[0], EditSetMenu):
            e.page.controls[0].change_height(e.page.height*0.8)
        PageProperties.set_width_height_from_page(e.page)
        
    page.on_resized = resize_page

    def on_search_click(e):
        # Logic for search button
        def hide_appbar_elements():
            page.bottom_appbar.visible = False
            page.floating_action_button.visible = False
            page.appbar.visible = False
            page.padding = 0
        
        if is_instance_in_the_page(page, ImportExportControl):
            export_body = PageProperties.get_export_body()
            if not export_body.has_content_tiles():
                return
            hide_appbar_elements()
            export_search_control = SearchControl(page, export_body)
            PageProperties.set_current_search_control_involved_export_mode(export_search_control)
            page.add(export_search_control)
        else: # if it is not instance of ImportExportControl
            if not body.has_content_tiles():
                return
            hide_appbar_elements()
            page.add(SearchControl(page, body))
            

    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=on_add_click, 
        bgcolor=colors["floating_action_button_bg"],
        foreground_color=colors["icon_color"],
    )
    page.floating_action_button_location = ft.FloatingActionButtonLocation.CENTER_DOCKED

    page.appbar = ft.AppBar(
        title=ft.Text(Greetings.get_greeting(), size=40, weight=ft.FontWeight.BOLD, color=colors["font_color"]),
        center_title=True,
        bgcolor=colors["appbar_bg"],
        toolbar_height=100,
        automatically_imply_leading=False,
    )
    page.bottom_appbar = ft.BottomAppBar(
        bgcolor=colors["bottom_appbar_bg"],
        shape=ft.NotchShape.CIRCULAR,
        content=ft.Row(
            controls=[
                ft.IconButton(icon=ft.Icons.MENU, icon_color=colors["icon_color"], on_click=on_menu_click),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.Icons.SEARCH, icon_color=colors["icon_color"], on_click=on_search_click),
            ]
        ),
    )

    page.add(body)

ft.app(target=main)