# Layout

Responsive layout is split into three independent decisions:

1. `body_wrapper` chooses the outer body container, padding, width policy, and
   safe-area behavior.
2. `layout_kind` tells the router which layout strategy to dispatch after
   navigation or resize.
3. `apply_layout()` lets one screen resize itself or its nested controls from
   the current metrics.

They are not alternatives. A route always selects a wrapper and a layout
strategy, while only screens with custom resize work implement
`apply_layout()`.

## 1. Select the body wrapper

The router applies `RouteDef.body_wrapper` after the build factory returns raw
controls. Factories must not call `build_shell_body()`, `build_deep_body()`, or
other wrapper helpers themselves.

The wrapper is responsible for the space immediately around the screen body.
For example, `BOTTOM_INSET_SHELL` protects Settings and Info from system
intrusions when the bottom app bar is hidden.

See [Chrome and wrappers](../concepts/chrome-and-wrappers.md) for the available
wrappers and safe-area reasoning.

## 2. Select route-level dispatch

`RouteDef.layout_kind` selects a router strategy:

- `HOME` refreshes the Home tile body's flex layout.
- `IMPORT_EXPORT` updates the Import/Export routable body.
- `SEARCH` updates the shared tile body used by Search.
- `SHELL` updates a normal routable Shell control.
- `DEEP_FORM` synchronizes the form wrapper and updates a Deep control.

The specialized `HOME`, `IMPORT_EXPORT`, and `SEARCH` strategies match
existing application flows. New routes normally use `SHELL` or `DEEP_FORM`.
See [Adding a screen](adding-a-screen.md#choose-layoutkind) for production
examples.

## 3. Decide whether the screen needs `apply_layout()`

=== "No custom layout hook"

    A fixed or naturally expanding control can rely on its wrapper:

    ```python
    class MyScreen(ft.Container):
        def __init__(self):
            super().__init__(
                expand=True,
                content=ft.Text("The wrapper handles available space"),
            )
    ```

    Do not add an empty `apply_layout()` merely to satisfy a pattern.

=== "Custom responsive layout"

    Use `RoutableScreenMixin` when the screen must resize itself or child
    controls:

    ```python
    from learning_app.ui.layout_metrics import LayoutMetrics
    from learning_app.ui.routable_screen import RoutableScreenMixin


    class MyScreen(RoutableScreenMixin, ft.Container):
        def apply_layout(
            self,
            metrics: LayoutMetrics | None = None,
        ) -> None:
            metrics = self.resolve_layout_metrics(metrics)
            self.width = metrics.body_width
            self.update_if_mounted()
    ```

The mixin resolves explicit, page-derived, or cached metrics and avoids
updating a detached control. It applies initial layout after mounting. The
router invokes the hook again after resize and when restoring the active view.

Keep screen-specific width and height decisions in this hook rather than
adding control-specific conditions to the router.

## Layout metrics

`LayoutMetrics` from `ui/layout_metrics.py` is one immutable
snapshot calculated from the viewport, visible chrome, padding, breakpoints,
and platform.

| Field | Meaning | Current consumers |
| --- | --- | --- |
| `body_width` | General Shell body width. | `TilesContainer`, `InfoControl`, and the Shell wrapper |
| `form_width` | Narrow width for focused forms and learning flows. | `CreateSetMenu`, `EditSetMenu`, `WordListMenu`, `WordFields`, and `WordDefinitionField` |
| `settings_width` | Width allocated to Settings controls. | `SettingsControl` and its background-shade slider |
| `content_height` | Height remaining after visible chrome and padding are subtracted. | Calculated and available, but no screen currently reads it directly |

The last row is intentionally explicit: do not invent a dependency on
`content_height`. Use it when a future control genuinely needs the remaining
vertical space.

## Common mistakes

### Wrapping controls inside the factory

Incorrect:

```python
return [build_deep_body(page, MyScreen())]
```

Return raw controls and let `RouteDef.body_wrapper` configure the wrapper.
Otherwise the screen can receive duplicate padding, sizing, or safe areas.

### Updating a detached control

Calling `self.update()` before mounting or after removal can fail. A
`RoutableScreenMixin` implementation should normally call
`self.update_if_mounted()`.

### Recalculating shared widths in each screen

Do not repeat viewport ratios in the router or individual controls. Shared
dimensions belong in `ui/layout_tokens.py` and `LayoutMetrics`;
the screen only chooses the relevant metric and applies it to its own
children.

For generated contracts, see the
[Layout host API](../reference/layout_host.md),
[Layout metrics API](../reference/layout_metrics.md), and
[Routable screen API](../reference/routable_screen.md).
