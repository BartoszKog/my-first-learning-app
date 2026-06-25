import flet as ft


class AppChrome:
    _appbar: ft.AppBar | None = None
    _bottom_appbar: ft.BottomAppBar | None = None
    _floating_action_button: ft.FloatingActionButton | None = None
    _floating_action_button_location: ft.FloatingActionButtonLocation | None = None
    _horizontal_alignment: ft.CrossAxisAlignment | None = None
    _vertical_alignment: ft.MainAxisAlignment | None = None
    _appbar_menu_button: ft.IconButton | None = None
    _search_button: ft.IconButton | None = None
    _drawer: ft.NavigationDrawer | None = None

    @classmethod
    def register(
        cls,
        *,
        appbar: ft.AppBar,
        bottom_appbar: ft.BottomAppBar,
        floating_action_button: ft.FloatingActionButton,
        floating_action_button_location: ft.FloatingActionButtonLocation,
        horizontal_alignment: ft.CrossAxisAlignment,
        vertical_alignment: ft.MainAxisAlignment,
        appbar_menu_button: ft.IconButton,
        search_button: ft.IconButton,
    ):
        cls._appbar = appbar
        cls._bottom_appbar = bottom_appbar
        cls._floating_action_button = floating_action_button
        cls._floating_action_button_location = floating_action_button_location
        cls._horizontal_alignment = horizontal_alignment
        cls._vertical_alignment = vertical_alignment
        cls._appbar_menu_button = appbar_menu_button
        cls._search_button = search_button

    @classmethod
    def set_drawer(cls, drawer: ft.NavigationDrawer):
        cls._drawer = drawer

    @classmethod
    def get_appbar(cls) -> ft.AppBar:
        assert cls._appbar is not None, "App chrome is not registered"
        return cls._appbar

    @classmethod
    def get_bottom_appbar(cls) -> ft.BottomAppBar:
        assert cls._bottom_appbar is not None, "App chrome is not registered"
        return cls._bottom_appbar

    @classmethod
    def get_floating_action_button(cls) -> ft.FloatingActionButton:
        assert cls._floating_action_button is not None, "App chrome is not registered"
        return cls._floating_action_button

    @classmethod
    def get_floating_action_button_location(cls) -> ft.FloatingActionButtonLocation:
        assert cls._floating_action_button_location is not None, "App chrome is not registered"
        return cls._floating_action_button_location

    @classmethod
    def get_horizontal_alignment(cls) -> ft.CrossAxisAlignment:
        assert cls._horizontal_alignment is not None, "App chrome is not registered"
        return cls._horizontal_alignment

    @classmethod
    def get_vertical_alignment(cls) -> ft.MainAxisAlignment:
        assert cls._vertical_alignment is not None, "App chrome is not registered"
        return cls._vertical_alignment

    @classmethod
    def get_appbar_menu_button(cls) -> ft.IconButton:
        assert cls._appbar_menu_button is not None, "App chrome is not registered"
        return cls._appbar_menu_button

    @classmethod
    def get_search_button(cls) -> ft.IconButton:
        assert cls._search_button is not None, "App chrome is not registered"
        return cls._search_button

    @classmethod
    def get_drawer(cls) -> ft.NavigationDrawer:
        assert cls._drawer is not None, "App drawer is not set"
        return cls._drawer

    @classmethod
    def has_drawer(cls) -> bool:
        return cls._drawer is not None
