import flet as ft

from learning_app.data.constants import WordDefinitions
from learning_app.tts import TtsError, TtsNetworkError
from learning_app.ui.app_session import AppSession
from learning_app.ui.components.base_word_field import BaseWordField
from learning_app.ui.components.controls import ProgressBar, WordField
from learning_app.ui.keyboard_shortcuts import pop_ctrl_s_action, push_ctrl_s_action
from learning_app.ui.layout_host import control_is_on_page
from learning_app.ui.layout_metrics import (
    LayoutMetrics,
    LayoutMetricsStore,
    is_windows_platform,
    learn_definition_field_width,
)
from learning_app.ui.layout_tokens import LEARN_DEFINITION_CHECK_BUTTON_SCALE
from learning_app.ui.screens.word_list_menu import WordListMenu
from learning_app.ui.tts_preferences import TtsPreferences


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
        self.checkButton = ft.Button(
            content="Start",
            on_click=self.on_check_click,
            tooltip="Ctrl+Enter",
        )
        self.speakButton = ft.IconButton(
            icon=ft.Icons.VOLUME_UP,
            tooltip="Pronounce word (Ctrl+S)",
            on_click=self.on_speak_click,
            disabled=True,
        )
        self._speak_unlocked = False
        self._ctrl_s_registered = False
        self.check_row = ft.Row(
            controls=[self.checkButton, self.speakButton],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.pb = ProgressBar(width=field_width)

        if not is_windows_platform(page):
            self.checkButton.scale = LEARN_DEFINITION_CHECK_BUTTON_SCALE

        self.active_controls = [
            self.pb,
            self.definitionLabel,
            self.word,
            self.check_row,
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
        self._set_speak_unlocked(False)
        self.update()

    def prepare_retry(self):
        self.word.reset()
        self._set_speak_unlocked(False)

    def focus_first_empty_input(self):
        if self.word.is_awaiting_input():
            self._focus_field(self.word)

    def _register_ctrl_enter(self):
        super()._register_ctrl_enter()
        if self._ctrl_s_registered:
            return
        push_ctrl_s_action(self._get_page(), self._on_ctrl_s)
        self._ctrl_s_registered = True

    def _unregister_ctrl_enter(self):
        if self._ctrl_s_registered:
            pop_ctrl_s_action(self._get_page(), self._on_ctrl_s)
            self._ctrl_s_registered = False
        super()._unregister_ctrl_enter()

    def _on_ctrl_s(self, e):
        if not self._session_active or not self._speak_unlocked:
            return
        if getattr(self.speakButton, "disabled", False):
            return
        page = self._get_page()
        if page is not None and hasattr(page, "run_task"):
            page.run_task(self._speak_current_word, True)

    def on_check_click(self, e):
        super().on_check_click(e)
        revealed = self._answer_is_revealed()
        self._set_speak_unlocked(revealed)
        if control_is_on_page(self):
            self.update()
        if revealed and TtsPreferences.auto_speak_definitions:
            page = self._get_page()
            if page is not None:
                page.run_task(self._speak_current_word, False)

    def _set_speak_unlocked(self, unlocked: bool) -> None:
        self._speak_unlocked = unlocked
        self.speakButton.disabled = not unlocked

    async def on_speak_click(self, e):
        await self._speak_current_word(True)

    async def _speak_current_word(self, notify_errors: bool):
        if not self._speak_unlocked:
            return
        word = self.words.get_current_row()[WordDefinitions.WORD.value]
        if word is None or str(word).strip() in ("", "nan"):
            return

        self.speakButton.disabled = True
        if control_is_on_page(self):
            self.update()
        try:
            await AppSession.speak(str(word), TtsPreferences.language)
        except TtsNetworkError:
            if notify_errors:
                self._show_tts_error("Could not play pronunciation. Check your internet connection.")
        except TtsError:
            if notify_errors:
                self._show_tts_error("Could not play pronunciation.")
        finally:
            self.speakButton.disabled = not self._speak_unlocked
            if control_is_on_page(self):
                self.update()

    def _show_tts_error(self, message: str) -> None:
        page = self._get_page()
        if page is None:
            return
        page.show_dialog(ft.SnackBar(content=ft.Text(message)))
