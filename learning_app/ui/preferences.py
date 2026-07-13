"""Create accessors for Flet's persistent shared-preferences service."""

import flet as ft


def get_shared_preferences() -> ft.SharedPreferences:
    """Create a standalone shared-preferences service.

    Returns:
        A service instance for persistent application preference operations.
    """
    return ft.SharedPreferences()
