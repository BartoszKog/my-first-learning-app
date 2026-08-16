"""Canonical path constants for every application route.

Shell-route constants identify destinations hosted by shared application
chrome. Deep-route constants identify views pushed above that shell.

Attributes:
    HOME_ROUTE: Learning-sets shell at ``/``.
    IMPORT_EXPORT_ROUTE: Import and export shell.
    SETTINGS_ROUTE: Settings shell with reduced chrome.
    INFO_ROUTE: Information shell with reduced chrome.
    CREATE_SET_ROUTE: Deep form for creating a new set.
    SET_EDIT_ROUTE: Deep form for editing an existing set.
    SET_LEARN_ROUTE: Deep learn-mode entry for a set.
    SET_LEARN_SESSION_ROUTE: Deep active learn session for a set.
"""

HOME_ROUTE = "/"
IMPORT_EXPORT_ROUTE = "/import-export"
SETTINGS_ROUTE = "/settings"
INFO_ROUTE = "/info"
CREATE_SET_ROUTE = "/create-set"
SET_EDIT_ROUTE = "/set/edit"
SET_LEARN_ROUTE = "/set/learn"
SET_LEARN_SESSION_ROUTE = "/set/learn/session"
