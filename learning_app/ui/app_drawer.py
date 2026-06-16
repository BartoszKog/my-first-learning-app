import flet as ft

from learning_app.ui.components.tiles_container import TilesContainer
from learning_app.ui.page_properties import PageProperties
from learning_app.ui.screens.import_export_control import ImportExportControl
from learning_app.ui.screens.info_control import InfoControl
from learning_app.ui.screens.settings_control import SettingsControl


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

    def __there_is_instance_of(self, control_class):
        return sum([isinstance(control, control_class) for control in self._host_page.controls]) > 0

    async def __handle_change(self, e: ft.ControlEvent):
        if PageProperties.is_navigation_disabled():
            return

        page = self._host_page

        if self.selected_index == 0:
            if not self.__there_is_instance_of(TilesContainer):
                page.controls.clear()
                TilesContainer.back_to_main_menu(e)

        elif self.selected_index == 1:
            if not self.__there_is_instance_of(ImportExportControl):
                page.controls.clear()
                page.add(ImportExportControl())

        elif self.selected_index == 2:
            if not self.__there_is_instance_of(SettingsControl):
                page.controls.clear()
                page.add(SettingsControl(page))

        elif self.selected_index == 3:
            if not self.__there_is_instance_of(InfoControl):
                page.controls.clear()
                page.add(InfoControl())

        await page.close_drawer()
