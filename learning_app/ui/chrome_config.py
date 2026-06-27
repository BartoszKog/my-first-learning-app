from dataclasses import dataclass

from learning_app.ui.route_paths import HOME_ROUTE, IMPORT_EXPORT_ROUTE, INFO_ROUTE, SETTINGS_ROUTE


@dataclass(frozen=True)
class ShellChromeConfig:
    appbar_title: str
    appbar_menu_leading: bool = False
    bottom_appbar_visible: bool = True
    fab_visible: bool = True
    search_button_visible: bool = True
    bottom_appbar_height: int = 80


SHELL_CHROME: dict[str, ShellChromeConfig] = {
    HOME_ROUTE: ShellChromeConfig(appbar_title="__greeting__"),
    IMPORT_EXPORT_ROUTE: ShellChromeConfig(
        appbar_title="Import/Export",
        fab_visible=False,
        search_button_visible=False,
    ),
    SETTINGS_ROUTE: ShellChromeConfig(
        appbar_title="Settings",
        appbar_menu_leading=True,
        bottom_appbar_visible=False,
        fab_visible=False,
        search_button_visible=False,
    ),
    INFO_ROUTE: ShellChromeConfig(
        appbar_title="Information",
        appbar_menu_leading=True,
        bottom_appbar_visible=False,
        fab_visible=False,
        search_button_visible=False,
    ),
}
