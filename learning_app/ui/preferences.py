import flet as ft


def get_shared_preferences() -> ft.SharedPreferences:
    # SharedPreferences can be used as a standalone service instance.
    return ft.SharedPreferences()
