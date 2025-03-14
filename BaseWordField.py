import flet as ft
from AppData import AppData, set_default_progress
from page_functions import create_alert_dialog
import threading

class BaseWordField(ft.Column):
    def __init__(self, file_name, page=None):
        super().__init__()
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.words = AppData(file_name)
        self.file_name = file_name
        self.page = page
        self.lock = threading.Lock()

    def menu(self):
        self.controls.clear()
        self.controls.append(self.menu_control)
        self.update()

    def set_default_progress_action(self, e):
        set_default_progress(self.file_name)
        self.menu_control.refresh_content()
        self.words.refresh()
        e.page.update()

    def show_all_words_learned_dialog(self):
        create_alert_dialog(
            page=self.page,
            title="Congratulations, all words learned!",
            content="If you want to start again, set the progress to 0.",
            close_button_text="Close",
            action_button_text="Set progress to 0",
            action_function=self.set_default_progress_action
        )

    def back(self):
        self.words.delete_last_group_of_indexes()

    def start(self):
        if not self.words.are_all_words_learned():
            self.controls.clear()
            self.controls.extend(self.active_controls)
            self.update()
            self.pb.reset()
            self.checkButton.text = "Check"
            length = self.words.draw_index_group(save_indexes_in_class_art=True)
            self.pb.set_max_qty(length)
            self.set_next_word()
        else:
            self.show_all_words_learned_dialog()

    def on_check_click(self, e):
        with self.lock:
            if self.checkButton.text == "Check":
                self.checkButton.disabled = True
                self.update()
                all_correct = self.compare_all_words()
                if all_correct:
                    self.words.good_answer_at_current_row()
                else:
                    self.words.bad_answer_at_current_row()
                self.checkButton.text = "Next"
                self.pb.increase()
                self.checkButton.disabled = False
                self.update()
            elif self.checkButton.text == "Next":
                self.checkButton.disabled = True
                self.update()
                self.checkButton.text = "Check"
                self.set_next_word()
                self.checkButton.disabled = False
                self.update()

    def compare_all_words(self):
        raise NotImplementedError("This method should be overridden in subclasses")

    def set_next_word(self):
        raise NotImplementedError("This method should be overridden in subclasses")
    
    def change_height(self, height):
        self.menu_control.change_height(height)