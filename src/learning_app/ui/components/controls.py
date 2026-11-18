import flet as ft

from learning_app.data.answer_diff import CLOSE_MATCH_RATIO, diff_answer
from learning_app.ui.app_theme import AppTheme

_FEEDBACK_PREFIX = "Your answer: "


class WordField(ft.TextField):
    """Styled text field for learn and edit forms.

    Supports read-only display, good/bad answer borders, and slash-separated
    alternate answers via ``contain_word``. ``feedback`` is a separate
    ``ft.Text`` the screen places under the field. After a wrong, non-blank
    answer it shows the typed text with wrong letters struck through and
    missing letters inserted. The owning screen updates it with its own
    ``update``.

    Args:
        label: Field label.
        width: Width in logical pixels.
        read_only: Initial read-only state.
        autofocus: Whether the field requests focus on mount.
    """

    def __init__(self, label: str, width: int = 250, read_only: bool = True, autofocus=False):
        super().__init__()
        self.label = label
        self.width = width
        self.read_only = read_only
        self.width_border_indicator = 1 if AppTheme.is_dark_mode() else 3
        self.default_border = self.border
        self.feedback = ft.Text(
            size=14,
            text_align=ft.TextAlign.CENTER,
            width=width,
            visible=False,
        )

        if autofocus:
            self.autofocus = True

    def set_value(self, value: str):
        self.value = value
        self.update()

    def get_value(self):
        return self.value

    def _indicator_border(self, color) -> ft.OutlineInputBorder:
        return ft.OutlineInputBorder(
            side=ft.BorderSide(color=color, width=self.width_border_indicator),
        )

    def _indicator_border_states(self, color) -> dict:
        """Keep DEFAULT and FOCUSED the same so theme focus color does not hide the result."""
        border = self._indicator_border(color)
        return {
            ft.ControlState.DEFAULT: border,
            ft.ControlState.FOCUSED: border,
        }

    def set_green_border(self):
        self.border = self._indicator_border_states(ft.Colors.GREEN)
        self.update()

    def set_red_border(self):
        self.border = self._indicator_border_states(ft.Colors.RED)
        self.update()

    def reset(self):
        self.border = self.default_border
        self.value = ""
        self.disabled = False
        self.read_only = False
        self.hide_feedback()
        self.update()

    def disable(self):
        self.disabled = True
        self.hide_feedback()
        self.update()

    def make_read_only(self):
        self.read_only = True
        self.update()

    def contain_word(self, word: str):
        # Checks if the word field contains the word.
        if not isinstance(word, str):
            word = "" if word is None else str(word)
        # Spaces around "/" separate alternatives; they are not part of either answer.
        if "/" in word:
            stored = [part.strip().lower() for part in word.split("/")]
        else:
            stored = [word.lower()]

        typed = self.get_value()
        if "/" not in typed:
            return typed.strip().lower() in stored

        # Every typed form must be a stored alternative. An empty piece fails.
        pieces = [part.strip().lower() for part in typed.split("/")]
        if any(piece == "" for piece in pieces):
            return False
        return all(piece in stored for piece in pieces)

    def indicate_good_answer(self, word: str):
        self.hide_feedback()
        self.set_green_border()
        self.make_read_only()
        self.set_value(word)

    def indicate_bad_answer(self, word: str):
        typed = self.get_value() or ""
        self._show_feedback(typed, "" if word is None else str(word))
        self.set_red_border()
        self.make_read_only()
        self.set_value(word)

    def hide_feedback(self):
        self.feedback.visible = False
        self.feedback.value = ""
        self.feedback.spans = []

    def _show_feedback(self, typed: str, expected: str):
        typed = typed.strip()
        if not typed:
            self.hide_feedback()
            return
        pieces, ratio = diff_answer(typed, expected)
        self.feedback.visible = True
        if ratio < CLOSE_MATCH_RATIO:
            self.feedback.value = _FEEDBACK_PREFIX + typed
            self.feedback.spans = []
            return
        dark = AppTheme.is_dark_mode()
        wrong_style = ft.TextStyle(
            color=ft.Colors.RED_300 if dark else ft.Colors.RED_700,
            decoration=ft.TextDecoration.LINE_THROUGH,
            decoration_color=ft.Colors.RED_300 if dark else ft.Colors.RED_700,
        )
        missing_style = ft.TextStyle(
            color=ft.Colors.GREEN_300 if dark else ft.Colors.GREEN_700,
            weight=ft.FontWeight.BOLD,
            decoration=ft.TextDecoration.UNDERLINE,
        )
        styles = {"wrong": wrong_style, "missing": missing_style}
        spans = [ft.TextSpan(text=_FEEDBACK_PREFIX, style=ft.TextStyle(color=ft.Colors.ON_SURFACE_VARIANT))]
        spans.extend(ft.TextSpan(text=piece.text, style=styles.get(piece.kind)) for piece in pieces)
        self.feedback.value = ""
        self.feedback.spans = spans

    def is_indicated_correct(self) -> bool:
        """Return whether this field is locked after a correct Check."""
        if not self.read_only:
            return False
        border = self.border
        if isinstance(border, dict):
            border = border.get(ft.ControlState.DEFAULT)
        side = getattr(border, "side", None)
        return side is not None and side.color == ft.Colors.GREEN

    def is_awaiting_input(self) -> bool:
        """Return whether this field is editable and still empty."""
        if self.disabled or self.read_only:
            return False
        value = self.value
        return value is None or str(value).strip() == ""


class ProgressBar(ft.Column):
    """Simple answered/total progress indicator for learn sessions.

    Args:
        qty: Maximum count (denominator).
        start: Initial answered count.
        width: Bar width in logical pixels.
        word: Label prefix shown beside the counts.
        div_qty: Step size when incrementing progress.
    """

    def __init__(self, qty: int = 10, start: int = 0, width: int = 250, word: str = "Answered", div_qty: int = 1):
        super().__init__()
        assert start <= qty, "The start quantity must be less than or equal to the maximum quantity."
        assert start >= 0, "The start quantity must be greater than or equal to zero."
        assert qty > 0, "The maximum quantity must be greater than zero."
        assert (div_qty >= 1) and (div_qty <= qty), "The division quantity must be greater than or equal to one and less than or equal to the maximum quantity."

        self.current_qty = start
        self.max_qty = qty
        self.word = word
        self.div_qty = div_qty
        self.word = word
        if div_qty == 1:
            self.text = ft.Text(f"{word}: {self.current_qty}/{self.max_qty}")
        else:  # float display
            self.text = ft.Text(f"{word}: {self.current_qty / div_qty:.2f}/{self.max_qty / div_qty:.0f}")

        self.pb = ft.ProgressBar(
            value=self.current_qty / self.max_qty,
            width=width,
            color=ft.Colors.ORANGE_ACCENT,
            bgcolor=ft.Colors.BLACK,
        )
        self.controls = [self.text, self.pb]

    def __change_text(self):
        if self.div_qty == 1:
            self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        else:  # float display
            numerator = self.current_qty / self.div_qty
            denominator = self.max_qty / self.div_qty
            formatted_numerator = f"{numerator:.2f}".rstrip("0").rstrip(".")  # remove trailing zeros and dot
            formatted_denominator = f"{denominator:.0f}"
            self.text.value = f"{self.word}: {formatted_numerator}/{formatted_denominator}"

    def increase(self):
        self.current_qty += 1
        if self.current_qty > self.max_qty:
            raise Exception("The current quantity is greater than the maximum quantity.")

        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()

    def increase_by(self, qty: int):
        self.current_qty += qty
        if self.current_qty > self.max_qty:
            raise Exception("The current quantity is greater than the maximum quantity.")

        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()

    def set_max_qty(self, qty: int):
        self.max_qty = qty
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()

    def reset(self):
        self.current_qty = 0
        # self.text.value = f"{self.word}: {self.current_qty}/{self.max_qty}"
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()

    def set_certain_qty(self, qty):
        assert qty <= self.max_qty, "The quantity must be less than or equal to the maximum quantity."
        self.current_qty = qty
        self.__change_text()
        self.pb.value = self.current_qty / self.max_qty
        self.update()
