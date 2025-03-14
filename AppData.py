import pandas as pd
import random as rd
import os
from constants import FilesColumns, StatsColumns, PartsOfSpeech, WordDefinitions
from FilePathManager import FilePathManager

def get_kind_of_file_and_validate(file_name: str) -> str:
    # Returns the kind of file and validates it.
    if file_name.endswith("_words.csv"):
        return "words"
    elif file_name.endswith("_definitions.csv"):
        return "definitions"
    else:
        raise Exception("The file_name must end with _words.csv or _definitions.csv.")

def save_set(data, file_name):
    # Use FilePathManager to get the correct file path
    full_path = FilePathManager.get_csv_path(file_name)
    data.to_csv(full_path, index=True)

def load_set(file_name):
    # Use FilePathManager to get the correct file path
    full_path = FilePathManager.get_csv_path(file_name)
    return pd.read_csv(full_path, index_col=0)

def sanitize_file_name(file_name: str, kind: str) -> str:
    # deletes special characters that are not allowed in the file name
    # and limits the length to 20 characters (excluding the suffix)
    file_name = "".join([c for c in file_name if c.isalnum()]).rstrip()
    file_name = f"{file_name}_{kind}.csv"
    return file_name

def get_file_names_and_titles() -> dict:
    # Use FilePathManager for the path to files.csv
    files_data_path = FilePathManager.get_files_data_path()
    
    if not os.path.exists(files_data_path):
        generate_empty_files_data()
    
    df_files = pd.read_csv(files_data_path)
    # change nan to empty string
    df_files[FilesColumns.SUBTITLE.value] = df_files[FilesColumns.SUBTITLE.value].apply(lambda x: "" if pd.isna(x) else x)
    
    # Convert to list of dictionaries with full paths
    result = []
    for _, row in df_files.iterrows():
        entry = {
            FilesColumns.FILE_NAME.value: FilePathManager.get_csv_path(row[FilesColumns.FILE_NAME.value]),
            FilesColumns.TITLE.value: row[FilesColumns.TITLE.value],
            FilesColumns.SUBTITLE.value: row[FilesColumns.SUBTITLE.value]
        }
        result.append(entry)
    return result

def get_file_names() -> list:
    # Use FilePathManager for the path to files.csv
    files_data_path = FilePathManager.get_files_data_path()
    
    if not os.path.exists(files_data_path):
        generate_empty_files_data()
    
    df_files = pd.read_csv(files_data_path)
    return df_files[FilesColumns.FILE_NAME.value].tolist()

def generate_empty_files_data():
    # Use FilePathManager for the path to files.csv
    files_data_path = FilePathManager.get_files_data_path()
    
    df = pd.DataFrame(columns=[
        FilesColumns.FILE_NAME.value,
        FilesColumns.TITLE.value,
        FilesColumns.SUBTITLE.value])
    df.to_csv(files_data_path, index=False)

def set_default_progress(file_name: str):
    # delate information about learned items and sets default values 
    data = load_set(file_name)
    default_values = {
        StatsColumns.CORRECT_ANSWERS.value: 0,
        StatsColumns.GOOD_ANSWER.value: False,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: False,
        StatsColumns.WORD_TO_LEARN.value: False
    }
    for col in default_values.keys():
        data[col] = default_values[col]
        
    save_set(data, file_name)

def delate_set(file_name: str, file_not_exist=False):
    # Use FilePathManager for the path to files.csv
    files_data_path = FilePathManager.get_files_data_path()
    
    if not os.path.exists(files_data_path):
        generate_empty_files_data()
    
    df_files = pd.read_csv(files_data_path)
    df_files = df_files[df_files[FilesColumns.FILE_NAME.value] != os.path.basename(file_name)]
    df_files.to_csv(files_data_path, index=False)
    
    full_path = FilePathManager.get_csv_path(file_name)
    if not file_not_exist and os.path.exists(full_path):
        os.remove(full_path)

def add_new_file(file_name: str, title: str, subtitle: str = ""):
    # Use FilePathManager for the path to files.csv
    files_data_path = FilePathManager.get_files_data_path()
    
    if not os.path.exists(files_data_path):
        generate_empty_files_data()
    
    df_files = pd.read_csv(files_data_path)
    new_row = {
        FilesColumns.FILE_NAME.value: os.path.basename(file_name),
        FilesColumns.TITLE.value: title,
        FilesColumns.SUBTITLE.value: subtitle
    }
    df_files = pd.concat([df_files, pd.DataFrame([new_row])], ignore_index=True)
    df_files.to_csv(files_data_path, index=False)

def create_empty_set(kind: str):
    assert kind in ["words", "definitions"], "The kind must be 'words' or 'definitions'."
    column_types_words = {
        PartsOfSpeech.VERB.value: str,
        PartsOfSpeech.PERSON.value: str,
        PartsOfSpeech.THING.value: str,
        PartsOfSpeech.ADJECTIVE.value: str,
        PartsOfSpeech.ADVERB.value: str,
        StatsColumns.CORRECT_ANSWERS.value: int,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: bool,
        StatsColumns.GOOD_ANSWER.value: bool,
        StatsColumns.WORD_TO_LEARN.value: bool
    }
    
    column_types_definitions = {
        WordDefinitions.DEFINITION.value: str,
        WordDefinitions.WORD.value: str,
        StatsColumns.CORRECT_ANSWERS.value: int,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: bool,
        StatsColumns.GOOD_ANSWER.value: bool,
        StatsColumns.WORD_TO_LEARN.value: bool
    }
    
    if kind == "words":
        # create a file with columns: verb, person, thing, adjective, adverb, correct_answers, good_answers_in_a_row, good_answer, word_to_learn
        df = pd.DataFrame({
            PartsOfSpeech.VERB.value: [],
            PartsOfSpeech.PERSON.value: [],
            PartsOfSpeech.THING.value: [],
            PartsOfSpeech.ADJECTIVE.value: [],
            PartsOfSpeech.ADVERB.value: [],
            StatsColumns.CORRECT_ANSWERS.value: [],
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [],
            StatsColumns.GOOD_ANSWER.value: [],
            StatsColumns.WORD_TO_LEARN.value: []
        }).astype(column_types_words)
        return df
    
    elif kind == "definitions":
        # create a file with columns: definition, word, correct_answers, good_answers_in_a_row, good_answer, word_to_learn
        df = pd.DataFrame({
            WordDefinitions.DEFINITION.value: [],
            WordDefinitions.WORD.value: [],
            StatsColumns.CORRECT_ANSWERS.value: [],
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [],
            StatsColumns.GOOD_ANSWER.value: [],
            StatsColumns.WORD_TO_LEARN.value: []
        }).astype(column_types_definitions)
        return df
    
class AppData:
    # class attributes
    last_group_of_indexes = []
    
    def __init__(self, file_name: str):
        self.words = load_set(file_name)
        self.file_name = file_name
        self.current_group_of_indexes = []
        self.place_of_group_index = 0
        self.len_of_group = 0
        self.draw_index_group()
        self.current_word_index = 0
        self.current_word_row = self.words.loc[self.current_word_index]
        
        self.kind = get_kind_of_file_and_validate(file_name)
        
        self.stats_columns = [
            StatsColumns.CORRECT_ANSWERS.value, 
            StatsColumns.GOOD_ANSWER.value, 
            StatsColumns.GOOD_ANSWERS_IN_A_ROW.value,
            StatsColumns.WORD_TO_LEARN.value
        ]
        
        # assert kind in ["words", "definitions"]
        if self.kind not in ["words", "definitions"]:
            raise Exception("The kind must be 'words' or 'definitions'.")
        
        # assert the the correct columns are in the data
        if self.kind == "words":
            assert  PartsOfSpeech.VERB.value in self.words.columns and \
                    PartsOfSpeech.PERSON.value in self.words.columns and \
                    PartsOfSpeech.THING.value in self.words.columns and \
                    PartsOfSpeech.ADJECTIVE.value in self.words.columns and \
                    PartsOfSpeech.ADVERB.value in self.words.columns \
                    , "The columns must be: verb, person, thing, adjective, adverb."
                    
        elif self.kind == "definitions":
            assert  WordDefinitions.DEFINITION.value in self.words.columns and \
                    WordDefinitions.WORD.value in self.words.columns \
                    , "The columns must be: definition, word."
                    
        for col in self.stats_columns:
            assert col in self.words.columns, f"The column {col} is missing."
    
    def draw_index_group(self, save_indexes_in_class_art = False) -> int:
        # Draws grup of indexes with the fewest correct answers and returns quantity of indexes.
        
        # Get the indexes where good_answer, good_answers_in_a_row are False 
        # and word_to_learn is True.
        # I will indicate like this way: 0/0/1
        indexes_to_draw = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                                     (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                                     (self.words[StatsColumns.WORD_TO_LEARN.value] == True)].index
                
        # check if there are at least 10 indexes to draw and correct quantity if it is possible.
        for i in range(2):
            if len(indexes_to_draw) >= 10:
                break
            elif i == 0: # Add to indexes_to_draw indexes where:  0/0/0
                # quantity of indexes to add.
                qty_to_add = 10 - len(indexes_to_draw)
                # Sorting words by correct_answers.
                self.words.sort_values(by=StatsColumns.CORRECT_ANSWERS.value, inplace=True)
                # Adding indexes to indexes_to_draw.
                indexes_to_draw = \
                    indexes_to_draw.union(self.words[\
                        (self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                        (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                        (self.words[StatsColumns.WORD_TO_LEARN.value] == False)].index[:qty_to_add])
                    
            elif i == 1: # Add to indexes_to_draw indexes where:  1/0/0 or 1/0/1 or 1/1/1
                # quantity of indexes to add.
                qty_to_add = 10 - len(indexes_to_draw)
                # Sorting words by correct_answers.
                self.words.sort_values(by=StatsColumns.CORRECT_ANSWERS.value, inplace=True)
                # Adding indexes to indexes_to_draw.
                indexes_to_draw = \
                    indexes_to_draw.union(self.words[\
                        ((self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                         (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False)) |
                        ((self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                         (self.words[StatsColumns.WORD_TO_LEARN.value] == True))].index[:qty_to_add])
                    
        number_of_indexes = len(indexes_to_draw)
        if number_of_indexes > 10:
            number_of_indexes = 10
        elif number_of_indexes == 0:
            return 0
        
        # Drawing indexes from indexes_to_draw.
        indexes = rd.sample(indexes_to_draw.tolist(), number_of_indexes)
        self.current_group_of_indexes = indexes
        self.place_of_group_index = 0
        self.len_of_group = number_of_indexes
        
        if save_indexes_in_class_art:
            self.__class__.last_group_of_indexes = indexes
            
        return number_of_indexes
    
    def __get_next_index(self):
        # Returns a next index from the current group of indexes.
        ret = self.current_group_of_indexes[self.place_of_group_index]
        self.place_of_group_index += 1
        
        # If the current group of indexes is finished, reset the group.
        if self.place_of_group_index == self.len_of_group:
            self.current_group_of_indexes = []
            self.place_of_group_index = 0
            self.len_of_group = 0
        
        return ret
    
    def draw_new_row(self):
        # Draw a new row from the data.
        self.current_word_index = self.__get_next_index()
        self.current_word_row = self.words.loc[self.current_word_index]
    
    def get_current_row(self):
        # Returns the current row with colnames and without stats columns.
        return self.current_word_row.dropna().drop(self.stats_columns)
        
    def get_current_words_list(self):
        # Returns the current row as a list.
        return self.get_current_row().tolist()
    
    def colnames_in_WordFields(self):
        # Returns the column names of the current word row without the stats columns.
        return [col for col in self.current_word_row.index if col not in self.stats_columns]
    
    def good_answer_at_current_row(self):
        # Increases the correct answers of the current row.
        self.words.at[self.current_word_index, StatsColumns.CORRECT_ANSWERS.value] += 1
        
        # Changes in states of the current row.
        special_case =  self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] and \
                        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] and \
                        self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value]
                        
        spacial_case2 = self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] and \
                        (not self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value]) and \
                        self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value]
        
        previous_good_answer = self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value]
        if previous_good_answer:
            self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = True
        
        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] = True
        
        if special_case:
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = False
        elif spacial_case2:
            self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = True
            self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = False
        
        save_set(self.words, self.file_name)
        
    def bad_answer_at_current_row(self):
        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWER.value] = False
        self.words.at[self.current_word_index, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] = False
        self.words.at[self.current_word_index, StatsColumns.WORD_TO_LEARN.value] = True
        save_set(self.words, self.file_name)
        
    def it_is_not_last_index_of_group(self):
        return self.place_of_group_index != self.len_of_group

    def number_of_known_words(self):
        temp_words = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == True) &
                            (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == True) &
                            (self.words[StatsColumns.WORD_TO_LEARN.value] == False)]
        
        if temp_words.empty:
            return 0
        else:
            return len(temp_words)
        
    def number_of_learning_words(self):
        temp_words = self.words[(self.words[StatsColumns.GOOD_ANSWER.value] == False) &
                            (self.words[StatsColumns.GOOD_ANSWERS_IN_A_ROW.value] == False) &
                            (self.words[StatsColumns.WORD_TO_LEARN.value] == False)]
        
        subtract = 0
        
        if not temp_words.empty:
            subtract = len(temp_words)
            
        # number of words learning is computed thanks to subtract other cases. 
        return len(self.words) - self.number_of_known_words() - subtract 

    def number_of_all_words(self):
        return len(self.words)

    def are_all_words_learned(self):
        if self.number_of_known_words() == self.number_of_all_words():
            return True
        else:
            return False

    # method created for WordListMenu
    def refresh(self):
        self.words = load_set(self.file_name)

    @classmethod
    def was_this_index_drawn(cls, index: int):
        # checks if the index was drawn in the last group of indexes.
        return index in cls.last_group_of_indexes

    @classmethod
    def delete_last_group_of_indexes(cls):
        cls.last_group_of_indexes = [] # use later

    # methods if kind == "words"
    def colnames_with_nan(self):
        if self.kind != "words":
            raise Exception("This method is only for the 'words' kind.")
        
        return self.current_word_row[self.current_word_row.isnull()].index.tolist()

    # statics methods to creating the data.csv files
    @staticmethod
    def create_data_file_words(file_name: str, title: str, subtitle: str = ""):
        # if file files.csv does not exist, create it.
        files_data_path = FilePathManager.get_files_data_path()
        if not os.path.exists(files_data_path):
            generate_empty_files_data()
            
        kind = get_kind_of_file_and_validate(file_name)
        
        df = create_empty_set(kind)
        save_set(df, file_name)
        
        add_new_file(file_name, title, subtitle)

