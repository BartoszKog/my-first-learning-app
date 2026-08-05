import flet as ft


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
        This function automatically handles adding the dialog to the page overlay and removing it
        when either button is clicked.
    """
    action_handled = False

    def run_dialog_action(e, callback=None, *, pop_dialog=True):
        nonlocal action_handled
        if action_handled:
            return
        action_handled = True
        if pop_dialog:
            e.page.pop_dialog()
        if callback:
            callback(e)
        e.page.update()

    def close_action(e):
        if close_action_function:
            run_dialog_action(e, close_action_function)
        else:
            run_dialog_action(e)

    def dismiss_action(e):
        # Barrier dismiss already removes the dialog; only run the close callback once.
        if close_action_function:
            run_dialog_action(e, close_action_function, pop_dialog=False)
        else:
            run_dialog_action(e, pop_dialog=False)

    actions = [ft.TextButton(close_button_text, on_click=close_action)]

    if secondary_action_function:
        def secondary_action(e):
            run_dialog_action(e, secondary_action_function)

        actions.append(ft.TextButton(secondary_button_text, on_click=secondary_action))

    if action_function:
        def action(e):
            run_dialog_action(e, action_function)

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
