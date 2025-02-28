import flet as ft 
from AppData import get_file_names, sanitize_file_name
from EditSetMenu import EditSetMenu
from constants import FilesColumns
from page_functions import create_alert_dialog

class CreateSetMenu(ft.Column):
    def __init__(self, width=300):
        from TilesContainer import TilesContainer
        super().__init__()
        self.width = width
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        self.title_field = ft.TextField(label="Title", width=width, max_length=20)
        
        self.subtitle_field = ft.TextField(label="Subtitle", width=width, multiline=True, min_lines=1, max_lines=2)
        
        self.kind_dropdown = ft.Dropdown(
            label="Kind",
            options=[
                ft.dropdown.Option("Word formations"),
                ft.dropdown.Option("Definitions"),
            ],
            width=width
        )
        
        def on_cancel_click(e):
            TilesContainer().back_to_main_menu(e)
        
        self.buttons_row = ft.Row(
            controls=[
                ft.ElevatedButton(text="Cancel", on_click=on_cancel_click),
                ft.ElevatedButton(text="Create", on_click=self.on_create_click)
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        self.controls.extend([
            self.title_field,
            self.subtitle_field,
            self.kind_dropdown,
            self.buttons_row
        ])
    
    def on_create_click(self, e):
        if not self.title_field.value:
            self.title_field.error_text = "This field is required"
        else:
            self.title_field.error_text = ""
            
        if not self.kind_dropdown.value:
            self.kind_dropdown.error_text = "Choose an option from the dropdown"
        else:
            self.kind_dropdown.error_text = ""
        
        if not self.title_field.value or not self.kind_dropdown.value:
            create_alert_dialog(
                page=e.page,
                title="Validation Error",
                content="Please fill in all fields and select an option \nfrom the dropdown.",
                close_button_text="OK"
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
                    
            title = self.title_field.value.capitalize()
            subtitle = self.subtitle_field.value.capitalize()            
        
            e.page.controls.clear()
            e.page.add(EditSetMenu(new_file_name, title=title, subtitle=subtitle, width=self.width))