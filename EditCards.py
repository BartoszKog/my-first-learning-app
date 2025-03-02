import flet as ft
from constants import PartsOfSpeech, WordDefinitions
from PageProperties import PageProperties

class EditCardBase(ft.Card):
    def __init__(self, lv_parent: ft.ListView, width: int, fields: dict, words_row=None):
        super().__init__()
        self.margin = 10
        self.index = None  # to check index from file
        self.font_text_field_color_dark_theme = ft.Colors.TEAL_200
        self.font_text_field_color_light_theme = ft.Colors.BLUE_ACCENT_700

        self.dict_word_fields = {label: field for label, field in fields.items()}

        for label, word_field in self.dict_word_fields.items():
            word_field.label = label.capitalize()
            word_field.width = width
            word_field.on_change = self.validate_fields

        self.error_label = ft.Text(value="", color="red")

        self.edited = True

        if words_row is not None:
            self.index = words_row.name

            for label, word_field in self.dict_word_fields.items():
                if isinstance(words_row[label], str):
                    word_field.value = words_row[label]
                else:
                    word_field.value = ""

            self.edited = False
            self.error_label.value = "This card is not edited yet"
            self.error_label.color = "blue"

        def on_delete_click(e):
            lv_parent.auto_scroll = False
            lv_parent.controls.remove(self)
            lv_parent.scroll_to(delta=30)

            snackbar_word = self.dict_word_fields[list(fields.keys())[0]].value
            for label in list(fields.keys())[1:]:
                if snackbar_word == "":
                    snackbar_word = self.dict_word_fields[label].value

            if snackbar_word == "":
                snackbar_word = "Card"

            e.page.snack_bar = ft.SnackBar(
                ft.Text(f"{snackbar_word.capitalize()} deleted"),
                bgcolor=ft.Colors.TEAL_600
            )
            e.page.snack_bar.open = True

            e.page.update()

            lv_parent.edited = True

            if self.index is not None:
                lv_parent.deleted_indexes.append(self.index)

        self.delete_button = ft.ElevatedButton(text="Delete", on_click=on_delete_click, icon=ft.Icons.DELETE)

        controls_column = ft.Column(
            controls=[
                ft.Text(size=5)
            ]
        )
        controls_column.controls.extend(self.dict_word_fields.values()) 
        
        controls_column.controls.append(self.delete_button)
        controls_column.controls.append(self.error_label)
        controls_column.controls.append(ft.Text(size=5))
        controls_column.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.content = controls_column

        self.validate_fields()

    def __two_fields_filled(self):
        filled_count = sum(1 for field in self.dict_word_fields.values() if field.value.strip())
        return filled_count >= 2

    def validate_fields(self, e=None):
        if e:
            self.edited = True
            self.error_label.value = ""
            self.error_label.visible = False

        for label, field in self.dict_word_fields.items():
            if field.value.strip():
                if PageProperties.dark_mode:
                    field.color = self.font_text_field_color_dark_theme
                else:
                    field.color = self.font_text_field_color_light_theme

        if not self.__two_fields_filled():
            self.error_label.visible = True
            self.error_label.value = "At least two fields must be filled with text"
            self.error_label.color = "red"
        if e:
            e.page.update()

    def is_valid(self):
        return self.__two_fields_filled()

    def get_values(self):
        return {label: field.value.strip() for label, field in self.dict_word_fields.items()}

    def has_changes(self):
        return self.edited

    def get_index(self):
        return self.index


class EditCardWords(EditCardBase):
    def __init__(self, lv_parent: ft.ListView, width: int = 250, words_row=None):
        fields = {
            PartsOfSpeech.VERB.value: ft.TextField(),
            PartsOfSpeech.PERSON.value: ft.TextField(),
            PartsOfSpeech.THING.value: ft.TextField(),
            PartsOfSpeech.ADJECTIVE.value: ft.TextField(),
            PartsOfSpeech.ADVERB.value: ft.TextField()
        }
        super().__init__(lv_parent, width, fields, words_row)


class EditCardDefinitions(EditCardBase):
    def __init__(self, lv_parent: ft.ListView, width: int = 250, words_row=None):
        fields = {
            WordDefinitions.WORD.value: ft.TextField(),
            WordDefinitions.DEFINITION.value: ft.TextField(
                multiline=True,
                min_lines=1,
                max_lines=6,
                shift_enter=True
            )
        }
        super().__init__(lv_parent, width, fields, words_row)