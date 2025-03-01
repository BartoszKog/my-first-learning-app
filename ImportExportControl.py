import flet as ft
from PageProperties import PageProperties   
from page_functions import create_alert_dialog, is_instance_in_the_page
from TilesContainer import TilesContainer
from SearchControl import SearchControl
from CSVProcessor import CSVProcessor
 
class ImportExportControl(ft.Container):
    SCALE_IMPORT_BUTTON = 1.25
    DEFAULT_BOTTOM_APP_BAR_HEIGHT = 80
    MINIMAL_BOTTOM_APP_BAR_HEIGHT = 50
    
    def __init__(self):
        super().__init__()
        # self.alignment = ft.MainAxisAlignment.START
        # self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.last_tab_index = 0
        self.height = PageProperties.height * 0.8
        self.width = PageProperties.width * 0.9
             
        self.tabs = ft.Tabs(
            tab_alignment=ft.TabAlignment.FILL,
            scrollable=False,
            on_change=self.__on_tab_change,
            tabs=[
                ft.Tab(text="Import"),
                ft.Tab(text="Export"),
            ]
        )
        
        self.body = ft.Container(
            padding=ft.Padding(left=30, right=30, top=0, bottom=30),
            expand=True
        )
        
        self.content = ft.Column(
            [
                self.tabs,
                self.body
            ]
        )
        
        # import controls
        self.title_field = ft.TextField(
            label="Title",
            value="",
            border_color=ft.colors.CYAN,
            on_focus=self.__on_focus_field,
            on_blur=self.__on_blur_field,
            visible=False,
        )
        
        self.subtitle_field = ft.TextField(
            label="Subtitle",
            value="",
            border_color=ft.colors.CYAN,
            on_focus=self.__on_focus_field,
            on_blur=self.__on_blur_field,
            visible=False,
        )
        
        self.choose_file_button = ft.ElevatedButton(
            text="Choose file",
            on_click=self.__on_choose_file_click,
            icon=ft.icons.FOLDER,
            scale=ImportExportControl.SCALE_IMPORT_BUTTON,
        )
        
        self.cancel_button = ft.ElevatedButton(
            text="Cancel",
            on_click=self.__on_cancel_button_click,
            icon=ft.icons.CLOSE,
            icon_color=ft.colors.RED_900,
            visible=False,
        )    
        
        self.add_set_button = ft.ElevatedButton(
            text="Add set",
            icon=ft.icons.ADD,
            on_click=self.__on_add_set_click,
            icon_color=ft.colors.GREEN_100,
            visible=False,
        )
        
        
        self.file_selection_tips = {
            "choose_file": "Click the button to select a file for import.\nFile must be in csv format.",
            "chosen_file_title": "Enter the title and optionally a subtitle.\nYou can also cancel the operation or select a different file.",
        }
        
        self.text_tip = ft.Text(
            spans=[
                ft.TextSpan(text=self.file_selection_tips["choose_file"])
            ],
            text_align=ft.TextAlign.CENTER
        )
        
        self.buttons = ft.Row(
            [
                self.add_set_button,
                self.cancel_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        self.import_controls = ft.Column(
            [
                self.text_tip,
                self.title_field,
                self.subtitle_field,
                self.buttons,
                self.choose_file_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=25
        )
        
        # export controls
        if not PageProperties.has_export_body():
            self.tiles_of_sets = TilesContainer(export_mode=True)
            PageProperties.set_export_body(self.tiles_of_sets)
        else:
            self.tiles_of_sets = PageProperties.get_export_body()
            
        self.export_controls = ft.Column(
            [
                ft.Text("Choose a set to export."),
                self.tiles_of_sets
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        
        # create select file dialog csv
        self.path_picker_csv_id = "path_picker_csv"
        self.csv_file_selector = ft.FilePicker(
            on_result=self.__on_csv_file_selector_result,
        )
        # set id to path picker to be able to find it in the page
        self.csv_file_selector.id = self.path_picker_csv_id
        
        # attributes involved in validation
        self.validation_warnings = None
        self.validation_requires_specific_actions = None
        self.validation_has_statistics = None
        self.validation_data_type = None
        
    
    def __make_layout_for_chosen_file(self, selected_file: str = None, selected_file_path: str = None):
        # assert that shows invalid call of the method
        # when selected_file is not None, selected_file_path must be not None too
        assert selected_file is None or selected_file_path is not None, "selected_file_path must be not None when selected_file is not None"
        
        # If an argument is passed, save it; otherwise, use the previously set attribute.
        if selected_file is not None:
            self.chosen_file = selected_file
            self.chosen_file_path = selected_file_path
        else:
            selected_file = self.chosen_file
        # Clear existing values in self.text_tip.spans
        self.text_tip.spans.clear()
        # Update the content of self.text_tip using the spans attribute
        self.text_tip.spans = [
            ft.TextSpan(text=self.file_selection_tips["chosen_file_title"]),
            ft.TextSpan(text="\nSelected file: ", style=ft.TextStyle(italic=True)),
            ft.TextSpan(text=selected_file, style=ft.TextStyle(color=ft.colors.TEAL))
        ]
        # if there is some error text in title_field remove it
        self.title_field.error_text = ""
        
        self.title_field.visible = True
        self.subtitle_field.visible = True
        self.add_set_button.visible = True
        self.cancel_button.visible = True
        self.__downscale_import_button()
        self.__change_import_button_to_changing_file()
        self.update()
    
    def __make_layout_before_chosen_file(self):
        self.text_tip.spans = [
            ft.TextSpan(text=self.file_selection_tips["choose_file"])
        ]
        self.title_field.visible = False
        self.subtitle_field.visible = False
        self.add_set_button.visible = False
        self.cancel_button.visible = False
        self.__upscale_import_button()
        self.__set_import_button_default()
        self.__remove_validation_properties()
        self.update()
    
    def __disable_all_import_controls(self):
        self.title_field.disabled = True
        self.subtitle_field.disabled = True
        self.choose_file_button.disabled = True
        self.cancel_button.disabled = True
        self.add_set_button.disabled = True
        self.__disable_menu_button()
        self.update()
        
    def __enable_all_import_controls(self):
        self.title_field.disabled = False
        self.subtitle_field.disabled = False
        self.choose_file_button.disabled = False
        self.cancel_button.disabled = False
        self.add_set_button.disabled = False
        self.__enable_menu_button()
        self.update()
    
    def __on_choose_file_click(self, e):
        self.csv_file_selector.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv"],
            dialog_title="Select csv file to import"
        )
        
        self.__disable_all_import_controls()
        
    def __layout_after_adding_set(self):
        self.chosen_file = None
        self.chosen_file_path = None
        self.__make_layout_before_chosen_file()
        self.__android_center_import_controls_alignment()
        self.page.open(ft.SnackBar(ft.Text("Set has been added successfully.")))
        
    def __on_add_set_click(self, e):
        if not self.title_field.value.strip():
            self.title_field.error_text = "Title cannot be empty."
            self.update()
        else:
            # asserts too make sure that attributes with file name and path are set
            assert self.chosen_file is not None, "chosen_file must be not None"
            assert self.chosen_file_path is not None, "chosen_file_path must be not None"
            
            # Logic for adding a set
            if not self.validation_requires_specific_actions:
                # if there are no specific actions required
                if self.validation_has_statistics:
                    
                    def action_function_for_dialog(e): # user checked "Yes"
                        CSVProcessor.save_set_with_no_specific_actions(
                            self.chosen_file_path,
                            self.chosen_file,
                            self.title_field.value,
                            self.subtitle_field.value,
                            True,
                            True,
                        )
                        self.__layout_after_adding_set()
                    
                    def close_action_function_for_dialog(e): # user checked "No"
                        CSVProcessor.save_set_with_no_specific_actions(
                            self.chosen_file_path,
                            self.chosen_file,
                            self.title_field.value,
                            self.subtitle_field.value,
                            False,
                        )
                        self.__layout_after_adding_set()
                    
                    create_alert_dialog(
                        self.page,
                        title="Statistics",
                        content="Do you want to keep progress information?",
                        close_button_text="No",
                        action_button_text="Yes",
                        action_function=action_function_for_dialog,
                        close_action_function=close_action_function_for_dialog
                    )
                else:
                    CSVProcessor.save_set_with_no_specific_actions(
                        self.chosen_file_path,
                        self.chosen_file,
                        self.title_field.value,
                        self.subtitle_field.value,
                        False,
                    )
                    self.__layout_after_adding_set()
                        
            else:  # if there are specific actions required
                if self.validation_has_statistics:
                    def action_function_for_dialog(e):  # user checked "Yes"
                        information = CSVProcessor.save_set_with_specific_actions(
                            self.chosen_file_path,
                            self.chosen_file,
                            self.title_field.value,
                            self.subtitle_field.value,
                            self.validation_data_type,
                            True,  # has_statistics
                            self.validation_warnings,
                            True,  # keep_statistics
                        )
                        if information:
                            create_alert_dialog(
                                self.page,
                                title="Information",
                                content=information
                            )
                        self.__layout_after_adding_set()
                    
                    def close_action_function_for_dialog(e):  # user checked "No"
                        information = CSVProcessor.save_set_with_specific_actions(
                            self.chosen_file_path,
                            self.chosen_file,
                            self.title_field.value,
                            self.subtitle_field.value,
                            self.validation_data_type,
                            True,  # has_statistics
                            self.validation_warnings,
                            False,  # don't keep_statistics
                        )
                        if information:
                            create_alert_dialog(
                                self.page,
                                title="Information",
                                content=information
                            )
                        self.__layout_after_adding_set()
                    
                    create_alert_dialog(
                        self.page,
                        title="Statistics",
                        content="Do you want to keep progress information?",
                        close_button_text="No",
                        action_button_text="Yes",
                        action_function=action_function_for_dialog,
                        close_action_function=close_action_function_for_dialog
                    )
                else:
                    information = CSVProcessor.save_set_with_specific_actions(
                        self.chosen_file_path,
                        self.chosen_file,
                        self.title_field.value,
                        self.subtitle_field.value,
                        self.validation_data_type,
                        False,  # has_statistics
                        self.validation_warnings,
                    )
                    if information:
                        create_alert_dialog(
                            self.page,
                            title="Information",
                            content=information
                        )
                    self.__layout_after_adding_set()
        
    
    def __upscale_import_button(self):
        self.choose_file_button.scale = ImportExportControl.SCALE_IMPORT_BUTTON
    
    def __downscale_import_button(self):
        self.choose_file_button.scale = 1.0
    
    def __change_import_button_to_changing_file(self):
        self.choose_file_button.text = "Change file"
        self.choose_file_button.icon = ft.icons.DRIVE_FILE_MOVE
        self.update()
        
    def __set_import_button_default(self):
        self.choose_file_button.text = "Choose file"
        self.choose_file_button.icon = ft.icons.FOLDER
        self.update()
        
    def __on_cancel_button_click(self, e):
        self.__make_layout_before_chosen_file()
        self.__android_center_import_controls_alignment()
    
    def __user_has_chosen_file(self):
        return self.title_field.visible
    
    def __set_validation_properties(self, validation_result):
        self.validation_warnings = validation_result["warnings"]
        self.validation_requires_specific_actions = validation_result["requires_specific_actions"]
        self.validation_has_statistics = validation_result["has_statistics"]
        self.validation_data_type = validation_result["data_type"]
        
    def __remove_validation_properties(self):
        self.validation_warnings = None
        self.validation_requires_specific_actions = None
        self.validation_has_statistics = None
        self.validation_data_type = None
    
    def __on_csv_file_selector_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            validation_result = CSVProcessor.validate_file(e.files[0].path)
            
            if validation_result["is_valid"]:
                self.title_field.value = validation_result["name_suggestion"]
                self.subtitle_field.value = "" # it will be set by default
                self.__make_layout_for_chosen_file(e.files[0].name, e.files[0].path)
                self.__set_validation_properties(validation_result)
            
                if validation_result["warnings"]:
                    warning_title = "Warnings" if len(validation_result["warnings"]) > 1 else "Warning"
                    create_alert_dialog(self.page, warning_title, "\n".join(validation_result["warnings"]))
            else:
                if validation_result["errors"]:
                    error_title = "Errors" if len(validation_result["errors"]) > 1 else "Error"
                    create_alert_dialog(self.page, error_title, "\n".join(validation_result["errors"]))

        elif self.__user_has_chosen_file():
            self.__make_layout_for_chosen_file()
        else:
            self.__make_layout_before_chosen_file()
        
        self.__enable_all_import_controls()
    
    def __ensure_csv_selector_in_overlay(self):
        dialog = self.csv_file_selector                
        # delete dialog selector from overlay if exists
        for p in self.page.overlay:
            if hasattr(p, 'id') and p.id == dialog.id:
                self.page.overlay.remove(p)
                break
            
        # add dialog selector to overlay
        self.page.overlay.append(self.csv_file_selector)
    
    def __on_change_tab_from_import_to_export_delate_search_control(self):
        if self.last_tab_index == 0:
            self.__on_blur_field(None)
    
    def __on_change_tab_from_export_to_import_delate_search_control(self):
        if is_instance_in_the_page(self.page, SearchControl):
            self.remove_space_before_export_controls()
            if self.last_tab_index == 1:
                current_search_control = PageProperties.get_current_search_control_involved_export_mode()
                current_search_control.close_but_in_export_mode()
    
    def __on_tab_change(self, e):
        self.__on_change_tab_from_import_to_export_delate_search_control()
        self.__on_change_tab_from_export_to_import_delate_search_control()
        if e.control.selected_index == 0:
            self.__show_import_controls()
        else:
            self.__show_export_controls()
        self.last_tab_index = e.control.selected_index
            
    def __show_import_controls(self):
        self.body.content = ft.Container(
            self.import_controls,
            height=PageProperties.height * 0.4,
        )
        self.__show_search_button(False)
        self.update()
    
    def __show_export_controls(self):
        self.body.content = self.export_controls
        self.__show_search_button(True)
        self.update()
        
    def __show_search_button(self, choice: bool):
        # making search button in bottom appbar visible or not
        self.page.bottom_appbar.content.controls[2].visible = choice 
        self.page.update()
        
    def __disable_menu_button(self):
        # disable menu button in bottom appbar
        self.page.bottom_appbar.content.controls[0].disabled = True
        self.page.update()
        
    def __enable_menu_button(self):
        # enable menu button in bottom appbar
        self.page.bottom_appbar.content.controls[0].disabled = False
        self.page.update()
        
    def __make_compact_bottom_appbar_height(self):
        self.page.bottom_appbar.height = ImportExportControl.MINIMAL_BOTTOM_APP_BAR_HEIGHT
        self.page.update()
        
    def __make_default_bottom_appbar_height(self):
        self.page.bottom_appbar.height = ImportExportControl.DEFAULT_BOTTOM_APP_BAR_HEIGHT
        self.page.update()
        
    def __hide_first_span_in_text_tip(self):
        self.text_tip.spans[0].visible = False
        self.update()
        
    def __show_first_span_in_text_tip(self):
        self.text_tip.spans[0].visible = True
        self.update()
        
    def __android_center_import_controls_alignment(self):
        if PageProperties.platform == ft.PagePlatform.ANDROID:
            # it is necessary to show the title field when keyboard is opened
            self.import_controls.alignment = ft.MainAxisAlignment.CENTER
            self.import_controls.spacing = 25
            self.__make_default_bottom_appbar_height()
            self.choose_file_button.visible = True
            self.__show_first_span_in_text_tip()
            self.update()
            
    def __android_start_import_controls_alignment(self):
        if PageProperties.platform == ft.PagePlatform.ANDROID:
            # it is necessary to show the title field when keyboard is opened
            self.import_controls.alignment = ft.MainAxisAlignment.START
            self.import_controls.spacing = 10
            self.__make_compact_bottom_appbar_height()
            self.choose_file_button.visible = False
            self.__hide_first_span_in_text_tip()
            self.update()
        
    def __on_focus_field(self, e = None):
        # change alignment of column with import controls when platform is android
        self.__android_start_import_controls_alignment()
            
    def __on_blur_field(self, e = None):
        # change alignment of column with import controls when platform is android
        self.__android_center_import_controls_alignment()
            
    def add_space_before_export_controls(self):
        if PageProperties.platform == ft.PagePlatform.ANDROID and self.last_tab_index == 1:
            self.content.controls.insert(0, ft.Container(height=40))
            self.update()
            
    def remove_space_before_export_controls(self):
        if PageProperties.platform == ft.PagePlatform.ANDROID and self.last_tab_index == 1:
            if isinstance(self.content.controls[0], ft.Container):
                self.content.controls.pop(0)
                self.update()
                
    def scale_height_to_page(self, scale_factor: float):
        self.height = self.page.height * scale_factor
        self.update()
        
    def did_mount(self):
        appbar = self.page.appbar
        appbar.title.value = "Import/Export"
        
        self.page.bottom_appbar.visible = True
        self.page.floating_action_button.visible = False
        
        self.__show_search_button(False)
        # show default tab
        self.__show_import_controls()
        
        self.__ensure_csv_selector_in_overlay()
        
        self.page.update()
 
    def will_unmount(self):
        self.__show_search_button(True)
        
        self.page.update()