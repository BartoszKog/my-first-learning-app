import flet as ft

from learning_app.data.app_data import get_file_names, sanitize_file_name
from learning_app.data.constants import TITLE_MAX_LENGTH
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.navigation import go_back, push_view
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.routable_screen import RoutableScreenMixin
from learning_app.ui.route_paths import SET_EDIT_ROUTE


class CreateSetMenu(RoutableScreenMixin, ft.Column):
    def __init__(self, width=300):
        super().__init__()
        self._form_width = width
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.title_field = ft.TextField(label="Title", width=width, max_length=TITLE_MAX_LENGTH)

        self.subtitle_field = ft.TextField(label="Subtitle", width=width, multiline=True, min_lines=1, max_lines=2)

        self.kind_dropdown = ft.Dropdown(
            label="Kind",
            options=[
                ft.DropdownOption("Word formations"),
                ft.DropdownOption("Definitions"),
            ],
            width=width,
        )
        def on_cancel_click(e):
            go_back(e.page)

        self.buttons_row = ft.Row(
            controls=[
                ft.Button(content="Cancel", on_click=on_cancel_click),
                ft.Button(content="Create", on_click=self.on_create_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.controls.extend([
            self.title_field,
            self.subtitle_field,
            self.kind_dropdown,
            self.buttons_row,
        ])

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        metrics = self.resolve_layout_metrics(metrics)
        self._form_width = metrics.form_width
        for field in (self.title_field, self.subtitle_field, self.kind_dropdown):
            field.width = metrics.form_width
        self.update_if_mounted()

    def on_create_click(self, e):
        from learning_app.data.csv_processor import CSVProcessor
        if not CSVProcessor.validate_files_csv()["is_valid"]:
            create_alert_dialog(
                page=e.page,
                title="Error",
                content="files.csv has been changed. \nPlease restore it to its original state.",
                close_button_text="OK",
            )
            return

        if not (self.title_field.value or "").strip():
            self.title_field.error = "This field is required"
        else:
            self.title_field.error = None

        if not self.kind_dropdown.value:
            self.kind_dropdown.error = "Choose an option from the dropdown"
        else:
            self.kind_dropdown.error = None

        if not (self.title_field.value or "").strip() or not self.kind_dropdown.value:
            create_alert_dialog(
                page=e.page,
                title="Error",
                content="Please fill in all fields and select an option \nfrom the dropdown.",
                close_button_text="OK",
            )
        else:
            # load list of file_names to create new file_name
            filenames = get_file_names()

            kind = self.kind_dropdown.value.lower()

            if kind == "word formations":
                kind = "words"

            # create sanitized file name
            sanitized_title = sanitize_file_name(self.title_field.value, kind)

            # check if file_name already exists
            checking = True
            counter = 1
            new_file_name = sanitized_title
            while checking:
                if new_file_name in filenames:
                    base_name = sanitized_title.replace(f"_{kind}.csv", "")
                    new_file_name = sanitize_file_name(f"{base_name}{counter}", kind)
                    counter += 1
                else:
                    checking = False

            title = self.title_field.value.strip().capitalize()
            subtitle = (self.subtitle_field.value or "").strip().capitalize()

            push_view(e.page, SET_EDIT_ROUTE, file=new_file_name, title=title, subtitle=subtitle)
