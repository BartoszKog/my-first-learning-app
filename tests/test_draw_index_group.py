"""Practice-group length follows the Settings queue-size limits."""

import pandas as pd
import pytest

from learning_app.data.app_data import AppData, save_set
from learning_app.data.constants import PartsOfSpeech, StatsColumns, WordDefinitions
from learning_app.ui.learn_preferences import LearnPreferences


@pytest.fixture
def restore_queue_sizes():
    words_queue = LearnPreferences.word_formations_queue_size
    definitions_queue = LearnPreferences.definitions_queue_size
    yield
    LearnPreferences.word_formations_queue_size = words_queue
    LearnPreferences.definitions_queue_size = definitions_queue


def _stats(count: int) -> dict:
    return {
        StatsColumns.CORRECT_ANSWERS.value: [0] * count,
        StatsColumns.GOOD_ANSWERS_IN_A_ROW.value: [False] * count,
        StatsColumns.GOOD_ANSWER.value: [False] * count,
        StatsColumns.WORD_TO_LEARN.value: [False] * count,
    }


def test_draw_index_group_respects_queue_limits(isolated_csv_dir, restore_queue_sizes):
    word_count = 12
    save_set(
        pd.DataFrame(
            {
                PartsOfSpeech.VERB.value: [f"verb{i}" for i in range(word_count)],
                PartsOfSpeech.PERSON.value: [f"person{i}" for i in range(word_count)],
                PartsOfSpeech.THING.value: [f"thing{i}" for i in range(word_count)],
                PartsOfSpeech.ADJECTIVE.value: [f"adj{i}" for i in range(word_count)],
                PartsOfSpeech.ADVERB.value: [f"adv{i}" for i in range(word_count)],
                **_stats(word_count),
            }
        ),
        "queue_words.csv",
    )
    definition_count = 16
    save_set(
        pd.DataFrame(
            {
                WordDefinitions.DEFINITION.value: [
                    f"def{i}" for i in range(definition_count)
                ],
                WordDefinitions.WORD.value: [
                    f"word{i}" for i in range(definition_count)
                ],
                **_stats(definition_count),
            }
        ),
        "queue_definitions.csv",
    )

    LearnPreferences.word_formations_queue_size = 4
    words = AppData("queue_words.csv")
    assert words.kind == "words"
    assert len(words.current_group_of_indexes) == 4
    assert words.len_of_group == 4

    drawn_group = list(words.current_group_of_indexes)
    LearnPreferences.word_formations_queue_size = 3
    assert words.current_group_of_indexes == drawn_group
    assert words.draw_index_group() == 3
    assert len(words.current_group_of_indexes) == 3

    LearnPreferences.definitions_queue_size = 15
    definitions = AppData("queue_definitions.csv")
    assert definitions.kind == "definitions"
    assert len(definitions.current_group_of_indexes) == 15
    assert definitions.len_of_group == 15
    assert definitions.draw_index_group() <= LearnPreferences.definitions_queue_size
