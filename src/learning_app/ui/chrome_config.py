"""Declarative visibility and title settings for shared shell chrome.

``SHELL_CHROME`` maps each shell route path to its ``ShellChromeConfig``.
Deep routes omit chrome and are not present in this mapping.
"""

from dataclasses import dataclass

from learning_app.ui.route_paths import HOME_ROUTE, IMPORT_EXPORT_ROUTE, INFO_ROUTE, SETTINGS_ROUTE


@dataclass(frozen=True)
class ShellChromeConfig:
    """Configure shared chrome for a shell route.

    Attributes:
        appbar_title: Text displayed in the app bar. The ``"__greeting__"``
            sentinel requests a generated greeting.
        appbar_menu_leading: Whether the app bar shows the drawer menu button.
        bottom_appbar_visible: Whether the shared bottom app bar is visible.
        fab_visible: Whether the shared floating action button is visible.
        search_button_visible: Whether the bottom app bar's search action is
            visible.
        bottom_appbar_height: Content height of the bottom app bar in logical
            pixels (menu/search row). The on-screen bar may be taller once the
            system navigation inset is applied by Flutter's built-in SafeArea.
    """

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
