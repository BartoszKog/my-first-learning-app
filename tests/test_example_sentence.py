"""Gap rules for a definition example sentence."""

import pytest

from learning_app.data.example_sentence import (
    accepted_forms,
    cloze_sentence,
    example_sentence_error,
    gap_answers,
    normalize_example_sentence,
    preview_parts,
)


def test_blank_sentence_is_no_example():
    assert example_sentence_error("") is None
    assert example_sentence_error("   ") is None
    assert normalize_example_sentence("  ") == ""
    assert gap_answers("  ") == []
    assert cloze_sentence("  ") == ""
    assert preview_parts("  ") == []


def test_one_gap_and_a_phrase_gap():
    sentence = "The cat {sat} on the mat."
    assert example_sentence_error(sentence) is None
    assert gap_answers(sentence) == ["sat"]
    assert cloze_sentence(sentence) == "The cat {} on the mat."

    idiom = "I {keep} him {in line}."
    assert gap_answers(idiom) == ["keep", "in line"]
    assert cloze_sentence(idiom) == "I {} him {}."


def test_normalize_trims_the_sentence_and_each_gap():
    assert normalize_example_sentence("  I { keep } him {in line}.  ") == "I {keep} him {in line}."


def test_slash_is_another_form_of_the_same_gap():
    sentence = "She {keep/keeps} him in line."
    assert gap_answers(sentence) == ["keep/keeps"]
    assert accepted_forms("keep/keeps") == ["keep", "keeps"]
    pieces = preview_parts(sentence)
    gaps = [piece.text for piece in pieces if piece.is_gap]
    assert gaps == ["keep/keeps"]


def test_preview_of_an_unclosed_gap_is_the_raw_sentence():
    raw = "I {keep him."
    pieces = preview_parts(raw)
    assert len(pieces) == 1
    assert pieces[0].is_gap is False
    assert pieces[0].text == raw


@pytest.mark.parametrize(
    ("sentence", "message"),
    [
        ("I {keep him.", "Braces must come in pairs."),
        ("I keep} him.", "Braces must come in pairs."),
        ("I {keep {him}} in line.", "Do not nest braces."),
        ("I {} him in line.", "Fill the text inside each {}."),
        ("I { / } him in line.", "Fill the text inside each {}."),
        ("{sat}", "Add words around the braces."),
        ("just a sentence", "Mark each answer with {}."),
        ("{a} {b} {c} {d} {e} extra", "Use at most 4 gaps."),
    ],
)
def test_rejects_broken_gaps(sentence, message):
    assert example_sentence_error(sentence) == message


def test_four_gaps_are_allowed():
    sentence = "{One} and {two} and {three} and {four} left."
    assert example_sentence_error(sentence) is None
    assert gap_answers(sentence) == ["One", "two", "three", "four"]
