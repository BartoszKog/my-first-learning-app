import flet as ft
import random as rd
from typing import Dict
from Controls import WordField, ProgressBar
from WordListMenu import WordListMenu
from BaseWordField import BaseWordField
from PageProperties import PageProperties

class WordFields(BaseWordField):
    def __init__(self, file_name: str = "data_words.csv", page=None, width=300):
        super().__init__(file_name, page)
        factor = 0.90
        if PageProperties.platform == ft.PagePlatform.WINDOWS:
            factor = 0.83
            
        self.dict_word_fields: Dict[str, WordField] = {}

        self.Word = ft.Text("Word", theme_style=ft.TextThemeStyle.TITLE_LARGE)
        self.verbWord = WordField(label="Verb", width=factor*width)
        self.nounPersonWord = WordField(label="Noun (person)", width=factor*width)
        self.nounThingWord = WordField(label="Noun (thing)", width=factor*width)
        self.adjWord = WordField(label="Adjective", width=factor*width)
        self.advWord = WordField(label="Adverb", width=factor*width)
        self.checkButton = ft.ElevatedButton(text="Start", on_click=self.on_check_click)
        self.pb = ProgressBar(width=width*factor)

        self.dict_word_fields = {
            "verb": self.verbWord,
            "person": self.nounPersonWord,
            "thing": self.nounThingWord,
            "adjective": self.adjWord,
            "adverb": self.advWord
        }

        self.active_controls = [
            self.pb,
            ft.Row([self.Word, self.checkButton], alignment=ft.MainAxisAlignment.CENTER),
            self.verbWord,
            self.nounPersonWord,
            self.nounThingWord,
            self.adjWord,
            self.advWord
        ]

        self.menu_control = WordListMenu(file_name, on_start=self.start, on_back=self.back, width=width)
        self.controls = [self.menu_control]

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