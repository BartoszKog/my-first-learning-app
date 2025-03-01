from flet import Page, Padding, ThemeMode, FilePicker

class PageProperties:
    width = 500
    height = 900
    padding = Padding(left=50, right=50, top=0, bottom=0)
    platform = None
    theme_mode = None
    dark_theme_slider_value = 2
    light_theme_slider_value = 2
    dark_theme_bgcolor = None
    light_theme_bgcolor = None
    export_picker_csv = None
    
    @classmethod
    def create_export_csv_picker(cls, page):
        if not cls.export_picker_csv:
            cls.export_picker_csv = FilePicker(
                on_result=cls._on_export_picker_result
            )
            page.overlay.append(cls.export_picker_csv)
            page.update()
        return cls.export_picker_csv

    @classmethod
    def _on_export_picker_result(cls, e):
        # Ten callback będzie uzupełniany przez ContentTile przy eksporcie
        if hasattr(cls, "export_callback") and cls.export_callback:
            cls.export_callback(e)

    @classmethod
    def set_export_callback(cls, callback):
        cls.export_callback = callback

    @classmethod
    def get_export_csv_picker(cls):
        assert cls.export_picker_csv is not None, "Export CSV picker is not set"
        return cls.export_picker_csv
    
    @classmethod
    def set_width_height_from_page(cls, page: Page):
        cls.width = page.width
        cls.height = page.height
        cls.padding = page.padding
        cls.platform = page.platform
    
    @classmethod
    def set_theme_from_page(cls, page: Page):
        cls.theme_mode = page.theme_mode
        if cls.theme_mode.value ==  ThemeMode.DARK.value:
            cls.dark_mode = True
            cls.light_mode = False
        else:
            cls.dark_mode = False
            cls.light_mode = True
    
    @classmethod
    def set_body(cls, body):
        cls.body = body
        
    @classmethod
    def set_drawer(cls, drawer):
        cls.drawer = drawer
        
    @classmethod
    def set_export_body(cls, export_body):
        cls.export_body = export_body
        
    @classmethod
    def has_export_body(cls):
        return hasattr(cls, "export_body")
        
    @classmethod
    def get_body(cls):
        assert hasattr(cls, "body"), "Body is not set"
        return cls.body
    
    @classmethod
    def get_drawer(cls):
        assert hasattr(cls, "drawer"), "Drawer is not set"
        return cls.drawer
    
    @classmethod
    def get_export_body(cls):
        assert hasattr(cls, "export_body"), "Export body is not set"
        return cls.export_body

    @classmethod
    def set_slider_value(cls, theme_mode, value):
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_slider_value = value
        else:
            cls.light_theme_slider_value = value

    @classmethod
    def get_slider_value(cls, theme_mode=""):
        if theme_mode == ThemeMode.DARK:
            return cls.dark_theme_slider_value
        elif theme_mode == "":
            # return slider value based on theme mode
            return cls.light_theme_slider_value if cls.theme_mode == ThemeMode.LIGHT else cls.dark_theme_slider_value
        else:
            return cls.light_theme_slider_value

    @classmethod
    def set_bgcolor(cls, theme_mode, color):
        if theme_mode == ThemeMode.DARK:
            cls.dark_theme_bgcolor = color
        else:
            cls.light_theme_bgcolor = color

    @classmethod
    def get_bgcolor(cls, theme_mode=""):
        if theme_mode == ThemeMode.DARK:
            return cls.dark_theme_bgcolor
        elif theme_mode == "":
            # return color based on theme mode
            return cls.light_theme_bgcolor if cls.theme_mode == ThemeMode.LIGHT else cls.dark_theme_bgcolor
        else:
            return cls.light_theme_bgcolor
        
    @classmethod
    def set_slider_and_bgcolor_values_from_page(cls, page):
        cls.dark_theme_slider_value = page.client_storage.get("dark_theme_slider_value")
        cls.light_theme_slider_value = page.client_storage.get("light_theme_slider_value")
        cls.dark_theme_bgcolor = page.client_storage.get("dark_theme_bgcolor")
        cls.light_theme_bgcolor = page.client_storage.get("light_theme_bgcolor")
        
    @classmethod
    def set_current_search_control_involved_export_mode(cls, involved):
        cls.current_search_control_involved_export_mode = involved
        
    @classmethod
    def get_current_search_control_involved_export_mode(cls):
        assert hasattr(cls, "current_search_control_involved_export_mode"), "Current search control involved export mode is not set"
        return cls.current_search_control_involved_export_mode
    
    @classmethod
    def delete_current_search_control_involved_export_mode(cls):
        del cls.current_search_control_involved_export_mode