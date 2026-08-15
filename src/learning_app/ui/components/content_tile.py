import os

import flet as ft

from learning_app.data.app_data import (
    delate_set,
    get_kind_of_file_and_validate,
    record_set_use,
    set_default_progress,
    update_set_metadata,
)
from learning_app.data.constants import TITLE_MAX_LENGTH
from learning_app.data.file_path_manager import FilePathManager
from learning_app.ui.layout_metrics import LayoutMetricsStore
from learning_app.ui.navigation import push_view
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.app_session import AppSession
from learning_app.ui.route_paths import SET_EDIT_ROUTE, SET_LEARN_ROUTE


class ContentTile(ft.Card):
    """One catalog entry with learn, edit, title change, delete, reset, or export actions.

    Home mode opens learn/edit flows and management menus. Export mode focuses
    on saving the set through the shared export file picker.

    Args:
        file_name: Set basename or path (``*_words.csv`` / ``*_definitions.csv``).
        title: Display title.
        subtitle: Optional secondary text.
        parent_container: Owning ``TilesContainer``, used after delete/refresh.
        key: Optional Flet control key.
        export_mode: When ``True``, present export-oriented behavior.
        pattern: Optional search highlight pattern.
        main_color: When ``True``, emphasize the tile as the current search hit.
    """

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
                ft.PopupMenuItem(content="Change title", on_click=self.show_change_title_dialog),
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
        push_view(e.page, SET_EDIT_ROUTE, file=self.file_name)

    def show_change_title_dialog(self, e):
        title_field = ft.TextField(
            label="Title",
            value=(self.title or "")[:TITLE_MAX_LENGTH],
            max_length=TITLE_MAX_LENGTH,
            autofocus=True,
        )
        subtitle_field = ft.TextField(
            label="Subtitle",
            value=self.subtitle or "",
            multiline=True,
            min_lines=1,
            max_lines=2,
        )

        def on_cancel(e):
            e.page.pop_dialog()

        def on_save(e):
            if not (title_field.value or "").strip():
                title_field.error = "This field is required"
                title_field.update()
                return

            title_field.error = None

            from learning_app.data.csv_processor import CSVProcessor

            if not CSVProcessor.validate_files_csv()["is_valid"]:
                e.page.pop_dialog()
                create_alert_dialog(
                    page=e.page,
                    title="Error",
                    content="files.csv has been changed. \nPlease restore it to its original state.",
                    close_button_text="OK",
                )
                return

            title = title_field.value.strip().capitalize()
            subtitle = (subtitle_field.value or "").strip().capitalize()
            update_set_metadata(self.file_name, title, subtitle)
            e.page.pop_dialog()
            if self.parent_container is not None:
                self.parent_container.refresh_content()
            e.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Change title"),
            content=ft.Column(
                controls=[title_field, subtitle_field],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.TextButton("Save", on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        e.page.show_dialog(dialog)

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
        from learning_app.ui.router import remove_views_for_set_file

        remove_views_for_set_file(e.page, self.file_name)
        # Already notified for a missing file; do not stack a second File not found.
        self.parent_container.refresh_content(show_alerts=not file_not_exist)
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

        record_set_use(self.file_name)
        LayoutMetricsStore.refresh(e.page)
        push_view(e.page, SET_LEARN_ROUTE, file=self.file_name)

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
        picker = AppSession.get_export_csv_picker()
        file_name = os.path.basename(self.file_name)
        if not file_name.endswith(".csv"):
            file_name += ".csv"

        try:
            src_file_path = FilePathManager.get_csv_path(self.file_name)
            with open(src_file_path, "rb") as fsrc:
                src_bytes = fsrc.read()

            destination_path = await picker.save_file(
                dialog_title="Choose export location",
                file_name=file_name,
                allowed_extensions=["csv"],
                file_type=ft.FilePickerFileType.CUSTOM,
                src_bytes=src_bytes,
            )
            if not destination_path:
                return

            if page.web:
                message = f"Successfully exported set '{self.title}'."
            else:
                message = f"Successfully exported set '{self.title}' to {destination_path}."
            page.show_dialog(ft.SnackBar(ft.Text(message)))
        except Exception as ex:
            create_alert_dialog(
                page=page,
                title="Export error",
                content=f"Failed to export file:\n{str(ex)}",
                close_button_text="OK",
            )
