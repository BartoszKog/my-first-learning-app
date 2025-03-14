import flet as ft 
from TilesContainer import TilesContainer
from PageProperties import PageProperties 

class SearchControl(ft.Row):
    COLOR = ft.Colors.CYAN
    
    def __init__(self, page, tiles_container: TilesContainer):
        super().__init__()
        self.page = page
        self.tiles_container = tiles_container
        
        self.vertical_alignment = ft.CrossAxisAlignment.CENTER
        self.tight = True
        self.search_field = ft.TextField(
            label="Search",
            expand=True,
            autofocus=True,
            on_focus=self.focus_text_field,
            on_change=self.change_text_field,
            border_color=self.COLOR,
        )
        
        self.next_pattern_button = ft.IconButton(
            icon=ft.Icons.ARROW_CIRCLE_DOWN,
            on_click=self.on_next_pattern_click,
            icon_color=self.COLOR
        )
        
        self.previous_pattern_button = ft.IconButton(
            icon=ft.Icons.ARROW_CIRCLE_UP,
            on_click=self.on_previous_pattern_click,
            icon_color=self.COLOR
        )
        
        self.close_button = ft.IconButton(
            icon=ft.Icons.CLOSE,
            on_click=self.on_close_click,
            icon_color=self.COLOR
        )
        
        self.controls.extend([
            self.search_field,
            self.next_pattern_button,
            self.previous_pattern_button,
            self.close_button
        ])
        
    def on_next_pattern_click(self, e):
        self.tiles_container.scroll_to_next()
        
    def on_previous_pattern_click(self, e):
        self.tiles_container.scroll_to_previous()
        
    def on_close_click(self, e):
        if not self.tiles_container.export_mode:
            TilesContainer().back_to_main_menu(e)
            self.tiles_container.turn_off_searching_mode()
        else:
            self.close_but_in_export_mode()
    
    # It is involved with changing the height of TilesContainer
    def focus_text_field(self, e):
        from page_functions import is_instance_in_the_page # to check if it is instance of ImportExportControl 
        from ImportExportControl import ImportExportControl # to check if it is instance of ImportExportControl 
        # check if it is instance of TilesContainer in controls of page
        if isinstance(e.page.controls[0], TilesContainer):
            if e.page.platform == ft.PagePlatform.WINDOWS:
                e.page.controls[0].scale_height_to_page(e.page, 0.85)
            else:
                e.page.controls[0].scale_height_to_page(e.page, 0.55)
        elif is_instance_in_the_page(e.page, ImportExportControl) and e.page.platform == ft.PagePlatform.ANDROID:
            export_body = PageProperties.get_export_body()
            export_body.scale_height_to_page(e.page, 0.40)
            assert isinstance(e.page.controls[0], ImportExportControl)
            import_export_control = e.page.controls[0] 
            import_export_control.add_space_before_export_controls()
            import_export_control.scale_height_to_page(0.55)
                
    def change_text_field(self, e):
        pattern = self.search_field.value
        self.tiles_container.indicate_patterns_and_scroll_to_first(pattern)         
                
    def did_mount(self):
        self.tiles_container.trigger_searching_mode()
        
    def will_unmount(self):
        self.tiles_container.turn_off_searching_mode()
        
    def close_but_in_export_mode(self):
        from ImportExportControl import ImportExportControl
        assert self.tiles_container.export_mode
        assert isinstance(self.page.controls[0], ImportExportControl)
        if self.page.platform == ft.PagePlatform.ANDROID:
            import_export_control = self.page.controls[0]
            import_export_control.remove_space_before_export_controls()
            import_export_control.scale_height_to_page(0.80)
        self.page.bottom_appbar.visible = True
        self.page.appbar.visible = True
        self.page.padding = PageProperties.padding
        export_body = PageProperties.get_export_body()
        export_body.reset_indications()
        self.tiles_container.turn_off_searching_mode()
        self.tiles_container.scale_height_to_page(self.page, 0.65)
        self.page.remove(self)
        
        
        