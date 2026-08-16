"""CSV schema enums, row limits, and import validation messages.

Column enums define the expected headers for words sets, definitions sets,
per-row learning statistics, and the ``files.csv`` catalog. ``Errors`` and
``Warnings`` supply stable message text for ``CSVProcessor``.
"""

from enum import Enum


class PartsOfSpeech(Enum):
    """Content columns for a ``*_words.csv`` learning set."""

    VERB = "verb"
    PERSON = "person"
    THING = "thing"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"


class WordDefinitions(Enum):
    """Content columns for a ``*_definitions.csv`` learning set."""

    DEFINITION = "definition"
    WORD = "word"


class StatsColumns(Enum):
    """Per-row learning statistics stored on every set CSV."""

    CORRECT_ANSWERS = "correct_answers"
    GOOD_ANSWERS_IN_A_ROW = "good_answers_in_a_row"
    GOOD_ANSWER = "good_answer"
    WORD_TO_LEARN = "word_to_learn"


class FilesColumns(Enum):
    """Columns of the set catalog ``files.csv``."""

    FILE_NAME = "file_name"
    TITLE = "title"
    SUBTITLE = "subtitle"
    CREATED_AT = "created_at"
    LAST_USED = "last_used"
    USE_COUNT = "use_count"


class SetSortMode(Enum):
    """Ordering modes for Home and export set tile lists."""

    LAST_USED = "last_used"
    CREATED = "created"
    TITLE = "title"
    USE_COUNT = "use_count"


class Warnings(Enum):
    """Non-fatal import validation messages from ``CSVProcessor``."""

    UNNECESSARY_COLUMNS = "Unnecessary columns found."
    FIRST_COLUMN_NOT_INDEX = "The first column is not an index."
    COLUMN_NOT_BOOLEAN = "One or more statistics columns are not of type boolean."
    EMPTY_VALUES_STATISTICS = "The file contains empty values in statistics columns."
    COLUMN_NOT_INTEGER = "The 'correct_answers' column is not of type integer."
    INCONSISTENT_STATISTICS_COMBINATION = "Inconsistent combinations of statistics found."
    NEGATIVE_CORRECT_ANSWERS = "Negative values found in correct_answers column."
    INSUFFICIENT_NON_EMPTY_VALUES = "Some rows have insufficient non-empty values in typical columns."


MAX_ROWS = 40
"""Maximum number of content rows allowed in one learning set."""

TITLE_MAX_LENGTH = 20
"""Maximum display title length for create, import, and rename."""


class Errors(Enum):
    """Fatal import validation messages from ``CSVProcessor``."""

    NOT_A_CSV = "File is not a CSV."
    ERROR_LOADING_FILE = "Error loading file with pandas."
    FILE_NOT_FOUND = "File not found."
    MISSING_COLUMNS_WORDS = "Missing required columns for words file."
    MISSING_COLUMNS_DEFINITIONS = "Missing required columns for definitions file."
    TOO_MANY_ROWS = f"File contains more than {MAX_ROWS} rows."
    EMPTY_VALUES_IN_DEFINITIONS = "All rows have empty values in typical columns for definitions file."
    INSUFFICIENT_NON_EMPTY_VALUES_IN_WORDS = "All rows have insufficient non-empty values in typical columns for words file."
    NO_MATCHING_COLUMN_PATTERN = "File does not match any expected column patterns."
