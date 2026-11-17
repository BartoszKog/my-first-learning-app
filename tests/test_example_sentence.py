"""Gap rules for a definition example sentence."""

import pytest

from learning_app.data.example_sentence import (
    accepted_forms,
    cloze_sentence,
    display_form,
    example_sentence_error,
    filled_sentence,
    gap_answers,
    matches_gap_answers,
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


def test_display_form_is_the_first_accepted_form():
    assert display_form("keep/keeps") == "keep"
    assert display_form("in line") == "in line"


@pytest.mark.parametrize(
    "typed",
    ["keep in line", "Keep  In Line", "keep, in line", "keep in; line", " keep ,in line "],
)
def test_gap_answers_in_order_are_accepted(typed):
    assert matches_gap_answers(typed, "I {keep} him {in line}.")


@pytest.mark.parametrize(
    "typed",
    ["in line keep", "keep", "keep him in line", "keep in him line", "", "   "],
)
def test_other_answers_do_not_match_the_gaps(typed):
    assert not matches_gap_answers(typed, "I {keep} him {in line}.")


def test_each_gap_accepts_its_slash_forms():
    sentence = "She {keep/keeps} him {in line}."
    assert matches_gap_answers("keeps in line", sentence)
    assert matches_gap_answers("keep in line", sentence)
    assert not matches_gap_answers("keep/keeps in line", sentence)


def test_blank_or_broken_sentence_matches_nothing():
    assert not matches_gap_answers("keep", "")
    assert not matches_gap_answers("keep", "I {keep him.")


def test_filled_sentence_uses_the_first_slash_form():
    assert filled_sentence("I {keep/keeps} him {in line}.") == "I keep him in line."
    assert filled_sentence("") == ""
    assert filled_sentence("I {keep him.") == ""
