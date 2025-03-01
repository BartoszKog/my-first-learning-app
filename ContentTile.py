import flet as ft
from WordFields import WordFields
from WordDefinitionField import WordDefinitionField
from AppData import delate_set, set_default_progress
from page_functions import create_alert_dialog
from PageProperties import PageProperties
# imports for export method
import os

class ContentTile(ft.Card):
    def __init__(self, file_name: str, title: str, subtitle: str = "", parent_container=None, key=None, export_mode = False):
        super().__init__(key=key)
        self.parent_container = parent_container
        self.title = title
        
        if file_name.split("_")[1] == "words.csv":
            kind = "words"
        elif file_name.split("_")[1] == "definitions.csv":
            kind = "definitions"
        else:         
            raise Exception("The file_name must match the kind.")
        
        self.file_name = file_name
        self.kind = kind
        
        leadingIcon = ft.Icon(ft.icons.BOOK)
        
        if kind == "definitions":
            leadingIcon = ft.Icon(ft.icons.HELP)

        self.popUpButton = ft.PopupMenuButton(
            icon=ft.icons.MORE_VERT,
            items=[
                ft.PopupMenuItem(text="Edit", on_click=self.edit),
                ft.PopupMenuItem(text="Set default progress", on_click=self.show_set_default_progress_dialog),
                ft.PopupMenuItem(text="Delete", on_click=self.show_delete_dialog),
            ],
            on_open=lambda e: self.file_not_found_dialog(e) if not self.__file_exist() else None
        )
        
        lt = ft.ListTile(
            leading=leadingIcon,
            title=ft.Text(title, size=20),
            subtitle=ft.Text(subtitle) if subtitle else None,
            trailing=self.popUpButton if not export_mode else None,
            on_click=self.open_set if not export_mode else self.export,
            dense=True,  # Make the ListTile more compact
            min_height=75
        )
        
        self.content = lt
        self.margin = 5  # Add some margin around the card

    def edit(self, e):
        from page_functions import quit_main_menu
        from EditSetMenu import EditSetMenu
        quit_main_menu(e)
        e.page.add(EditSetMenu(self.file_name, width=PageProperties.width*0.8))
        

    def show_delete_dialog(self, e):
        create_alert_dialog(
            page=e.page,
            title="Confirm Delete",
            content="Are you sure you want to delete this set of " + self.kind + "?",
            close_button_text="Cancel",
            action_button_text="Delete",
            action_function=self.delete_item
        )

    def delete_item(self, e, file_not_exist=False):
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
            action_function=self.set_default_progress
        )
        
    def set_default_progress(self, e):
        # Logic for setting default progress
        set_default_progress(self.file_name)
        e.page.update()
        
    def open_set(self, e):
        if self.__file_exist():
            # opening the set of words or definitions
            e.page.controls.clear()
            e.page.appbar.visible = False
            e.page.bottom_appbar.visible = False
            e.page.floating_action_button.visible = False
            PageProperties.set_width_height_from_page(e.page)
            if self.kind == "words":
                wf = WordFields(self.file_name, page=e.page, width=PageProperties.width*0.8)
                e.page.add(wf)
            elif self.kind == "definitions":
                wdf = WordDefinitionField(self.file_name, page=e.page, width=PageProperties.width*0.8)
                e.page.add(wdf)
            e.page.update()
        else:
            self.file_not_found_dialog(e)
        
    def file_not_found_dialog(self, e):
        create_alert_dialog(
            page=e.page,
            title="File not found",
            content="File of this set was not found. \nIt has been removed from the list.",
            close_button_text="OK"
        )
        self.delete_item(e, file_not_exist=True)
        
    def __file_exist(self):
        try:
            with open(self.file_name, "r"):
                pass
        except FileNotFoundError:
            return False
        return True
    
    # methods involved with logic of searching
    def contains_pattern(self, pattern: str):
        return pattern.lower() in self.title.lower()
    
    def indicate_pattern(self, pattern: str, main_color = False):
        assert pattern != "", "Pattern must not be empty."
        
        title_text = self.title
        pattern_lower = pattern.lower()
        title_lower = title_text.lower()
        bgcolor = ft.colors.YELLOW
        if main_color:
            bgcolor = ft.colors.LIGHT_BLUE
        color = ft.colors.BLACK
        
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
            return
        
        formatted_text = []
        last_index = 0
        
        for start, end in spans:
            if last_index < start:
                formatted_text.append(ft.TextSpan(text=title_text[last_index:start]))
            formatted_text.append(ft.TextSpan(title_text[start:end], ft.TextStyle(bgcolor=bgcolor, color=color)))
            last_index = end
        
        if last_index < len(title_text):
            formatted_text.append(ft.TextSpan(text=title_text[last_index:]))
        
        self.content.title = ft.Text(spans=formatted_text, size=20)
        self.content.update()

    def reset_indication(self):
        self.content.title = ft.Text(self.title, size=20)
        self.content.update()
    
    def export(self, e):
        if not self.__file_exist():
            self.file_not_found_dialog(e)
            return
        
        # Create or get file picker
        try:
            picker = PageProperties.get_export_csv_picker()
        except AssertionError:
            picker = PageProperties.create_export_csv_picker(e.page)
        
        # Set callback to handle picker result
        def export_callback(picker_result):
            if not picker_result.path:
                return  # Selection canceled
            
            def copy2(src: str, dst: str):
                with open(src, 'rb') as fsrc:
                    with open(dst, 'wb') as fdst:
                        fdst.write(fsrc.read())
                
            # Prepare destination file name
            destination_path = picker_result.path
            
            try:
                # Copy file to selected location
                copy2(self.file_name, destination_path)
                
                # Show success message
                create_alert_dialog(
                    page=e.page,
                    title="Export completed",
                    content=f"Successfully exported set '{self.title}' to:\n{destination_path}",
                    close_button_text="OK"
                )
            except Exception as ex:
                # Error handling
                create_alert_dialog(
                    page=e.page,
                    title="Export error",
                    content=f"Failed to export file:\n{str(ex)}",
                    close_button_text="OK"
                )
        
        # Assign callback and launch picker
        PageProperties.set_export_callback(export_callback)
        picker.save_file(
            dialog_title="Choose export location",
            file_name=os.path.basename(self.file_name),
            allowed_extensions=["csv"]
        )
        e.page.update()