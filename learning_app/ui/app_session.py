from flet import FilePicker, IconButton, Page

from learning_app.ui.app_chrome import AppChrome


class AppSession:
    _page: Page | None = None
    _export_picker_csv: FilePicker | None = None
    _navigation_disabled = False

    @classmethod
    def set_page(cls, page: Page):
        cls._page = page

    @classmethod
    def get_page(cls) -> Page:
        assert cls._page is not None, "Page is not set"
        return cls._page

    @classmethod
    def get_export_csv_picker(cls) -> FilePicker:
        if cls._export_picker_csv is None:
            cls._export_picker_csv = FilePicker()
        return cls._export_picker_csv

    @classmethod
    def disable_all_navigation_controls(cls):
        page = cls.get_page()

        if page.bottom_appbar and page.bottom_appbar.content:
            for control in page.bottom_appbar.content.controls:
                if isinstance(control, IconButton):
                    control.disabled = True

        if page.floating_action_button:
            page.floating_action_button.disabled = True

        if AppChrome.has_drawer():
            AppChrome.get_drawer().disabled = True

        cls._navigation_disabled = True
        page.update()

    @classmethod
    def enable_all_navigation_controls(cls):
        page = cls.get_page()

        if page.bottom_appbar and page.bottom_appbar.content:
            for control in page.bottom_appbar.content.controls:
                if isinstance(control, IconButton):
                    control.disabled = False

        if page.floating_action_button:
            page.floating_action_button.disabled = False

        if AppChrome.has_drawer():
            AppChrome.get_drawer().disabled = False

        cls._navigation_disabled = False
        page.update()

    @classmethod
    def is_navigation_disabled(cls) -> bool:
        return cls._navigation_disabled
