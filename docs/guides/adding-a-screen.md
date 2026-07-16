# Adding a screen

Use `ui/screens/_screen_template.py` as the implementation
starting point. Before copying it, decide what role the new screen has.

## Decide: Shell or Deep?

- Choose **Shell** when the screen is a main destination, can replace the
  current navigation stack, and may appear in the drawer.
- Choose **Deep** when the screen is a focused task opened from another view
  and closed with Back, Cancel, or Save.

See [Two navigation roles](../architecture.md#two-navigation-roles) for the
reason behind this distinction.

The remaining work is usually: define a path, implement the control, create a
factory, register a `RouteDef`, configure Shell chrome if needed, and navigate
through the public helpers.

## 1. Define the path

Add a constant to `ui/route_paths.py`:

```python
MY_SCREEN_ROUTE = "/my-screen"
```

A named constant keeps the path in one place and prevents slightly different
route strings from being repeated in controls, registry entries, and tests.
See the [route paths API](../reference/route_paths.md).

## 2. Create the screen control

Place the control in `ui/screens/`. Keeping UI construction in a
screen class separates screen behavior from route lookup and view-stack
management.

Choose the simplest variant that matches the screen:

=== "Simple screen"

    Use a regular Flet control when the wrapper can handle sizing and the
    screen has no nested controls that require custom resize logic.

    ```python
    class MyScreen(ft.Container):
        def __init__(self, page: ft.Page):
            super().__init__(expand=True)
            self.content = ft.Text("My screen")
    ```

=== "Screen with custom resize"

    Add `RoutableScreenMixin` and `apply_layout()` when the screen must resize
    itself or nested controls from the current `LayoutMetrics`.

    ```python
    from learning_app.ui.layout_metrics import LayoutMetrics
    from learning_app.ui.routable_screen import RoutableScreenMixin


    class MyScreen(RoutableScreenMixin, ft.Container):
        def __init__(self, page: ft.Page):
            super().__init__(expand=True)
            self._app_page = page
            self.content = ft.Text("My screen")

        def apply_layout(
            self,
            metrics: LayoutMetrics | None = None,
        ) -> None:
            metrics = self.resolve_layout_metrics(metrics)
            self.width = metrics.body_width
            self.update_if_mounted()
    ```

See the [Layout guide](layout.md) for the resize lifecycle and the
[routable screen API](../reference/routable_screen.md) for the mixin contract.

## 3. Add a build factory

Build factories in `ui/route_registry.py` receive the page and
decoded query parameters. The factory isolates how the route creates its
screen, so the router does not need screen-specific constructors.

```python
def _build_my_screen_controls(
    page: ft.Page,
    _params: dict[str, str],
) -> list[ft.Control]:
    from learning_app.ui.screens.my_screen import MyScreen

    return [MyScreen(page)]
```

Return raw controls. The router applies the configured body wrapper after the
factory returns. Local imports help avoid circular dependencies between
screens, navigation, and route registration.

A factory may return `None` when required route data is missing. In that case
the router builds the configured fallback route.

## 4. Register the route

Add a `RouteDef` to `ROUTE_REGISTRY` in
`ui/route_registry.py`. This is the single place that connects a
path with its construction, navigation role, wrapper, layout behavior, chrome,
and optional drawer metadata.

```python
RouteDef(
    path=MY_SCREEN_ROUTE,
    kind=RouteKind.SHELL,
    body_wrapper=BodyWrapperKind.BOTTOM_INSET_SHELL,
    layout_kind=LayoutKind.SHELL,
    chrome=SHELL_CHROME[MY_SCREEN_ROUTE],
    build_factory=_build_my_screen_controls,
    drawer_label="My screen",
    drawer_icon="STAR",
)
```

### Required fields

- `path` — the constant defined in `ui/route_paths.py`.
- `kind` — `RouteKind.SHELL` or `RouteKind.DEEP`.
- `body_wrapper` — the outer body container selected by the router.
- `layout_kind` — the resize-dispatch strategy.
- `chrome` — a `ShellChromeConfig` for Shell, normally `None` for Deep.
- `build_factory` — the function that returns raw controls or `None`.

### Optional fields

- `fallback_path` — opened when the factory returns `None`.
- `shell_layout_control` — control type the Shell dispatcher should find when
  applying custom layout.
- `body_content_alignment` — vertical alignment inside a Deep body column.
- `vertical_alignment` — alignment applied to the complete `ft.View`.
- `drawer_label` and `drawer_icon` — include a Shell route in the drawer.
- `drawer_divider_before` — place a divider before that drawer item.

The registration above matches the simple screen variant and intentionally
omits `shell_layout_control`. For the responsive variant, add:

```python
shell_layout_control=MyScreen
```

The mixin applies initial layout after mounting. The router uses this type to
find the control and pass fresh metrics after resizing and restoring the view.

See the [route registry API](../reference/route_registry.md) for complete field
types and defaults.

### Choose `LayoutKind`

| Value | Use when | Existing example |
| --- | --- | --- |
| `HOME` | The route owns the Home tile body and its flex-layout refresh. | Home |
| `IMPORT_EXPORT` | The route hosts the Import/Export control and tile body. | Import/Export |
| `SEARCH` | The route hosts `SearchScreen` and its shared tile body. | Search |
| `SHELL` | A normal Shell route may contain a routable screen control. | Settings, Info |
| `DEEP_FORM` | A Deep route contains a responsive form or learning flow. | Create, Edit, Learn |

The first three values are specialized for existing application flows. A new
ordinary Shell screen normally uses `SHELL`; a new Deep form normally uses
`DEEP_FORM`.

Choose `body_wrapper` separately. It controls the outer container, padding,
and safe area rather than resize dispatch. See
[Chrome and wrappers](../concepts/chrome-and-wrappers.md).

## 5. Configure Shell chrome

For a Shell route, add its `ShellChromeConfig` to `SHELL_CHROME` in
`ui/chrome_config.py`:

```python
MY_SCREEN_ROUTE: ShellChromeConfig(
    appbar_title="My screen",
    appbar_menu_leading=True,
    bottom_appbar_visible=False,
    fab_visible=False,
    search_button_visible=False,
),
```

This keeps shared AppBar, bottom bar, FAB, and search visibility out of the
screen's business logic. Deep routes set `chrome=None` and need no entry.
See the [chrome configuration API](../reference/chrome_config.md).

## 6. Navigate and verify

Use `navigate_to()` for Shell and `push_view()` for Deep. These helpers express
the intended stack behavior without exposing router internals. See the
[Navigation guide](navigation.md) and
[navigation API](../reference/navigation.md).

Before considering the route complete, verify:

- The screen opens through its intended action.
- Back, Cancel, or Save reveals the expected previous screen.
- Missing required route parameters use the expected fallback.
- The layout updates after resizing.
- AppBar, bottom bar, FAB, search, and safe-area behavior are correct.
- Drawer label, icon, selection, and divider are correct when configured.
