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