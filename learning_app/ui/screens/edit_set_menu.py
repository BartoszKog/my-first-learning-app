import flet as ft
import pandas as pd

from learning_app.data.app_data import create_empty_set, get_kind_of_file_and_validate, load_set, save_set
from learning_app.data.constants import MAX_ROWS, PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.components.edit_cards import EditCardDefinitions, EditCardWords
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.page_properties import PageProperties


class EditSetMenu(ft.Column):
    MAX_CARDS = MAX_ROWS
    HEIGHT_FACTOR = 0.8
    DEFAULT_APPBAR_HEIGHT = 100
    DEFAULT_BOTTOM_APPBAR_HEIGHT = 80

    def __init__(self, file_name: str, width=340, title=None, subtitle=None):
        super().__init__()
        self.alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.edited = False
        self.file_name = file_name
        self.title = title
        self.subtitle = subtitle

        # get kind of file and validate based on file_name
        self.kind = get_kind_of_file_and_validate(file_name)

        self.addButton = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=ft.Colors.TEAL_900,
            on_click=self.on_add_click,
            foreground_color=ft.Colors.WHITE,
        )
        self.backButton = ft.Button(
            content="Back",
            on_click=self.on_back_click,
            icon=ft.Icons.ARROW_BACK,
        )
        self.ok_button = ft.Button(
            content="OK",
            on_click=self.on_ok_click,
            icon=ft.Icons.CHECK,
        )
        self.buttons_row = ft.Row(
            controls=[
                self.backButton,
                self.ok_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.lv = ft.ListView(
            controls=[self.addButton],
            auto_scroll=True,
        )
        self.lv.edited = False  # to check when some card is deleted, logic is in EditCardWords
        self.lv.deleted_indexes = []  # to store indexes of deleted cards

        self.main_container = ft.Container(
            content=self.lv,
            width=width,
            height=PageProperties.height * self.HEIGHT_FACTOR,
        )

        if title is None:
            words = load_set(file_name)
            assert len(words) <= self.MAX_CARDS, f"Error: The file contains more than {self.MAX_CARDS} cards."
        else:
            words = create_empty_set(self.kind)

        words_columns = [
            PartsOfSpeech.VERB.value,
            PartsOfSpeech.PERSON.value,
            PartsOfSpeech.THING.value,
            PartsOfSpeech.ADJECTIVE.value,
            PartsOfSpeech.ADVERB.value,
        ]

        definitions_columns = [
            WordDefinitions.WORD.value,
            WordDefinitions.DEFINITION.value,
        ]

        for i in range(len(words)):
            words_row = words.iloc[i]
            if self.kind == "words":
                words_row = words_row[words_columns]
                self.lv.controls.append(EditCardWords(self.lv, words_row=words.iloc[i]))
            elif self.kind == "definitions":
                words_row = words_row[definitions_columns]
                self.lv.controls.append(EditCardDefinitions(self.lv, words_row=words.iloc[i]))
        # make button bottom
        self.lv.controls.remove(self.addButton)
        self.lv.controls.append(self.addButton)

        self.controls = [
            self.main_container,
            self.buttons_row,
        ]

    def did_mount(self):
        self.__sync_height_to_page(self.page)
        self.update()

    def on_add_click(self, e):
        if len(self.lv.controls) - 1 >= self.MAX_CARDS:  # -1 because addButton is also in controls
            create_alert_dialog(
                page=e.page,
                title="Alert",
                content=f"Cannot add more than {self.MAX_CARDS} cards.",
                close_button_text="OK",
            )
            return

        self.lv.auto_scroll = True
        self.lv.controls.remove(self.addButton)
        if self.kind == "words":
            self.lv.controls.append(EditCardWords(self.lv))
        elif self.kind == "definitions":
            self.lv.controls.append(EditCardDefinitions(self.lv))

        self.lv.controls.append(self.addButton)
        self.update()

    def __is_valid(self):
        for control in self.lv.controls:
            if isinstance(control, (EditCardWords, EditCardDefinitions)):
                if not control.is_valid():
                    return False

        return True

    def __no_cards(self, e):
        if len(self.lv.controls) == 1:
            create_alert_dialog(
                page=e.page,
                title="Alert",
                content="Cannot save changes with no cards.",
                close_button_text="OK",
            )
            return True

    def on_ok_click(self, e):
        if self.__no_cards(e):
            return

        if not self.__is_valid():
            create_alert_dialog(
                page=e.page,
                title="Invalid Data",
                content="Some cards have less than two text fields filled.",
                close_button_text="OK",
            )
            return

        changes_detected = self.lv.edited or any(isinstance(control, (EditCardWords, EditCardDefinitions)) and control.has_changes() for control in self.lv.controls)

        if changes_detected:
            create_alert_dialog(
                page=e.page,
                title="Confirm",
                content="Do you want to save the changes?",
                close_button_text="Cancel",
                action_button_text="OK",
                action_function=self.__save_changes,
            )
        else:
            self.__save_changes(e)

    def __save_changes(self, e, dialog=None):
        def delete_row_at(df, index):
            if index is None:
                return df
            return df.drop(index)

        if self.title is None:
            existing_data = load_set(self.file_name)
        else:
            existing_data = create_empty_set(self.kind)

        words_columns = []

        if self.kind == "words":
            words_columns.extend([
                PartsOfSpeech.VERB.value,
                PartsOfSpeech.PERSON.value,
                PartsOfSpeech.THING.value,
                PartsOfSpeech.ADJECTIVE.value,
                PartsOfSpeech.ADVERB.value,
            ])
        elif self.kind == "definitions":
            words_columns.extend([
                WordDefinitions.WORD.value,
                WordDefinitions.DEFINITION.value,
            ])

        all_columns = words_columns + [
            StatsColumns.CORRECT_ANSWERS.value,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
            StatsColumns.GOOD_ANSWER.value,
            StatsColumns.WORD_TO_LEARN.value,
        ]

        new_data = []

        for control in self.lv.controls:
            if isinstance(control, (EditCardWords, EditCardDefinitions)):
                values = control.get_values()
                changed = control.has_changes()
                index = control.get_index()

                if values and changed:
                    existing_data = delete_row_at(existing_data, index)

                    values.update({
                        StatsColumns.CORRECT_ANSWERS.value: 0,
                        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
                        StatsColumns.GOOD_ANSWER.value: False,
                        StatsColumns.WORD_TO_LEARN.value: False,
                    })
                    new_data.append(values)

        for index in self.lv.deleted_indexes:
            existing_data = delete_row_at(existing_data, index)

        # set default values involved with deleted cards
        self.lv.deleted_indexes.clear()
        self.lv.edited = False

        new_df = pd.DataFrame(new_data, columns=all_columns)

        if not new_df.empty:
            existing_data = pd.concat([existing_data, new_df], ignore_index=True)

        # reset index
        existing_data = existing_data.reset_index(drop=True)

        if self.title is not None:
            from learning_app.data.app_data import AppData
            AppData.create_data_file_words(
                self.file_name,
                title=self.title,
                subtitle=self.subtitle if self.subtitle is not None else "",
            )

        save_set(existing_data, self.file_name)

        if dialog:
            e.page.pop_dialog()

        from learning_app.ui.components.tiles_container import TilesContainer
        TilesContainer.back_to_main_menu(e)
        e.page.update()

    def on_back_click(self, e):
        from learning_app.ui.components.tiles_container import TilesContainer
        TilesContainer.back_to_main_menu(e)

    def change_height(self, height_or_page):
        if hasattr(height_or_page, "window"):
            self.__sync_height_to_page(height_or_page)
        else:
            self.main_container.height = height_or_page
        self.update()

    def __sync_height_to_page(self, page):
        if page is not None:
            PageProperties.set_width_height_from_page(page)
        self.main_container.height = self.__get_available_height(page) * self.HEIGHT_FACTOR

    def __get_available_height(self, page=None):
        if page is None:
            return PageProperties.height

        window_height = page.window.height if getattr(page, "window", None) and page.window.height else page.height
        if not window_height:
            return PageProperties.height

        occupied_height = 0
        if page.appbar and getattr(page.appbar, "visible", True):
            occupied_height += (
                getattr(page.appbar, "toolbar_height", None)
                or getattr(page.appbar, "height", None)
                or self.DEFAULT_APPBAR_HEIGHT
            )
        if page.bottom_appbar and getattr(page.bottom_appbar, "visible", True):
            occupied_height += getattr(page.bottom_appbar, "height", None) or self.DEFAULT_BOTTOM_APPBAR_HEIGHT

        padding = page.padding
        if padding:
            occupied_height += (padding.top or 0) + (padding.bottom or 0)

        return max(window_height - occupied_height, 0)
