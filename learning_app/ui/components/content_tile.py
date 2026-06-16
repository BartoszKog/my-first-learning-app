import os

import flet as ft

from learning_app.data.app_data import delate_set, get_kind_of_file_and_validate, set_default_progress
from learning_app.data.file_path_manager import FilePathManager
from learning_app.ui.components.word_definition_field import WordDefinitionField
from learning_app.ui.components.word_fields import WordFields
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.page_properties import PageProperties


class ContentTile(ft.Card):
    def __init__(self, file_name: str, title: str, subtitle: str = "", parent_container=None, key=None, export_mode=False, pattern: str = "", main_color: bool = False):
        super().__init__(key=key)
        self.parent_container = parent_container
        self.title = title
        self.subtitle = subtitle
        self.export_mode = export_mode

        kind = get_kind_of_file_and_validate(file_name)

        self.file_name = file_name
        self.kind = kind

        leadingIcon = ft.Icon(ft.Icons.BOOK)

        if kind == "definitions":
            leadingIcon = ft.Icon(ft.Icons.HELP)

        self.popUpButton = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            items=[
                ft.PopupMenuItem(content="Edit", on_click=self.edit),
                ft.PopupMenuItem(content="Set default progress", on_click=self.show_set_default_progress_dialog),
                ft.PopupMenuItem(content="Delete", on_click=self.show_delete_dialog),
            ],
            on_open=lambda e: self.file_not_found_dialog(e) if not self.__file_exist() else None,
        )

        lt = ft.ListTile(
            leading=leadingIcon,
            title=self.__create_title_control(pattern, main_color),
            subtitle=ft.Text(subtitle) if subtitle else None,
            trailing=self.popUpButton if not export_mode else None,
            on_click=self.open_set if not export_mode else self.export,
            dense=True,  # Make the ListTile more compact
            min_height=75,
        )

        self.content = lt
        self.margin = 5  # Add some margin around the card

    def edit(self, e):
        from learning_app.ui.page_functions import quit_main_menu
        from learning_app.ui.screens.edit_set_menu import EditSetMenu
        quit_main_menu(e)
        e.page.add(EditSetMenu(self.file_name, width=PageProperties.width * 0.8))

    def show_delete_dialog(self, e):
        create_alert_dialog(
            page=e.page,
            title="Confirm Delete",
            content="Are you sure you want to delete this set of " + self.kind + "?",
            close_button_text="Cancel",
            action_button_text="Delete",
            action_function=self.delete_item,
        )

    def delete_item(self, e, file_not_exist=False):
        from learning_app.data.csv_processor import CSVProcessor
        if not CSVProcessor.validate_files_csv()["is_valid"]:
            create_alert_dialog(
                page=e.page,
                title="Error",
                content="files.csv has been changed. \nPlease restore it to its original state.",
                close_button_text="OK",
            )
            return

        delate_set(self.file_name, file_not_exist)
        self.parent_container.refresh_content()
        e.page.update()

    def show_set_default_progress_dialog(self, e):
        create_alert_dialog(
            page=e.page,
            title="Set Default Progress",
            content="Are you sure you want to set default progress for this set of " + self.kind + "?",
            close_button_text="Cancel",
            action_button_text="Set",
            action_function=self.set_default_progress,
        )

    def set_default_progress(self, e):
        # Logic for setting default progress
        set_default_progress(self.file_name)
        e.page.update()

    def __validate_file_before_opening(self, e):
        from learning_app.data.csv_processor import CSVProcessor

        if not self.__file_exist():
            self.file_not_found_dialog(e)
            return False

        validation_result = CSVProcessor.validate_file(self.file_name)

        if not validation_result["is_valid"] or len(validation_result["warnings"]) > 0 or not validation_result["has_statistics"]:
            error_message = "The file has been modified externally and cannot be opened correctly in the application.\n\n"

            if validation_result["errors"]:
                error_message += "Errors:\n"
                for error in validation_result["errors"]:
                    error_message += f"- {error}\n"

            if validation_result["warnings"]:
                error_message += "\nWarnings:\n"
                for warning in validation_result["warnings"]:
                    error_message += f"- {warning}\n"

            if not validation_result["has_statistics"]:
                error_message += "\nStatistics columns missing. This file cannot be used for learning without progress tracking.\n"

            error_message += "\nPlease fix the issues in the file before opening it."

            create_alert_dialog(
                page=e.page,
                title="File validation error",
                content=error_message,
                close_button_text="OK",
            )
            return False

        return True

    def open_set(self, e):
        if not self.__validate_file_before_opening(e):
            return

        e.page.controls.clear()
        e.page.appbar.visible = False
        e.page.bottom_appbar.visible = False
        e.page.floating_action_button.visible = False
        PageProperties.set_width_height_from_page(e.page)
        if self.kind == "words":
            wf = WordFields(self.file_name, page=e.page, width=PageProperties.width * 0.8)
            e.page.add(wf)
        elif self.kind == "definitions":
            wdf = WordDefinitionField(self.file_name, page=e.page, width=PageProperties.width * 0.8)
            e.page.add(wdf)
        e.page.update()

    def file_not_found_dialog(self, e):
        create_alert_dialog(
            page=e.page,
            title="File not found",
            content="File of this set was not found. \nIt has been removed from the list.",
            close_button_text="OK",
        )
        self.delete_item(e, file_not_exist=True)

    def __file_exist(self):
        file_path = FilePathManager.get_csv_path(self.file_name)
        try:
            with open(file_path, "r"):
                pass
        except FileNotFoundError:
            return False
        return True

    # methods involved with logic of searching
    def contains_pattern(self, pattern: str):
        return pattern.lower() in self.title.lower()

    def __create_title_control(self, pattern: str = "", main_color: bool = False):
        if not pattern:
            return ft.Text(self.title, size=20)

        title_lower = self.title.lower()
        pattern_lower = pattern.lower()
        bgcolor = ft.Colors.LIGHT_BLUE if main_color else ft.Colors.YELLOW
        color = ft.Colors.BLACK
        start = 0
        spans = []

        while start < len(title_lower):
            start = title_lower.find(pattern_lower, start)
            if start == -1:
                break
            end = start + len(pattern)
            spans.append((start, end))
            start = end

        if not spans:
            return ft.Text(self.title, size=20)

        formatted_text = []
        last_index = 0
        for start, end in spans:
            if last_index < start:
                formatted_text.append(ft.TextSpan(text=self.title[last_index:start]))
            formatted_text.append(ft.TextSpan(self.title[start:end], ft.TextStyle(bgcolor=bgcolor, color=color)))
            last_index = end

        if last_index < len(self.title):
            formatted_text.append(ft.TextSpan(text=self.title[last_index:]))

        return ft.Text(spans=formatted_text, size=20)

    def export(self, e):
        if not self.__file_exist():
            self.file_not_found_dialog(e)
            return

        e.page.run_task(self._export_file, e.page)

    async def _export_file(self, page):
        try:
            picker = PageProperties.get_export_csv_picker()
        except AssertionError:
            picker = PageProperties.create_export_csv_picker(page)

        is_windows = page.platform == ft.PagePlatform.WINDOWS

        if is_windows:
            destination_path = await picker.save_file(
                dialog_title="Choose export location",
                file_name=os.path.basename(self.file_name),
                allowed_extensions=["csv"],
                file_type=ft.FilePickerFileType.CUSTOM,
            )
            if destination_path and not destination_path.endswith(".csv"):
                destination_path += ".csv"
        else:
            directory_path = await picker.get_directory_path(
                dialog_title="Choose export directory",
            )
            if not directory_path:
                return
            destination_path = os.path.join(directory_path, os.path.basename(self.file_name))

        if not destination_path:
            return

        try:
            src_file_path = FilePathManager.get_csv_path(self.file_name)
            with open(src_file_path, "rb") as fsrc:
                with open(destination_path, "wb") as fdst:
                    fdst.write(fsrc.read())

            create_alert_dialog(
                page=page,
                title="Export completed",
                content=f"Successfully exported set '{self.title}' to:\n{destination_path}",
                close_button_text="OK",
            )
        except Exception as ex:
            create_alert_dialog(
                page=page,
                title="Export error",
                content=f"Failed to export file:\n{str(ex)}",
                close_button_text="OK",
            )
