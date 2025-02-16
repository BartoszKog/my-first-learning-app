import flet as ft
from PageProperties import PageProperties
 
class InfoControl(ft.Container):
    def __init__(self):
        super().__init__()
        self.drawer = PageProperties.get_drawer()
        
        # menu button
        self.menu_button = ft.IconButton(
            icon=ft.icons.MENU,
            on_click=self.on_menu_click,
            icon_color=ft.colors.WHITE
        )
    
    def on_menu_click(self, e):
        self.page.open(self.drawer)
        
    def did_mount(self):
        appbar = self.page.appbar
        appbar.leading = self.menu_button
        appbar.title.value = "Information"
        
        self.page.bottom_appbar.visible = False
        self.page.floating_action_button.visible = False
        self.page.update()
 
    def will_unmount(self):
        appbar = self.page.appbar
        appbar.leading = None
        self.page.update()