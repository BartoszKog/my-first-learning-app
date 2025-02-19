import pandas as pd
from constants import PartsOfSpeech, WordDefinitions, StatsColumns, Warnings
from AppData import load_set
import os

class CSVProcessor:
    @staticmethod
    def validate_file(file_path: str) -> dict:
        # Function for validating the file of the given path
        errors = []
        warnings = []
        is_valid = True
        requires_specific_actions = False
        has_statistics = False
        name_suggestion = ""
        data_type = ""

        # Check if the file is a CSV
        if not file_path.endswith('.csv'):
            errors.append(Warnings.NOT_A_CSV.value)
            is_valid = False
        else:
            # Try to load the file with pandas
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                errors.append(Warnings.ERROR_LOADING_FILE.value)
                is_valid = False

        # Check if the first column is an index
        if is_valid and (df.columns[0] != "Unnamed: 0" or not pd.api.types.is_integer_dtype(df["Unnamed: 0"])):
            warnings.append(Warnings.FIRST_COLUMN_NOT_INDEX.value)
            requires_specific_actions = True
        else:
            df.set_index("Unnamed: 0", inplace=True)

        # Validate column names based on file name
        if is_valid:
            if file_path.endswith('_words.csv'):
                expected_columns = {col.value for col in PartsOfSpeech}
                data_type = "words"
                if not expected_columns.issubset(df.columns):
                    errors.append(Warnings.MISSING_COLUMNS_WORDS.value)
                    is_valid = False
                else:
                    unnecessary_columns = set(df.columns) - expected_columns - {col.value for col in StatsColumns}
                    if unnecessary_columns:
                        warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                        requires_specific_actions = True
                name_suggestion = file_path.split('_words.csv')[0].split('/')[-1]
            elif file_path.endswith('_definitions.csv'):
                expected_columns = {col.value for col in WordDefinitions}
                data_type = "definitions"
                if not expected_columns.issubset(df.columns):
                    errors.append(Warnings.MISSING_COLUMNS_DEFINITIONS.value)
                    is_valid = False
                else:
                    unnecessary_columns = set(df.columns) - expected_columns - {col.value for col in StatsColumns}
                    if unnecessary_columns:
                        warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                        requires_specific_actions = True
                name_suggestion = file_path.split('_definitions.csv')[0].split('/')[-1]
            else:
                # Check if columns match either words or definitions
                words_columns = {col.value for col in PartsOfSpeech}
                definitions_columns = {col.value for col in WordDefinitions}
                if words_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_WORDS.value)
                    requires_specific_actions = True
                    unnecessary_columns = set(df.columns) - words_columns - {col.value for col in StatsColumns}
                    if unnecessary_columns:
                        warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                    data_type = "words"
                elif definitions_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_DEFINITIONS.value)
                    requires_specific_actions = True
                    unnecessary_columns = set(df.columns) - definitions_columns - {col.value for col in StatsColumns}
                    if unnecessary_columns:
                        warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                    data_type = "definitions"
                else:
                    errors.append("File does not match any expected column patterns.")
                    is_valid = False

        # Check for statistics columns
        if is_valid:
            stats_columns = {col.value for col in StatsColumns}
            has_statistics = stats_columns.issubset(df.columns)

            # Validate types of statistics columns
            if has_statistics:
                if not pd.api.types.is_integer_dtype(df[StatsColumns.CORRECT_ANSWERS.value]):
                    warnings.append(Warnings.COLUMN_NOT_INTEGER.value)
                    has_statistics = False
                for col in [StatsColumns.GOOD_ANSWER.value, StatsColumns.GOOD_ANSWERS_IN_A_ROW.value, StatsColumns.WORD_TO_LEARN.value]:
                    if not pd.api.types.is_bool_dtype(df[col]):
                        warnings.append(Warnings.COLUMN_NOT_BOOLEAN.value)
                        has_statistics = False

        # Check for empty values in statistics columns
        if is_valid and has_statistics:
            if df[list(stats_columns)].isnull().values.any():
                warnings.append(Warnings.EMPTY_VALUES_STATISTICS.value)
                requires_specific_actions = True

        # Remove duplicate warnings
        warnings = list(set(warnings))

        return {
            "errors": errors,
            "warnings": warnings,
            "is_valid": is_valid,
            "requires_specific_actions": requires_specific_actions,
            "has_statistics": has_statistics,
            "name_suggestion": name_suggestion,
            "data_type": data_type
        }

# for testing
if __name__ == "__main__":
    # Existing files
    files_to_test = ["data_words.csv", "dataCopy_words.csv"]

    # Create test files
    test_files = {
        "test_words.csv": pd.DataFrame({
            "verb": ["run", "jump"],
            "person": ["teacher", "student"],
            "thing": ["book", "pen"],
            "adjective": ["quick", "slow"],
            "adverb": ["quickly", "slowly"],
            "correct_answers": [1, 2],
            "good_answers_in_a_row": [True, False],
            "good_answer": [True, False],
            "word_to_learn": [False, True]
        }),
        "test_definitions.csv": pd.DataFrame({
            "definition": ["a place where people live", "a large vehicle for transporting goods"],
            "word": ["house", "truck"],
            "correct_answers": [3, 4],
            "good_answers_in_a_row": [True, True],
            "good_answer": [True, True],
            "word_to_learn": [False, False]
        }),
        # Test file with missing required columns for words file
        "test_missing_columns_words.csv": pd.DataFrame({
            "verb": ["run", "jump"],
            "person": ["teacher", "student"]
        }),
        # Test file with unnecessary columns
        "test_unnecessary_columns.csv": pd.DataFrame({
            "verb": ["run", "jump"],
            "person": ["teacher", "student"],
            "thing": ["book", "pen"],
            "adjective": ["quick", "slow"],
            "adverb": ["quickly", "slowly"],
            "correct_answers": [1, 2],
            "good_answers_in_a_row": [True, False],
            "good_answer": [True, False],
            "word_to_learn": [False, True],
            "extra_column": ["extra1", "extra2"]
        }),
        # Test file with incorrect column types
        "test_incorrect_column_types.csv": pd.DataFrame({
            "verb": ["run", "jump"],
            "person": ["teacher", "student"],
            "thing": ["book", "pen"],
            "adjective": ["quick", "slow"],
            "adverb": ["quickly", "slowly"],
            "correct_answers": ["one", "two"],  # Should be integers
            "good_answers_in_a_row": ["yes", "no"],  # Should be booleans
            "good_answer": ["yes", "no"],  # Should be booleans
            "word_to_learn": ["yes", "no"]  # Should be booleans
        })
    }

    for file_name, df in test_files.items():
        df.to_csv(file_name, index=False)
        files_to_test.append(file_name)

    # Validate files
    for file in files_to_test:
        print(f"Validating {file}:")
        result = CSVProcessor.validate_file(file)
        print(result)
        print()

    # Clean up test files
    for file_name in test_files.keys():
        os.remove(file_name)
