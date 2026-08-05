import flet as ft
import pandas as pd

from learning_app.data.app_data import create_empty_set, get_kind_of_file_and_validate, load_set, save_set
from learning_app.data.constants import MAX_ROWS, PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.components.edit_cards import EditCardDefinitions, EditCardWords
from learning_app.ui.layout_metrics import LayoutMetrics
from learning_app.ui.navigation import go_back, navigate_to, reanchor_edit_on_home
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.routable_screen import RoutableScreenMixin
from learning_app.ui.route_paths import HOME_ROUTE


class EditSetMenu(RoutableScreenMixin, ft.Column):
    MAX_CARDS = MAX_ROWS

    def __init__(self, file_name: str, width=340, title=None, subtitle=None):
        super().__init__()
        self.expand = True
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 20
        self.edited = False
        self.file_name = file_name
        self.title = title
        self.subtitle = subtitle
        self._from_create = title is not None
        self._form_width = width

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
        self.save_button = ft.Button(
            content="Save",
            on_click=self.on_save_click,
            icon=ft.Icons.SAVE,
        )
        buttons = [self.backButton, self.save_button]
        if self.kind == "definitions":
            self.swap_all_button = ft.FilledTonalButton(
                content="Swap all",
                icon=ft.Icons.SWAP_VERT,
                on_click=self.on_swap_all_click,
            )
            buttons.append(self.swap_all_button)
        self.buttons_row = ft.Row(
            controls=buttons,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.lv = ft.ListView(
            controls=[self.addButton],
            expand=True,
            auto_scroll=True,
        )
        self.lv.edited = False
        self.lv.deleted_indexes = []

        self.main_container = ft.Container(
            content=self.lv,
            width=width,
            expand=True,
        )

        if title is None:
            words = load_set(file_name)
            assert len(words) <= self.MAX_CARDS, f"Error: The file contains more than {self.MAX_CARDS} cards."
        else:
            words = create_empty_set(self.kind)

        self.__populate_cards(words)

        self.controls = [
            self.main_container,
            self.buttons_row,
        ]

    def __populate_cards(self, words):
        self.lv.controls.clear()
        self.lv.edited = False
        self.lv.deleted_indexes = []

        for i in range(len(words)):
            if self.kind == "words":
                self.lv.controls.append(EditCardWords(self.lv, words_row=words.iloc[i]))
            elif self.kind == "definitions":
                self.lv.controls.append(EditCardDefinitions(self.lv, words_row=words.iloc[i]))

        self.lv.controls.append(self.addButton)

    def __reload_cards(self):
        words = load_set(self.file_name)
        self.__populate_cards(words)

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        metrics = self.resolve_layout_metrics(metrics)
        self._form_width = metrics.form_width
        self.main_container.width = metrics.form_width
        self.update_if_mounted()

    def on_swap_all_click(self, e):
        for control in self.lv.controls:
            if isinstance(control, EditCardDefinitions):
                control.swap_word_and_definition()
        e.page.update()

    def on_add_click(self, e):
        if len(self.lv.controls) - 1 >= self.MAX_CARDS:
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
        return False

    def __has_changes(self):
        return self.lv.edited or any(
            isinstance(control, (EditCardWords, EditCardDefinitions)) and control.has_changes()
            for control in self.lv.controls
        )

    def __validate_for_save(self, e):
        if self.__no_cards(e):
            return False

        if not self.__is_valid():
            create_alert_dialog(
                page=e.page,
                title="Invalid Data",
                content="Some cards have less than two text fields filled.",
                close_button_text="OK",
            )
            return False

        return True

    def on_save_click(self, e):
        if not self.__validate_for_save(e):
            return

        if not self.__has_changes():
            return

        self.__save_changes(e, leave=False)

    def __save_changes(self, e, *, leave=False):
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

        self.lv.deleted_indexes.clear()
        self.lv.edited = False

        new_df = pd.DataFrame(new_data, columns=all_columns)

        if not new_df.empty:
            existing_data = pd.concat([existing_data, new_df], ignore_index=True)

        existing_data = existing_data.reset_index(drop=True)

        first_create_save = self.title is not None
        if first_create_save:
            from learning_app.data.app_data import AppData
            AppData.create_data_file_words(
                self.file_name,
                title=self.title,
                subtitle=self.subtitle if self.subtitle is not None else "",
            )
            self.title = None
            self.subtitle = None

        save_set(existing_data, self.file_name)

        e.page.show_dialog(ft.SnackBar(
            content=ft.Text("Changes saved"),
            bgcolor=ft.Colors.TEAL_600,
        ))

        if leave:
            navigate_to(e.page, HOME_ROUTE)
        else:
            if first_create_save:
                reanchor_edit_on_home(e.page, self.file_name)
            self.__reload_cards()

        e.page.update()

    def __save_and_leave(self, e):
        if not self.__validate_for_save(e):
            return
        self.__save_changes(e, leave=True)

    def on_back_click(self, e):
        if not self.__has_changes():
            go_back(e.page)
            return

        create_alert_dialog(
            page=e.page,
            title="Unsaved changes",
            content="You have unsaved changes. Leave without saving?",
            close_button_text="Cancel",
            secondary_button_text="Don't save",
            secondary_action_function=lambda event: go_back(event.page),
            action_button_text="Save",
            action_function=self.__save_and_leave,
        )
