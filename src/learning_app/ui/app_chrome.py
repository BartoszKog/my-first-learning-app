"""Registry of shared Shell chrome controls created at startup."""

import flet as ft


class AppChrome:
    """Holds references to the shared AppBar, bottom bar, FAB, and drawer.

    ``app.py`` builds the controls once, then calls ``register`` and
    ``set_drawer``. The router applies ``SHELL_CHROME`` visibility and titles
    through these getters when entering Shell routes, and hides chrome for
    Deep routes. This is the live control registry — not the declarative
    config in ``chrome_config.py``.

    Callers must register before the first Shell view is built. Getters raise
    ``AssertionError`` if registration (or the drawer) is missing.
    """

    _appbar: ft.AppBar | None = None
    _bottom_appbar: ft.BottomAppBar | None = None
    _floating_action_button: ft.FloatingActionButton | None = None
    _floating_action_button_location: ft.FloatingActionButtonLocation | None = None
    _horizontal_alignment: ft.CrossAxisAlignment | None = None
    _vertical_alignment: ft.MainAxisAlignment | None = None
    _appbar_menu_button: ft.IconButton | None = None
    _appbar_title: ft.Text | None = None
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
        """Store shared chrome controls and page alignment defaults.

        Args:
            appbar: Shared top app bar.
            bottom_appbar: Shared bottom app bar.
            floating_action_button: Shared FAB (Create set).
            floating_action_button_location: FAB dock location.
            horizontal_alignment: Default view horizontal alignment.
            vertical_alignment: Default view vertical alignment.
            appbar_menu_button: Leading menu button used when config enables it.
            search_button: Search action on the bottom app bar.
        """
        cls._appbar = appbar
        cls._bottom_appbar = bottom_appbar
        cls._floating_action_button = floating_action_button
        cls._floating_action_button_location = floating_action_button_location
        cls._horizontal_alignment = horizontal_alignment
        cls._vertical_alignment = vertical_alignment
        cls._appbar_menu_button = appbar_menu_button
        cls._appbar_title = appbar.title if isinstance(appbar.title, ft.Text) else None
        cls._search_button = search_button
        cls._allow_bottom_appbar_system_inset(bottom_appbar)

    @classmethod
    def set_drawer(cls, drawer: ft.NavigationDrawer):
        """Attach the shared navigation drawer reference.

        Args:
            drawer: ``AppDrawer`` (or compatible) instance assigned to the page.
        """
        cls._drawer = drawer

    @classmethod
    def set_bottom_appbar_height(cls, height: float) -> None:
        """Set the bottom app bar content height without clipping system insets.

        ``height`` is the interactive content box (menu/search row), not the
        final on-screen bar size. Flutter's ``BottomAppBar`` already wraps that
        box in ``SafeArea`` and grows by the system navigation inset. Flet's
        ``LayoutControl`` must not clamp the outer height to the same value, or
        buttons are squeezed under the system navigation bar.

        Args:
            height: Content height in logical pixels (for example ``80`` or
                ``50``).
        """
        bottom_appbar = cls.get_bottom_appbar()
        cls._allow_bottom_appbar_system_inset(bottom_appbar)
        bottom_appbar.height = height

    @classmethod
    def _allow_bottom_appbar_system_inset(cls, bottom_appbar: ft.BottomAppBar) -> None:
        """Keep ``height`` as Flutter content height, not an outer SizedBox clamp."""
        bottom_appbar._internals["skip_properties"] = ["height"]

    @classmethod
    def get_appbar(cls) -> ft.AppBar:
        """Return the registered app bar."""
        assert cls._appbar is not None, "App chrome is not registered"
        return cls._appbar

    @classmethod
    def get_bottom_appbar(cls) -> ft.BottomAppBar:
        """Return the registered bottom app bar."""
        assert cls._bottom_appbar is not None, "App chrome is not registered"
        return cls._bottom_appbar

    @classmethod
    def get_floating_action_button(cls) -> ft.FloatingActionButton:
        """Return the registered floating action button."""
        assert cls._floating_action_button is not None, "App chrome is not registered"
        return cls._floating_action_button

    @classmethod
    def get_floating_action_button_location(cls) -> ft.FloatingActionButtonLocation:
        """Return the registered FAB location."""
        assert cls._floating_action_button_location is not None, "App chrome is not registered"
        return cls._floating_action_button_location

    @classmethod
    def get_horizontal_alignment(cls) -> ft.CrossAxisAlignment:
        """Return the default view horizontal alignment."""
        assert cls._horizontal_alignment is not None, "App chrome is not registered"
        return cls._horizontal_alignment

    @classmethod
    def get_vertical_alignment(cls) -> ft.MainAxisAlignment:
        """Return the default view vertical alignment."""
        assert cls._vertical_alignment is not None, "App chrome is not registered"
        return cls._vertical_alignment

    @classmethod
    def get_appbar_menu_button(cls) -> ft.IconButton:
        """Return the leading drawer-menu button for Shell routes that show it."""
        assert cls._appbar_menu_button is not None, "App chrome is not registered"
        return cls._appbar_menu_button

    @classmethod
    def get_appbar_title(cls) -> ft.Text:
        """Return the shared app bar title text control."""
        assert cls._appbar_title is not None, "App chrome is not registered"
        return cls._appbar_title

    @classmethod
    def show_appbar_title(cls, text: str) -> None:
        """Restore the greeting/title ``Text`` after in-place search replaces it."""
        appbar = cls.get_appbar()
        title = cls.get_appbar_title()
        title.value = text
        appbar.title = title
        appbar.center_title = True

    @classmethod
    def get_search_button(cls) -> ft.IconButton:
        """Return the bottom-bar search button."""
        assert cls._search_button is not None, "App chrome is not registered"
        return cls._search_button

    @classmethod
    def get_drawer(cls) -> ft.NavigationDrawer:
        """Return the registered navigation drawer."""
        assert cls._drawer is not None, "App drawer is not set"
        return cls._drawer

    @classmethod
    def has_drawer(cls) -> bool:
        """Return whether a drawer has been set."""
        return cls._drawer is not None
