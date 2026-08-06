# In-place search API

Source: `ui/inplace_search.py`

Inserts and removes `SearchControl` above a Home or export `TilesContainer`
without reparenting tiles or changing the route. Prefer calling
`go_search()` / `go_back()` from [Navigation](navigation.md); use this module
when wiring the router or debugging search chrome. Concept overview:
[Body registry](../concepts/body-registry.md) and
[Open search](../guides/navigation.md#open-search).

::: learning_app.ui.inplace_search
