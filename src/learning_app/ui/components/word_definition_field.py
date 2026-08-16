import flet as ft

from learning_app.data.constants import WordDefinitions
from learning_app.ui.components.base_word_field import BaseWordField
from learning_app.ui.components.controls import ProgressBar, WordField
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import (
    LayoutMetrics,
    LayoutMetricsStore,
    is_windows_platform,
    learn_definition_field_width,
)
from learning_app.ui.layout_tokens import LEARN_DEFINITION_CHECK_BUTTON_SCALE
from learning_app.ui.screens.word_list_menu import WordListMenu


class WordDefinitionField(BaseWordField):
    """Learn UI for a ``*_definitions.csv`` set (definition → word).

    Shows the definition prompt and a single answer field, with progress and
    the optional ``WordListMenu`` when ``session`` is ``False``.
    """

    def __init__(self, file_name, page=None, width=300, session=False):
        super().__init__(file_name, page, session=session)
        if not session:
            self.expand = True

        self._form_width = width
        field_width = learn_definition_field_width(width, page)

        self.definitionLabel = ft.Text(
            theme_style=ft.TextThemeStyle.TITLE_LARGE,
            text_align=ft.TextAlign.CENTER,
        )
        self.word = WordField(label="", width=field_width)
        self.word.text_size = 30
        self.word.text_align = ft.TextAlign.CENTER
        self.checkButton = ft.Button(content="Start", on_click=self.on_check_click)
        self.pb = ProgressBar(width=field_width)

        if not is_windows_platform(page):
            self.checkButton.scale = LEARN_DEFINITION_CHECK_BUTTON_SCALE

        self.active_controls = [
            self.pb,
            self.definitionLabel,
            self.word,
            self.checkButton,
        ]

        self.menu_control = WordListMenu(file_name, on_back=self.back, width=width)
        self.controls = [self.menu_control] if not session else []

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        if metrics is None:
            metrics = LayoutMetricsStore.refresh(self._get_page())
        self._form_width = metrics.form_width
        field_width = learn_definition_field_width(metrics.form_width, self._get_page())
        self.word.width = field_width
        self.pb.width = field_width
        if self.menu_control in self.controls:
            self.menu_control.apply_layout(metrics)
        elif control_is_on_page(self):
            self.update()

    def compare_all_words(self):
        good_word = self.words.get_current_row()[WordDefinitions.WORD.value]
        if self.word.contain_word(good_word):
            self.word.indicate_good_answer(good_word)
            return True
        else:
            self.word.indicate_bad_answer(good_word)
            return False

    def set_next_word(self):
        if self.words.it_is_not_last_index_of_group():
            self.words.draw_new_row()
            self.definitionLabel.value = self.words.get_current_row()[WordDefinitions.DEFINITION.value]
            self.word.reset()
        else:
            self.menu()
        self.update()
