"""Central layout knobs used by ``layout_metrics`` and responsive screens.

Widths are typically ``viewport_width * ratio``, then capped via
``CONTENT_MAX_WIDTH``. On phones the ratio dominates; the max width mainly
limits desktop / wide windows.
"""

# Fallback chrome heights when AppBar / BottomAppBar do not expose height.
# Used only to subtract occupied vertical space from available content height.
DEFAULT_APPBAR_HEIGHT = 100
DEFAULT_BOTTOM_APPBAR_HEIGHT = 80

# Absolute cap (logical px) for body-scale content. With BODY_WIDTH_RATIO=0.87,
# body_width never exceeds this; form/settings are capped proportionally.
CONTENT_MAX_WIDTH = 720

# Fraction of viewport width for shell routes (Home tile list, Import/Export,
# Info shell body, etc.). Applied as metrics.body_width → TilesContainer.width.
BODY_WIDTH_RATIO = 0.87

# Fraction of viewport width for deep form routes: learn menu/session,
# create/edit set, word list. Applied as metrics.form_width (e.g. EditSetMenu
# main_container, learn screen outer form). On a phone this is the main lever
# for how wide those screens feel.
FORM_WIDTH_RATIO = 0.83

# Fraction of viewport width for the Settings screen content column.
SETTINGS_WIDTH_RATIO = 0.8

# Viewport width thresholds (logical px) stored on LayoutMetrics.breakpoint
# as "compact" / "normal" / "wide". Currently classification only — they do
# not change computed widths by themselves.
BREAKPOINT_COMPACT = 600
BREAKPOINT_WIDE = 900

# Top/bottom padding inside deep-form body hosts (learn, edit, create, …).
DEEP_FORM_VERTICAL_INSET = 52

# Fallback viewport size before the page reports real dimensions (startup).
DEFAULT_VIEWPORT_WIDTH = 500
DEFAULT_VIEWPORT_HEIGHT = 900

# Learn TextField / ProgressBar width as a fraction of form_width.
# Non-Windows (e.g. Android phone) uses the base ratios; Windows uses *_WINDOWS.
# Labels (ft.Text) are not sized by these — only input fields and the bar.
LEARN_WORDS_FIELD_WIDTH_RATIO = 0.90
LEARN_WORDS_FIELD_WIDTH_RATIO_WINDOWS = 0.83
LEARN_DEFINITION_FIELD_WIDTH_RATIO = 0.90
LEARN_DEFINITION_FIELD_WIDTH_RATIO_WINDOWS = 0.80

# Scale of the Check button on the definition learn screen.
LEARN_DEFINITION_CHECK_BUTTON_SCALE = 1.3
