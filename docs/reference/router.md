# Router

Source: `ui/router.py`

Route-change and resize handlers that build views, synchronize shell chrome,
and apply route-specific layouts. Screen authors normally use
[Navigation API](navigation.md) instead; see the
[Routing concept](../concepts/routing.md) for the end-to-end flow and
[Startup and lifecycle](../architecture/startup.md) for when handlers are
attached in `app.py`. After a route change that leaves `/set/learn`, the
router drops that set's open visit id. Counters already written stay on the
visit row. See [Data and storage](../architecture/data-and-storage.md#set_opened).

::: learning_app.ui.router
