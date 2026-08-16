import flet as ft


def _dialog_title_value(dlg):
    raw = getattr(dlg, "title", None)
    if isinstance(raw, str):
        return raw
    return getattr(raw, "value", None)


def _open_dialog_titles(page):
    dialogs = getattr(page, "_dialogs", None)
    controls = getattr(dialogs, "controls", None) if dialogs is not None else None
    if not controls:
        return []
    return [
        _dialog_title_value(dlg)
        for dlg in controls
        if getattr(dlg, "open", False)
    ]


def _pop_open_dialogs_with_title(page, title):
    """Close stacked duplicates that share ``title`` (the top dialog is already closed)."""
    while title in _open_dialog_titles(page):
        if page.pop_dialog() is None:
            break


def create_alert_dialog(
    page,
    title,
    content,
    close_button_text="OK",
    action_button_text=None,
    action_function=None,
    close_action_function=None,
    secondary_button_text=None,
    secondary_action_function=None,
):
    """
    Creates and displays an alert dialog using the Flet library.
    This function creates a customizable alert dialog with a title, content, and action buttons.
    The dialog is added to the page's overlay and displayed immediately.
    Parameters:
        page (ft.Page): The page where the dialog should be displayed.
        title (str): The title text of the alert dialog.
        content (str): The main content text of the alert dialog.
        close_button_text (str, optional): The text for the close/cancel button. Defaults to "OK".
        action_button_text (str, optional): The text for the optional primary action button.
            Required if action_function is provided.
        action_function (callable, optional): A function to be called when the primary action
            button is clicked. Should accept an event parameter.
        close_action_function (callable, optional): A function to be called when the close button
            is clicked or the dialog is dismissed (e.g. tap outside). Should accept an event
            parameter. When omitted, close/dismiss only closes the dialog.
        secondary_button_text (str, optional): The text for an optional middle button.
            Required if secondary_action_function is provided.
        secondary_action_function (callable, optional): A function to be called when the
            secondary button is clicked. Should accept an event parameter.
    Returns:
        None: The function displays the dialog but doesn't return any value.
    Note:
        Action buttons call ``page.pop_dialog()`` themselves (same pattern as the
        change-title dialog). Flet already removes the dialog on a tap outside.
        A second call with the same title is ignored while that dialog is still
        open. Closing (button or tap outside) also pops remaining open dialogs
        with the same title.
    """
    if title in _open_dialog_titles(page):
        return

    callback_handled = False

    def run_callback(e, callback):
        nonlocal callback_handled
        if callback is None or callback_handled:
            return
        callback_handled = True
        callback(e)

    def close_action(e):
        page.pop_dialog()
        _pop_open_dialogs_with_title(page, title)
        run_callback(e, close_action_function)
        page.update()

    def action(e):
        page.pop_dialog()
        _pop_open_dialogs_with_title(page, title)
        run_callback(e, action_function)
        page.update()

    def secondary_action(e):
        page.pop_dialog()
        _pop_open_dialogs_with_title(page, title)
        run_callback(e, secondary_action_function)
        page.update()

    def dismiss_action(e):
        # Barrier dismiss already closed the top dialog; clear stacked copies.
        _pop_open_dialogs_with_title(page, title)
        run_callback(e, close_action_function)

    actions = [ft.TextButton(close_button_text, on_click=close_action)]

    if secondary_action_function:
        actions.append(ft.TextButton(secondary_button_text, on_click=secondary_action))

    if action_function:
        actions.append(ft.TextButton(action_button_text, on_click=action))

    alert_dialog = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(content),
        actions=actions,
        actions_alignment=ft.MainAxisAlignment.END,
        on_dismiss=dismiss_action,
    )

    page.show_dialog(alert_dialog)


def set_theme_from_bgcolor(page, bgcolor):
    from learning_app.ui.app_theme import AppTheme

    AppTheme.apply_bgcolor(page, bgcolor)
