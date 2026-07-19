# App Chrome

Source: `ui/app_chrome.py`

Registry of shared Shell chrome controls (AppBar, bottom bar, FAB, drawer)
created at startup. Declarative per-route flags live in
[Chrome configuration](chrome_config.md); how they work together is in
[Chrome and wrappers](../concepts/chrome-and-wrappers.md). Startup order is in
[Startup](../architecture/startup.md).

::: learning_app.ui.app_chrome
