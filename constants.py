from enum import Enum

class PartsOfSpeech(Enum):
    VERB = "verb"
    PERSON = "person"
    THING = "thing"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    
class WordDefinitions(Enum):
    DEFINITION = "definition"
    WORD = "word"
    
class StatsColumns(Enum):
    CORRECT_ANSWERS = "correct_answers"
    GOOD_ANSWERS_IN_A_ROW = "good_answers_in_a_row"
    GOOD_ANSWER = "good_answer"
    WORD_TO_LEARN = "word_to_learn"
    
class FilesColumns(Enum):
    FILE_NAME = "file_name"
    TITLE = "title"
    SUBTITLE = "subtitle"

class Warnings(Enum):
    NOT_A_CSV = "File is not a CSV."
    ERROR_LOADING_FILE = "Error loading file with pandas."
    FIRST_COLUMN_NOT_INDEX = "The first column is not an index."
    MISSING_COLUMNS_WORDS = "Missing required columns for words file."
    MISSING_COLUMNS_DEFINITIONS = "Missing required columns for definitions file."
    UNNECESSARY_COLUMNS = "Unnecessary columns found."
    FILE_NAME_PATTERN_WORDS = "File name does not match the expected pattern for words file."
    FILE_NAME_PATTERN_DEFINITIONS = "File name does not match the expected pattern for definitions file."
    COLUMN_NOT_INTEGER = "The 'correct_answers' column is not of type integer."
    COLUMN_NOT_BOOLEAN = "One or more statistics columns are not of type boolean."
    EMPTY_VALUES_STATISTICS = "The file contains empty values in statistics columns."