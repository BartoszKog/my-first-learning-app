# Routing

Routing is split between a declarative registry and an imperative router.
The registry describes each route; the router executes that description.

## Registry responsibility

`ui/route_registry.py` is the source of truth for available
screens. `ROUTE_REGISTRY` keeps route-specific decisions out of buttons,
drawer code, and router conditionals.

A `RouteDef` connects a path to:

- a Shell or Deep route kind,
- a screen build factory,
- body wrapper and layout behavior,
- optional Shell chrome (`chrome=SHELL_CHROME[path]` on existing Shell
  entries; runtime visibility still comes from `SHELL_CHROME` by path),
- optional drawer metadata,
- optional fallback behavior.

For example, the Settings definition connects one path with its factory,
wrapper, resize strategy, chrome, and drawer entry:

```python
RouteDef(
    path=SETTINGS_ROUTE,
    kind=RouteKind.SHELL,
    body_wrapper=BodyWrapperKind.BOTTOM_INSET_SHELL,
    layout_kind=LayoutKind.SHELL,
    chrome=SHELL_CHROME[SETTINGS_ROUTE],
    build_factory=_build_settings_controls,
    shell_layout_control=SettingsControl,
    drawer_label="Settings",
    drawer_icon="SETTINGS",
)
```

Drawer items are derived from definitions that provide a label and icon. A
new drawer route therefore does not require a separate path-to-drawer mapping.

## Router responsibility

`ui/router.py`:

- responds to Flet route and view-pop events,
- resolves the matching `RouteDef`,
- calls the route's build factory,
- applies the selected wrapper and Shell chrome from `SHELL_CHROME[path]`,
- builds an `ft.View`,
- replaces or extends the view stack,
- dispatches responsive layout updates.

The router owns these invariants centrally. A screen should not decide how to
detach shared chrome, normalize unknown paths, or manipulate `page.views`.
Do not change a live view's `route` or replace the views underneath it — that
desyncs Android system Back from the Python stack, and Home can appear without
chrome.

## Factory result and fallback

A factory receives the current `ft.Page` and decoded route parameters. It
returns raw controls when the route can be built, or `None` when required
input is missing.

Conceptually, the router handles the result like this:

```python
controls = route_def.build_factory(page, params)

if controls is None:
    fallback = route_def.fallback_path or HOME_ROUTE
    return build_route_view(fallback)

wrapped_controls = apply_body_wrapper(controls, route_def.body_wrapper)
return build_view(wrapped_controls, route_def)
```

The helper names in this example describe the flow rather than form a public
API. The real implementation keeps wrapper and view construction private to
`ui/router.py`.

## Why screens use navigation helpers

Screens should import `navigate_to()`, `push_view()`, `go_back()`, and
`go_search()` from `ui/navigation.py`, not internal router
functions. The helper module provides a small stable boundary and lets the
router change its stack, normalization, or update details without changing
every screen.

For a practical registration checklist, see
[Adding a screen](../guides/adding-a-screen.md). For the route map and Shell
versus Deep roles, see
[Routing and screens](../architecture/routing-and-screens.md). For symbol-level
details, see the [Route registry API](../reference/route_registry.md),
[Router API](../reference/router.md), and
[Navigation API](../reference/navigation.md).
