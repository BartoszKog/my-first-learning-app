import flet as ft
from PageProperties import PageProperties
from page_functions import set_theme_from_bgcolor

class BackgroundShadeSlider(ft.Column):
    DARK_THEME_COLORS = [
        ft.Colors.BLACK,
        ft.Colors.SURFACE,
        ft.Colors.WHITE10,
        ft.Colors.GREY_900,
    ]
    
    LIGHT_THEME_COLORS = [
        ft.Colors.WHITE,
        ft.Colors.SURFACE,
        ft.Colors.BLUE_GREY_50,
        ft.Colors.BLUE_50,
    ]
    
    def __init__(self, label: str, initial_value: int):
        super().__init__()
        max_value = len(self.DARK_THEME_COLORS)
        self.label = ft.Text(label)
        self.slider = ft.Slider(
            min=1,
            max=max_value,
            divisions=max_value - 1,
            value=initial_value,
            on_change=self.on_slider_change
        )
        self.controls = [self.label, self.slider]

    def on_slider_change(self, e):
        value = int(e.control.value)
        PageProperties.set_slider_value(PageProperties.theme_mode, value)
        if PageProperties.theme_mode == ft.ThemeMode.DARK:
            color = self.DARK_THEME_COLORS[value - 1]
        else:
            color = self.LIGHT_THEME_COLORS[value - 1]      
        PageProperties.set_bgcolor(PageProperties.theme_mode, color)
        set_theme_from_bgcolor(self.page, color)
        self.page.client_storage.set(f"{PageProperties.theme_mode.value}_theme_slider_value", value)
        self.page.client_storage.set(f"{PageProperties.theme_mode.value}_theme_bgcolor", color)
        self.page.update()
        
    def update_slider_position(self):
        self.slider.value = PageProperties.get_slider_value()
        self.slider.update()
        
    def did_mount(self):
        self.update_slider_position()

class SettingsControl(ft.Column):
    #BUTTON_HEIGHT = 60
    #FONT_SIZE_BUTTON = 15
    def __init__(self, page):
        super().__init__()
        self.spacing = 60
        
        self.page = page
        self.drawer = PageProperties.get_drawer()
        
        # menu button
        self.menu_button = ft.IconButton(
            icon=ft.Icons.MENU,
            on_click=self.on_menu_click,
            icon_color=ft.Colors.WHITE
        )
        
        # theme dropdown
        self.theme_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option(ft.ThemeMode.DARK, "Dark"),
                ft.dropdown.Option(ft.ThemeMode.LIGHT, "Light")
            ],
            value=PageProperties.theme_mode,
            border_color=ft.Colors.TEAL_800,
            on_change=self.on_theme_change
        )
        
        # background shade slider
        initial_value = PageProperties.get_slider_value()
        self.background_shade_slider = BackgroundShadeSlider(
            label="Background Shade",
            initial_value=initial_value,
        )
        
        # Add elements in column to container
        self.controls = [
            self.theme_dropdown,
            self.background_shade_slider
        ]
        
        self.__update_controls_width()
        
                
    def __update_controls_width(self):
        width = PageProperties.width * 0.7
        for control in self.controls:
            control.width = width
    
    def on_menu_click(self, e):
        self.page.open(self.drawer)
    
    def on_theme_change(self, e):
        selected_theme = e.control.value
        if selected_theme == str(ft.ThemeMode.DARK):
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.client_storage.set("theme_mode", ft.ThemeMode.DARK.value)
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.client_storage.set("theme_mode", ft.ThemeMode.LIGHT.value)
            
        PageProperties.set_theme_from_page(self.page)
        bgcolor = PageProperties.get_bgcolor()
        set_theme_from_bgcolor(self.page, bgcolor)
        self.page.update()
        self.background_shade_slider.update_slider_position()
    
    def did_mount(self):
        appbar = self.page.appbar
        appbar.leading = self.menu_button
        appbar.title.value = "Settings"
        
        self.page.bottom_appbar.visible = False
        self.page.floating_action_button.visible = False
        self.page.update()
        
    def will_unmount(self):
        self.__update_controls_width()
        appbar = self.page.appbar
        appbar.leading = None
        self.page.update()