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
    UNNECESSARY_COLUMNS = "Unnecessary columns found."
    FIRST_COLUMN_NOT_INDEX = "The first column is not an index."
    FILE_NAME_PATTERN_WORDS = "File name does not match the expected pattern for words file."
    FILE_NAME_PATTERN_DEFINITIONS = "File name does not match the expected pattern for definitions file."
    COLUMN_NOT_BOOLEAN = "One or more statistics columns are not of type boolean."
    EMPTY_VALUES_STATISTICS = "The file contains empty values in statistics columns."
    COLUMN_NOT_INTEGER = "The 'correct_answers' column is not of type integer."
    INCONSISTENT_STATISTICS_COMBINATION = "Inconsistent combinations of statistics found."
    NEGATIVE_CORRECT_ANSWERS = "Negative values found in correct_answers column."
    INSUFFICIENT_NON_EMPTY_VALUES = "Some rows have insufficient non-empty values in typical columns."

# constant value form maximum number of rows in set
MAX_ROWS = 40

class Errors(Enum):
    NOT_A_CSV = "File is not a CSV."
    ERROR_LOADING_FILE = "Error loading file with pandas."
    FILE_NOT_FOUND = "File not found."
    MISSING_COLUMNS_WORDS = "Missing required columns for words file."
    MISSING_COLUMNS_DEFINITIONS = "Missing required columns for definitions file."
    TOO_MANY_ROWS = f"File contains more than {MAX_ROWS} rows."
    EMPTY_VALUES_IN_DEFINITIONS = "All rows have empty values in typical columns for definitions file."
    INSUFFICIENT_NON_EMPTY_VALUES_IN_WORDS = "All rows have insufficient non-empty values in typical columns for words file."
    NO_MATCHING_COLUMN_PATTERN = "File does not match any expected column patterns."

