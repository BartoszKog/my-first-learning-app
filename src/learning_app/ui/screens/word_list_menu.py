from typing import Dict

import flet as ft

from learning_app.data.app_data import AppData, get_kind_of_file_and_validate, set_default_progress
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.tts import TtsError, TtsNetworkError
from learning_app.ui.app_session import AppSession
from learning_app.ui.components.controls import ProgressBar
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import LayoutMetrics, LayoutMetricsStore
from learning_app.ui.app_theme import AppTheme
from learning_app.ui.keyboard_shortcuts import pop_ctrl_enter_action, push_ctrl_enter_action
from learning_app.ui.navigation import go_back, push_view
from learning_app.ui.page_functions import create_alert_dialog
from learning_app.ui.route_paths import SET_LEARN_SESSION_ROUTE
from learning_app.ui.tts_preferences import TtsPreferences

BORDERS = {
    "To learn": ft.Border.all(1.5, ft.Colors.BLUE_GREY_700),
    "Learned": ft.Border.all(1.5, ft.Colors.ORANGE_500),
    "Known": ft.Border.all(1.5, ft.Colors.GREEN_ACCENT_700),
}

COLORS_CHECKS = {
    "All": ft.Colors.RED_ACCENT_700,
    "Previous session": ft.Colors.YELLOW_700,
    "To learn": ft.Colors.LIGHT_BLUE_200,
    "Learned": ft.Colors.ORANGE_500,
    "Known": ft.Colors.GREEN_ACCENT_700,
}

_LABEL_COLOR = ft.Colors.BLUE_GREY_500
_SPEAKER_RESERVE_PX = 40
_WORD_FORMATION_COLUMNS = frozenset(member.value for member in PartsOfSpeech)
_DEFINITION_CONTENT_COLUMNS = frozenset(member.value for member in WordDefinitions)


def _is_blank_cell(value) -> bool:
    return value is None or str(value).strip() in ("", "nan")


def _speaker_enabled_for(column: str) -> bool:
    if column in _WORD_FORMATION_COLUMNS:
        return TtsPreferences.speakers_word_formations
    if column == WordDefinitions.WORD.value:
        return TtsPreferences.speakers_word
    if column == WordDefinitions.DEFINITION.value:
        return TtsPreferences.speakers_definition
    return False


def _wrap_slash_cell(text: str, char_threshold: float) -> str:
    if len(text) <= char_threshold:
        return text
    parts = text.split("/")
    wrapped = parts[0]
    for part in parts[1:]:
        wrapped += "/\n" + part
    return wrapped


def _wrap_space_cell(text: str, char_threshold: float) -> str:
    if len(text) <= char_threshold:
        return text
    list_words = text.split(" ")
    new_word = list_words[0]
    current_line = list_words[0]
    for word_l in list_words[1:]:
        real_last_line = current_line.split("\n")[-1]
        if len(real_last_line + " " + word_l) > char_threshold:
            if "\n" not in word_l:
                new_word += "\n" + word_l
            current_line = word_l
        else:
            new_word += " " + word_l
            current_line += " " + word_l
    return new_word


class WordContainer(ft.Container):
    def __init__(self, words_row, width, was_in_previous_session=False):
        super().__init__()
        # checking if the row have correct columns
        stats_columns = [
            StatsColumns.CORRECT_ANSWERS.value,
            StatsColumns.GOOD_ANSWER.value,
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
            StatsColumns.WORD_TO_LEARN.value,
        ]

        columns_words = [
            PartsOfSpeech.VERB.value,
            PartsOfSpeech.PERSON.value,
            PartsOfSpeech.THING.value,
            PartsOfSpeech.ADJECTIVE.value,
            PartsOfSpeech.ADVERB.value,
        ]

        columns_definitions = [
            WordDefinitions.DEFINITION.value,
            WordDefinitions.WORD.value,
        ]

        columns_words.extend(stats_columns)
        columns_definitions.extend(stats_columns)

        assert all([col in words_row.index for col in columns_words]) or \
            all([col in words_row.index for col in columns_definitions]) \
            , "The row must have correct columns."

        self.padding = 10

        # indicating state (to learn, learned, known)
        self.border_radius = 5

        self.to_learn = words_row[StatsColumns.GOOD_ANSWER.value] == False \
            and words_row[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False \
            and words_row[StatsColumns.WORD_TO_LEARN.value] == False

        self.known = words_row[StatsColumns.GOOD_ANSWER.value] == True \
            and words_row[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == True \
            and words_row[StatsColumns.WORD_TO_LEARN.value] == False

        self.in_previous_session = was_in_previous_session

        if self.to_learn:
            # indicating by gray border
            self.border = BORDERS["To learn"]
        elif self.known:
            # indicating by green border
            self.border = BORDERS["Known"]
        else:
            # indicating by orange border learned words
            self.border = BORDERS["Learned"]

        # dropping NaN values
        words_row = words_row.dropna()

        for _col in list(words_row.index):
            if _col in stats_columns:
                continue
            _val = words_row[_col]
            if not isinstance(_val, str):
                words_row[_col] = str(_val)

        # creating dictionary with index names where the length of the index name is equal to the max length
        dict_index_names = {  # it is used to make the columns the same width
            PartsOfSpeech.VERB.value: "Verb         ",
            PartsOfSpeech.PERSON.value: "Person     ",
            PartsOfSpeech.THING.value: "Thing       ",
            PartsOfSpeech.ADJECTIVE.value: "Adjective ",
            PartsOfSpeech.ADVERB.value: "Adverb    ",
            WordDefinitions.DEFINITION.value: "Definition ",
            WordDefinitions.WORD.value: "Word        ",
        }

        Column_with_words = ft.Column()

        for word in words_row.index:
            if word in stats_columns:
                continue
            original = words_row[word]
            show_speaker = (not _is_blank_cell(original)) and _speaker_enabled_for(word)
            wrap_width = width - _SPEAKER_RESERVE_PX if show_speaker else width
            char_threshold = 20 / 250 * wrap_width
            if word in _DEFINITION_CONTENT_COLUMNS:
                display = _wrap_space_cell(original, char_threshold)
            else:
                display = _wrap_slash_cell(original, char_threshold)
            row_controls = [
                ft.Text(dict_index_names[word], color=_LABEL_COLOR),
                ft.Text(display, expand=True),
            ]
            if show_speaker:
                row_controls.append(
                    ft.IconButton(
                        icon=ft.Icons.VOLUME_UP,
                        icon_color=_LABEL_COLOR,
                        icon_size=16,
                        padding=0,
                        height=18,
                        visual_density=ft.VisualDensity.COMPACT,
                        size_constraints=ft.BoxConstraints(
                            min_width=18,
                            min_height=18,
                            max_width=18,
                            max_height=18,
                        ),
                        tooltip="Pronounce",
                        on_click=self._make_speak_handler(original),
                    )
                )
            Column_with_words.controls.append(
                ft.Row(
                    row_controls,
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        self.content = Column_with_words

    def _make_speak_handler(self, text: str):
        async def on_click(e):
            await self._speak_cell(e, text)

        return on_click

    async def _speak_cell(self, e, text: str):
        try:
            await AppSession.speak(text, TtsPreferences.language)
        except TtsNetworkError:
            self._show_tts_error(
                getattr(e, "page", None),
                "Could not play pronunciation. Check your internet connection.",
            )
        except TtsError:
            self._show_tts_error(
                getattr(e, "page", None),
                "Could not play pronunciation.",
            )

    def _show_tts_error(self, page, message: str) -> None:
        if page is None:
            return
        page.show_dialog(ft.SnackBar(content=ft.Text(message)))

    def is_to_learn(self):
        return self.to_learn

    def is_known(self):
        return self.known

    def is_learned(self):
        if not self.to_learn and not self.known:
            return True
        else:
            return False

    def was_in_previous_session(self):
        return self.in_previous_session

    def __change_border_width(self, width):
        self.border.top.width = width
        self.border.bottom.width = width
        self.border.left.width = width
        self.border.right.width = width

    def did_mount(self):
        # changing the border width based on the theme mode
        if AppTheme.is_dark_mode():
            self.__change_border_width(1.5)
        else:
            self.__change_border_width(3)


class WordListMenu(ft.Column):
    def __init__(self, file_name: str = "data_words.csv", width: int = 250, on_back=lambda: None):
        super().__init__()
        self.expand = True
        self.file_name = file_name
        self._content_width = width
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.kind = get_kind_of_file_and_validate(file_name)

        self.words = AppData(file_name)
        self.dict_filter_chips: Dict[str, ft.Chip] = {}

        labels_chips = ["All", "Previous session", "Learned", "To learn", "Known"]

        def chip_selected(e):
            # unselecting other chips
            for label in labels_chips:
                if label != e.control.label.value:
                    self.dict_filter_chips[label].selected = False

            self.__update_lv()

        for label in labels_chips:
            self.dict_filter_chips[label] = ft.Chip(
                label=ft.Text(label),
                check_color=COLORS_CHECKS[label],
                on_select=chip_selected,
                selected=True if label == "All" else False,
            )

        self.filter_chips_row = ft.Container(
            width=width + 30,
            height=50,
            content=ft.ListView(
                controls=[self.dict_filter_chips[label] for label in labels_chips],
                horizontal=True,
                spacing=5,
            ),
        )

        self.bp = ProgressBar(
            qty=self.words.number_of_all_words() * 4,
            start=self.words.number_of_known_words() * 4 + self.words.number_of_learning_words() * 1,  # multiply by weights
            word="Progress",
            div_qty=4,
            width=width,
        )

        def reset_progress_and_refresh(e):
            set_default_progress(self.file_name)
            self.words.refresh()
            self.refresh_content()

        self._reset_progress_and_refresh = reset_progress_and_refresh
        self._on_back = on_back

        def on_button_click(e):
            if e.control is self.start_button:
                self.start_learning(e.page)
            elif e.control is self.back_button:
                self._on_back()
                go_back(e.page)

        self.start_button = ft.Button(
            content="Start",
            icon=ft.Icons.PLAY_ARROW,
            on_click=on_button_click,
            tooltip="Start (Ctrl+Enter)",
        )

        self.back_button = ft.Button(
            content="Back",
            icon=ft.Icons.ARROW_BACK,
            on_click=on_button_click,
        )
        self._ctrl_enter_registered = False

        self.lv = ft.ListView(
            expand=True,
            spacing=10,
        )

        self.container = ft.Container(
            content=self.lv,
            padding=10,
            width=width + 30,
            expand=True,
        )

        self.controls = [
            self.bp,
            self.filter_chips_row,
            self.container,
            ft.Row(
                [self.back_button, self.start_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ]

    def start_learning(self, page=None):
        page = page or self.page
        self.words.refresh()
        if self.words.are_all_words_learned():
            create_alert_dialog(
                page=page,
                title="Congratulations, all words learned!",
                content="If you want to start again, set the progress to 0.",
                close_button_text="Close",
                action_button_text="Set progress to 0",
                action_function=self._reset_progress_and_refresh,
            )
        else:
            push_view(page, SET_LEARN_SESSION_ROUTE, file=self.file_name)

    def _on_ctrl_enter(self, e):
        self.start_learning(e.page or self.page)

    def __update_lv(self):
        self.lv.controls.clear()
        for label, chip in self.dict_filter_chips.items():
            if chip.selected:
                self.__add_words_to_list_view(label)
        self.update()

    def __add_words_to_list_view(self, label):
        self.words.refresh()
        for row in self.words.words.iterrows():
            is_in_previous_session = self.words.was_this_index_drawn(row[0])
            wc = WordContainer(
                row[1],
                width=self._content_width,
                was_in_previous_session=is_in_previous_session,
            )
            if self.__should_add_word(label, wc):
                self.lv.controls.append(wc)

    def __should_add_word(self, label, wc):
        if label == "Learned" and wc.is_learned():
            return True
        elif label == "To learn" and wc.is_to_learn():
            return True
        elif label == "Known" and wc.is_known():
            return True
        elif label == "All":
            return True
        elif label == "Previous session" and wc.was_in_previous_session():
            return True
        return False

    def __update_bp(self):
        self.bp.set_certain_qty(self.words.number_of_known_words() * 4 + self.words.number_of_learning_words() * 1)
        self.update()

    def did_mount(self):
        self.apply_layout()
        self.__update_lv()
        self.__update_bp()
        if not self._ctrl_enter_registered:
            push_ctrl_enter_action(self.page, self._on_ctrl_enter)
            self._ctrl_enter_registered = True

    def will_unmount(self):
        if self._ctrl_enter_registered:
            pop_ctrl_enter_action(self.page, self._on_ctrl_enter)
            self._ctrl_enter_registered = False

    def apply_layout(self, metrics: LayoutMetrics | None = None):
        if metrics is None:
            metrics = LayoutMetricsStore.refresh(self.page)
        self._content_width = metrics.form_width
        list_width = metrics.form_width + 30
        self.container.width = list_width
        self.filter_chips_row.width = list_width
        self.bp.width = metrics.form_width
        if control_is_on_page(self):
            self.update()

    def refresh_content(self):
        self.__update_lv()
        self.__update_bp()
        if control_is_on_page(self):
            self.update()
