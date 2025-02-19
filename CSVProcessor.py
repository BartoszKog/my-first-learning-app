import pandas as pd
from constants import PartsOfSpeech, WordDefinitions, StatsColumns, Warnings, Errors, MAX_ROWS
from AppData import load_set
from PageProperties import PageProperties
from flet import PagePlatform

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

        data_conventions = [
            ("words", "_words.csv", PartsOfSpeech, Errors.MISSING_COLUMNS_WORDS, Warnings.FILE_NAME_PATTERN_WORDS),
            ("definitions", "_definitions.csv", WordDefinitions, Errors.MISSING_COLUMNS_DEFINITIONS, Warnings.FILE_NAME_PATTERN_DEFINITIONS)
        ]

        # Assertions to ensure the integrity of data_conventions entries
        for convention in data_conventions:
            assert len(convention) == 5, "Each data convention must have exactly 5 elements."
            assert isinstance(convention[0], str), "The first element of each data convention must be a string (data type)."
            assert isinstance(convention[1], str), "The second element of each data convention must be a string (file suffix)."
            assert hasattr(convention[2], '__members__'), "The third element of each data convention must be an Enum (columns enum)."
            assert isinstance(convention[3], Errors), "The fourth element of each data convention must be an Errors enum member."
            assert isinstance(convention[4], Warnings), "The fifth element of each data convention must be a Warnings enum member."

        def validate_columns(expected_columns, df_columns, error_message):
            if not expected_columns.issubset(df_columns):
                errors.append(error_message.value)
                return False
            unnecessary_columns = set(df_columns) - expected_columns - {col.value for col in StatsColumns}
            if unnecessary_columns:
                warnings.append(Warnings.UNNECESSARY_COLUMNS.value)
                requires_specific_actions = True
            return True

        def check_missing_data(typical_columns, df):
            if data_type == "words":
                insufficient_non_empty_rows = df[typical_columns].isnull().sum(axis=1) >= (len(typical_columns) - 1)
                if insufficient_non_empty_rows.all():
                    errors.append(Errors.INSUFFICIENT_NON_EMPTY_VALUES_IN_WORDS.value)
                    return False
                elif insufficient_non_empty_rows.any():
                    warnings.append(Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value)
                    requires_specific_actions = True
            elif data_type == "definitions":
                rows_with_empty_values = df[typical_columns].isnull().any(axis=1)
                if rows_with_empty_values.all():
                    errors.append(Errors.EMPTY_VALUES_IN_DEFINITIONS.value)
                    return False
                elif rows_with_empty_values.any():
                    warnings.append(Warnings.INSUFFICIENT_NON_EMPTY_VALUES.value)
                    requires_specific_actions = True
            return True

        # Check if the file is a CSV
        if not file_path.endswith('.csv'):
            errors.append(Errors.NOT_A_CSV.value)
            is_valid = False
        else:
            # Try to load the file with pandas
            try:
                df = pd.read_csv(file_path)
            except Exception as e:
                errors.append(Errors.ERROR_LOADING_FILE.value)
                is_valid = False

        # Check if the first column is an index
        if is_valid and (df.columns[0] != "Unnamed: 0" or not pd.api.types.is_integer_dtype(df["Unnamed: 0"])):
            warnings.append(Warnings.FIRST_COLUMN_NOT_INDEX.value)
            requires_specific_actions = True
        else:
            if is_valid:
                df.set_index("Unnamed: 0", inplace=True)

        # Check if the number of rows exceeds the maximum allowed
        if is_valid and len(df) > MAX_ROWS:
            errors.append(Errors.TOO_MANY_ROWS.value)
            is_valid = False

        # Validate column names based on file name
        if is_valid:
            for convention, suffix, columns_enum, missing_columns_error, pattern_warning in data_conventions:
                if file_path.endswith(suffix):
                    expected_columns = {col.value for col in columns_enum}
                    data_type = convention
                    if not validate_columns(expected_columns, df.columns, missing_columns_error):
                        is_valid = False
                        
                    file_separator = '\\' if PageProperties.platform == PagePlatform.WINDOWS else '/'
                        
                    name_suggestion = file_path.split(suffix)[0].split(file_separator)[-1] # android can be different
                    break
            else:
                # Check if columns match either words or definitions
                words_columns = {col.value for col in PartsOfSpeech}
                definitions_columns = {col.value for col in WordDefinitions}
                if words_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_WORDS.value)
                    requires_specific_actions = True
                    validate_columns(words_columns, df.columns, Errors.MISSING_COLUMNS_WORDS)
                    data_type = "words"
                elif definitions_columns.issubset(df.columns):
                    warnings.append(Warnings.FILE_NAME_PATTERN_DEFINITIONS.value)
                    requires_specific_actions = True
                    validate_columns(definitions_columns, df.columns, Errors.MISSING_COLUMNS_DEFINITIONS)
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

        # Check for empty values in typical columns based on data type
        if is_valid:
            typical_columns = [col.value for col in PartsOfSpeech] if data_type == "words" else [col.value for col in WordDefinitions]
            if not check_missing_data(typical_columns, df):
                is_valid = False

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

