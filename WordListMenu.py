import flet as ft
from AppData import AppData
from typing import Dict
from Controls import ProgressBar
from constants import PartsOfSpeech, WordDefinitions, StatsColumns
from PageProperties import PageProperties

BORDERS = {
            "To learn": ft.border.all(1.5, ft.Colors.BLUE_GREY_700),
            "Learned": ft.border.all(1.5, ft.Colors.ORANGE_500),
            "Known": ft.border.all(1.5, ft.Colors.GREEN_ACCENT_700),
        }

COLORS_CHECKS = {
            "All": ft.Colors.RED_ACCENT_700,
            "Previous session": ft.Colors.YELLOW_700,
            "To learn": ft.Colors.LIGHT_BLUE_200,
            "Learned": ft.Colors.ORANGE_500,
            "Known": ft.Colors.GREEN_ACCENT_700,
        }

class WordContainer(ft.Container):
    def __init__(self, words_row, width, was_in_previous_session=False):
        super().__init__()
        # checking if the row have correct columns
        stats_columns = [
            StatsColumns.CORRECT_ANSWERS.value, 
            StatsColumns.GOOD_ANSWER.value, 
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
            StatsColumns.WORD_TO_LEARN.value
        ]
        
        columns_words = [
            PartsOfSpeech.VERB.value,
            PartsOfSpeech.PERSON.value,
            PartsOfSpeech.THING.value,
            PartsOfSpeech.ADJECTIVE.value,
            PartsOfSpeech.ADVERB.value
        ]
        
        columns_definitions = [
            WordDefinitions.DEFINITION.value,
            WordDefinitions.WORD.value
        ]
        
        columns_words.extend(stats_columns)
        columns_definitions.extend(stats_columns)
        
        assert  all([col in words_row.index for col in columns_words]) or \
                all([col in words_row.index for col in columns_definitions]) \
                , "The row must have correct columns."
        
        self.padding = 10
        
        # indicating state (to learn, learned, known)
        self.border_radius = 5
        
        self.to_learn = words_row[StatsColumns.GOOD_ANSWER.value] == False \
                    and words_row[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False \
                    and words_row[StatsColumns.WORD_TO_LEARN.value] == False
                    
        self.known =    words_row[StatsColumns.GOOD_ANSWER.value] == True \
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
        
        # finding words that are to long
        
        char_threshold = 20/250 * width # proportion of the width
        
        for word in words_row.index:
            # it means that the word is not kind of stats and definitions
            if not ((word in stats_columns) or (word in columns_definitions)): 
                if len(words_row[word]) > char_threshold: 
                    list_words = words_row[word].split("/")
                    words_row[word] = list_words[0]
                    for word_l in list_words[1:]:
                        words_row[word] += "/\n" + word_l
            elif not (word in stats_columns): # it could be definition or something else but not stats
                if len(words_row[word]) > char_threshold:
                    list_words = words_row[word].split(" ")
                    new_word = list_words[0]
                    current_line = list_words[0]
                    for word_l in list_words[1:]:
                        real_last_line = current_line.split("\n")[-1]
                        if len(real_last_line + " " + word_l) > char_threshold:
                            if not "\n" in word_l:
                                new_word += "\n" + word_l
                            current_line = word_l
                        else:
                            new_word += " " + word_l
                            current_line += " " + word_l
                    words_row[word] = new_word
                    
            
        # creating dictionary with index names where the length of the index name is equal to the max length
        dict_index_names = { # it is used to make the columns the same width
            PartsOfSpeech.VERB.value: "Verb        ",
            PartsOfSpeech.PERSON.value: "Person    ",
            PartsOfSpeech.THING.value: "Thing      ",
            PartsOfSpeech.ADJECTIVE.value: "Adjective",
            PartsOfSpeech.ADVERB.value: "Adverb   ",
            WordDefinitions.DEFINITION.value: "Definition",
            WordDefinitions.WORD.value: "Word       ",
        }
        
        
        Column_with_words = ft.Column()
        
        for word in words_row.index:
            if not (word in stats_columns):
                Column_with_words.controls.append(
                    ft.Row(
                        [
                            ft.Text(dict_index_names[word], color=ft.Colors.BLUE_GREY_500),
                            ft.Text(words_row[word]),
                        ],
                    )
                )
            
        self.content = Column_with_words
        
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
        if PageProperties.dark_mode:
            self.__change_border_width(1.5)
        else:
            self.__change_border_width(3)
        

class WordListMenu(ft.Column):
    def __init__(self, file_name: str = "data_words.csv", width: int = 250, on_start=lambda: None, on_back=lambda: None):
        from TilesContainer import TilesContainer
        
        super().__init__()
        self.width = width
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        if file_name.split("_")[1] == "words.csv":
            self.kind = "words"
        elif file_name.split("_")[1] == "definitions.csv":
            self.kind = "definitions"
        else: 
            raise Exception("The file_name must match the kind.")
        
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
        
        filter_chips_row = ft.Container(
            width=width+30,
            height=50,
            content=ft.ListView(
                        controls=[self.dict_filter_chips[label] for label in labels_chips],
                        horizontal=True,
                        spacing=5,
                    ),
        )
        
        self.bp =   ProgressBar(
            qty=self.words.number_of_all_words() * 4,
            start=self.words.number_of_known_words() * 4 + self.words.number_of_learning_words() * 1, # multiply by weights
            word="Progress",
            div_qty=4,
            width=width
        )
        
        def on_button_click(e):
            if e.control.text == "Start":
                on_start()
                
            elif e.control.text == "Back":
                on_back()
                TilesContainer().back_to_main_menu(e)
                    
        self.start_button = ft.ElevatedButton(
            text="Start",
            icon=ft.Icons.PLAY_ARROW,
            on_click=on_button_click
        )

        
        self.back_button = ft.ElevatedButton(
            text="Back",
            icon=ft.Icons.ARROW_BACK,
            on_click=on_button_click
        )
        
        self.lv =   ft.ListView(
            expand=True, 
            spacing=10, 
        )
        
        self.container = ft.Container(
            content=self.lv,
            padding=10,
            width=width+30,
            height=PageProperties.height * 0.7,
        )
        
        self.controls = [
            self.bp,
            filter_chips_row,
            self.container,
            ft.Row(
                [self.back_button, self.start_button],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ]
        
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
            wc = WordContainer(row[1], 
                               width=self.width, 
                               was_in_previous_session=is_in_previous_session)
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
        self.__update_lv()
        self.__update_bp()
        self.update()
        
    def refresh_content(self):
        self.__update_lv()
        self.__update_bp()
        self.update()
        
    def change_height(self, height):
        self.container.height = height
        self.update()
    