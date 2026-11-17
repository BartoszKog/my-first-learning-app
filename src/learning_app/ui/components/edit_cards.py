import asyncio

import flet as ft

from learning_app.data.app_data import _stringify_content_cell
from learning_app.data.constants import (
    EXAMPLE_SENTENCE_COLUMN,
    PartsOfSpeech,
    WordDefinitions,
)
from learning_app.data.example_sentence import (
    example_sentence_error,
    normalize_example_sentence,
    preview_parts,
)
from learning_app.ui.app_theme import AppTheme


class EditCardBase(ft.Card):
    """Editable card for one set row inside create/edit flows.

    Wires labeled fields, tracks whether the user has edited the card, and
    validates required content before save. Prefer subclassing for set kinds
    instead of duplicating field layout in a screen.

    Args:
        lv_parent: Parent ``ListView`` that owns the card list.
        width: Field width in logical pixels.
        fields: Mapping of column name → text field control.
        words_row: Optional existing DataFrame row to preload.
    """

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

        self.error_label = ft.Text(value="", color="red", text_align=ft.TextAlign.CENTER)

        self.edited = True

        if words_row is not None:
            self.index = words_row.name

            for label, word_field in self.dict_word_fields.items():
                text = _stringify_content_cell(words_row[label])
                word_field.value = text if isinstance(text, str) else ""

            self.edited = False
            self.error_label.value = "This card is not edited yet"
            self.error_label.color = "blue"

        def on_delete_click(e):
            async def scroll_after_delete():
                await lv_parent.scroll_to(delta=30)

            lv_parent.auto_scroll = False
            lv_parent.controls.remove(self)
            if hasattr(e.page, "run_task"):
                e.page.run_task(scroll_after_delete)
            else:
                asyncio.create_task(scroll_after_delete())

            snackbar_word = self.dict_word_fields[list(fields.keys())[0]].value
            for label in list(fields.keys())[1:]:
                if snackbar_word == "":
                    snackbar_word = self.dict_word_fields[label].value

            if snackbar_word == "":
                snackbar_word = "Card"

            e.page.show_dialog(ft.SnackBar(
                content=ft.Text(f"{snackbar_word.capitalize()} deleted"),
                bgcolor=ft.Colors.TEAL_600,
            ))
            e.page.update()

            lv_parent.edited = True

            if self.index is not None:
                lv_parent.deleted_indexes.append(self.index)

        self.delete_button = ft.Button(
            content="Delete",
            tooltip="Delete",
            on_click=on_delete_click,
            icon=ft.Icons.DELETE,
        )
        self.action_buttons = ft.Row(
            controls=[self.delete_button],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        controls_column = ft.Column(
            controls=[
                ft.Text(size=5)
            ]
        )
        controls_column.controls.extend(self.dict_word_fields.values())

        controls_column.controls.append(self.action_buttons)
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
                if AppTheme.is_dark_mode():
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

    def invalid_message(self):
        if self.is_valid():
            return None
        return "Some cards have less than two text fields filled."

    def get_values(self):
        return {label: field.value.strip() for label, field in self.dict_word_fields.items()}

    def has_changes(self):
        return self.edited

    def get_index(self):
        return self.index


class EditCardWords(EditCardBase):
    """Edit card with parts-of-speech fields for a words set."""

    def __init__(self, lv_parent: ft.ListView, width: int = 250, words_row=None):
        fields = {
            PartsOfSpeech.VERB.value: ft.TextField(),
            PartsOfSpeech.PERSON.value: ft.TextField(),
            PartsOfSpeech.THING.value: ft.TextField(),
            PartsOfSpeech.ADJECTIVE.value: ft.TextField(),
            PartsOfSpeech.ADVERB.value: ft.TextField(),
        }
        super().__init__(lv_parent, width, fields, words_row)


class EditCardDefinitions(EditCardBase):
    """Edit card with word, definition, and an optional example sentence."""

    def __init__(self, lv_parent: ft.ListView, width: int = 250, words_row=None):
        fields = {
            WordDefinitions.WORD.value: ft.TextField(),
            WordDefinitions.DEFINITION.value: ft.TextField(
                multiline=True,
                min_lines=1,
                max_lines=6,
                shift_enter=True,
            ),
        }
        super().__init__(lv_parent, width, fields, words_row)

        self.swap_button = ft.IconButton(
            icon=ft.Icons.SWAP_VERT,
            tooltip="Swap word and definition",
            on_click=self._on_swap_click,
        )
        self.example_button = ft.IconButton(
            icon=ft.Icons.EDIT_NOTE,
            tooltip="Add example",
            on_click=self._on_example_click,
        )
        self.action_buttons.controls.insert(0, self.swap_button)
        self.action_buttons.controls.insert(1, self.example_button)

        field_width = self.dict_word_fields[WordDefinitions.WORD.value].width
        self.example_help = ft.Text(
            "Use 1 to 4 {} and put a word or phrase inside.",
            width=field_width,
            text_align=ft.TextAlign.CENTER,
            size=12,
        )
        self.example_field = ft.TextField(
            label="Example",
            hint_text="e.g. {Turn} it {off}.",
            width=field_width,
            multiline=True,
            min_lines=1,
            max_lines=4,
            shift_enter=True,
            on_change=self._on_example_change,
        )
        self.example_preview = ft.Text(
            width=field_width,
            text_align=ft.TextAlign.CENTER,
            visible=False,
        )
        self.example_section = ft.Column(
            controls=[self.example_help, self.example_field, self.example_preview],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )
        content_column = self.content
        button_index = content_column.controls.index(self.action_buttons)
        content_column.controls.insert(button_index, self.example_section)

        stored_example = self._stored_example(words_row)
        if stored_example.strip():
            self.example_field.value = stored_example
            self._set_example_open(True)
        self.validate_fields()

    def validate_fields(self, e=None):
        super().validate_fields(e)
        if not hasattr(self, "example_field"):
            return
        self._style_example_field()
        self._refresh_preview()
        self._apply_example_validation()
        if e:
            e.page.update()

    def is_valid(self):
        if not super().is_valid():
            return False
        return example_sentence_error(self.example_field.value or "") is None

    def invalid_message(self):
        if not super().is_valid():
            return "Some cards have less than two text fields filled."
        message = example_sentence_error(self.example_field.value or "")
        if message:
            return f"Example: {message}"
        return None

    def get_values(self):
        values = super().get_values()
        text = self.example_field.value or ""
        if not self.example_section.visible or text.strip() == "":
            values[EXAMPLE_SENTENCE_COLUMN] = ""
            return values
        if example_sentence_error(text):
            values[EXAMPLE_SENTENCE_COLUMN] = text.strip()
            return values
        values[EXAMPLE_SENTENCE_COLUMN] = normalize_example_sentence(text)
        return values

    def swap_word_and_definition(self):
        word_field = self.dict_word_fields[WordDefinitions.WORD.value]
        definition_field = self.dict_word_fields[WordDefinitions.DEFINITION.value]
        word_field.value, definition_field.value = definition_field.value, word_field.value
        self.edited = True
        self.error_label.value = ""
        self.error_label.visible = False
        self.validate_fields()

    def _on_swap_click(self, e):
        self.swap_word_and_definition()
        e.page.update()

    def _on_example_click(self, e):
        if self.example_section.visible:
            self.example_field.value = ""
            self._set_example_open(False)
            self.edited = True
            self.validate_fields(e)
            return
        self._set_example_open(True)
        self._refresh_preview()
        e.page.update()

    def _on_example_change(self, e):
        self.validate_fields(e)

    def _set_example_open(self, open_section: bool):
        self.example_section.visible = open_section
        if open_section:
            self.example_button.icon = ft.Icons.CLOSE
            self.example_button.tooltip = "Remove example"
        else:
            self.example_button.icon = ft.Icons.EDIT_NOTE
            self.example_button.tooltip = "Add example"

    def _stored_example(self, words_row) -> str:
        if words_row is None or EXAMPLE_SENTENCE_COLUMN not in words_row.index:
            return ""
        text = _stringify_content_cell(words_row[EXAMPLE_SENTENCE_COLUMN])
        if not isinstance(text, str):
            return ""
        return text

    def _gap_style(self, color):
        return ft.TextStyle(weight=ft.FontWeight.BOLD, color=color)

    def _gap_color(self):
        if AppTheme.is_dark_mode():
            return self.font_text_field_color_dark_theme
        return self.font_text_field_color_light_theme

    def _style_example_field(self):
        if (self.example_field.value or "").strip():
            self.example_field.color = self._gap_color()

    def _refresh_preview(self):
        text = self.example_field.value or ""
        pieces = preview_parts(text)
        if not pieces:
            self.example_preview.value = ""
            self.example_preview.spans = []
            self.example_preview.visible = False
            return
        self.example_preview.visible = True
        if example_sentence_error(text):
            self.example_preview.value = text
            self.example_preview.spans = []
            return
        self.example_preview.value = ""
        color = self._gap_color()
        self.example_preview.spans = [
            ft.TextSpan(text=piece.text, style=self._gap_style(color) if piece.is_gap else None)
            for piece in pieces
            if piece.text
        ]

    def _apply_example_validation(self):
        message = example_sentence_error(self.example_field.value or "")
        self.example_field.error = message
