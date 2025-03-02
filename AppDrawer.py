import flet as ft
from PageProperties import PageProperties
from TilesContainer import TilesContainer
from SettingsControl import SettingsControl
from InfoControl import InfoControl
from ImportExportControl import ImportExportControl

class AppDrawer(ft.NavigationDrawer):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.tile_padding = 10
        self.on_change = self.__handle_change
        self.controls = [
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
        ]

    def __there_is_instance_of(self, control_class):
        return sum([isinstance(control, control_class) for control in self.page.controls]) > 0

    def __handle_change(self, e: ft.ControlEvent):
        if self.selected_index == 0: # Learning sets
            if not self.__there_is_instance_of(TilesContainer):
                self.page.controls.clear()
                body: TilesContainer = PageProperties.get_body()
                body.back_to_main_menu(e)
        
        elif self.selected_index == 1: # Importing and exporting
            if not self.__there_is_instance_of(ImportExportControl):
                self.page.controls.clear()
                self.page.add(ImportExportControl())        
        
        
        elif self.selected_index == 2: # settings
            if not self.__there_is_instance_of(SettingsControl):
                self.page.controls.clear()
                self.page.add(SettingsControl(self.page))
                
        elif self.selected_index == 3: # info
            if not self.__there_is_instance_of(InfoControl):
                self.page.controls.clear()
                self.page.add(InfoControl())