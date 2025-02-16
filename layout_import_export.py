import flet as ft

class ImportExportControl(ft.Container):
    def __init__(self):
        super().__init__()
        self.last_tab_index = 0
        self.height = 900 * 0.8
        self.width = 500 * 0.9

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
                ft.Container(self.tabs),
                self.body
            ]
        )

        # import controls
        self.title_field = ft.TextField(
            label="Title",
            value="",
            border_color=ft.colors.CYAN
        )

        self.subtitle_field = ft.TextField(
            label="Subtitle",
            value="",
            border_color=ft.colors.CYAN
        )

        self.choose_file_button = ft.ElevatedButton(
            text="Choose file",
            on_click=self.__on_choose_file_click,
            scale=1.25
        )

        self.import_controls = ft.Column(
            [
                ft.Text("Insert the title and additionally a subtitle, then choose a file to import."),
                self.title_field,
                self.subtitle_field,
                self.choose_file_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )

        # export controls
        self.export_controls = ft.Column(
            [
                ft.Text("Choose a set to export."),
                ft.Container(
                    content=ft.Text("Export content here"),
                    bgcolor=ft.colors.LIGHT_GREEN,
                    width=400,
                    height=300
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def __on_choose_file_click(self, e):
        pass

    def __on_change_tab_from_export_to_import_delate_search_control(self):
        pass

    def __on_tab_change(self, e):
        self.__on_change_tab_from_export_to_import_delate_search_control()
        if e.control.selected_index == 0:
            self.__show_import_controls()
        else:
            self.__show_export_controls()
        self.last_tab_index = e.control.selected_index

    def __show_import_controls(self):
        self.body.content = self.import_controls
        self.update()

    def __show_export_controls(self):
        self.body.content = self.export_controls
        self.update()
        
    def did_mount(self):
        self.__show_import_controls()

def main(page: ft.Page):
    page.title = "Import/Export Control Test"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    import_export_control = ImportExportControl()
    page.add(import_export_control)

ft.app(target=main)