import flet as ft
from Controls import WordField, ProgressBar
from WordListMenu import WordListMenu
from constants import WordDefinitions
from BaseWordField import BaseWordField
from PageProperties import PageProperties

class WordDefinitionField(BaseWordField):
    def __init__(self, file_name, page=None, width=300):
        super().__init__(file_name, page)
        factor = 0.90
        if PageProperties.platform == ft.PagePlatform.WINDOWS:
            factor = 0.80

        self.definitionLabel = ft.Text(theme_style=ft.TextThemeStyle.TITLE_LARGE)
        self.word = WordField(label="", width=factor*width)
        self.word.text_size = 30
        self.word.text_align = ft.TextAlign.CENTER
        self.checkButton = ft.ElevatedButton(text="Start", on_click=self.on_check_click)
        self.pb = ProgressBar(width=width*factor)
        
        if not PageProperties.platform == ft.PagePlatform.WINDOWS:
            self.checkButton.scale = 1.3

        self.active_controls = [
            self.pb,
            self.definitionLabel,
            self.word,
            self.checkButton
        ]

        self.menu_control = WordListMenu(file_name, on_start=self.start, on_back=self.back, width=width)
        self.controls = [self.menu_control]

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