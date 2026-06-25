import random as rd
from typing import Dict

import flet as ft

from learning_app.ui.components.base_word_field import BaseWordField
from learning_app.ui.components.controls import ProgressBar, WordField
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore, learn_words_field_width
from learning_app.ui.screens.word_list_menu import WordListMenu


class WordFields(BaseWordField):
    def __init__(self, file_name: str = "data_words.csv", page=None, width=300, session=False):
        super().__init__(file_name, page, session=session)
        if not session:
            self.expand = True

        self._form_width = width
        field_width = learn_words_field_width(width, page)

        self.dict_word_fields: Dict[str, WordField] = {}

        self.Word = ft.Text("Word", theme_style=ft.TextThemeStyle.TITLE_LARGE)
        self.verbWord = WordField(label="Verb", width=field_width)
        self.nounPersonWord = WordField(label="Noun (person)", width=field_width)
        self.nounThingWord = WordField(label="Noun (thing)", width=field_width)
        self.adjWord = WordField(label="Adjective", width=field_width)
        self.advWord = WordField(label="Adverb", width=field_width)
        self.checkButton = ft.Button(content="Start", on_click=self.on_check_click)
        self.pb = ProgressBar(width=field_width)

        self.dict_word_fields = {
            "verb": self.verbWord,
            "person": self.nounPersonWord,
            "thing": self.nounThingWord,
            "adjective": self.adjWord,
            "adverb": self.advWord,
        }

        self.active_controls = [
            self.pb,
            ft.Row([self.Word, self.checkButton], alignment=ft.MainAxisAlignment.CENTER),
            self.verbWord,
            self.nounPersonWord,
            self.nounThingWord,
            self.adjWord,
            self.advWord,
        ]

        self.menu_control = WordListMenu(file_name, on_back=self.back, width=width)
        self.controls = [self.menu_control] if not session else []

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        if metrics is None:
            metrics = LayoutMetricsStore.refresh(self._get_page())
        self._form_width = metrics.form_width
        field_width = learn_words_field_width(metrics.form_width, self._get_page())
        for word_field in self.dict_word_fields.values():
            word_field.width = field_width
        self.pb.width = field_width
        if self.menu_control in self.controls:
            self.menu_control.apply_layout(metrics)
        elif control_is_on_page(self):
            self.update()

    def compare_all_words(self):
        all_correct = True
        row_without_nan = self.words.get_current_row()
        for column_name in row_without_nan.index:
            word_field = self.dict_word_fields[column_name]
            word_class = self.words.get_current_row()[column_name]
            if word_field.contain_word(word_class):
                word_field.indicate_good_answer(word_class)
            else:
                word_field.indicate_bad_answer(word_class)
                all_correct = False
        return all_correct

    def set_next_word(self):
        if self.words.it_is_not_last_index_of_group():
            self.words.draw_new_row()
            word_label = rd.choice(self.words.get_current_words_list())
            if "/" in word_label:
                self.Word.value = rd.choice(word_label.split("/"))
            else:
                self.Word.value = word_label
            for colname in self.words.colnames_in_WordFields():
                self.dict_word_fields[colname].reset()
            for nan_colname in self.words.colnames_with_nan():
                self.dict_word_fields[nan_colname].disable()
        else:
            self.menu()
        self.update()
