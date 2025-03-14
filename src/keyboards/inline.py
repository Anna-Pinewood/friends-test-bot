"""
Inline keyboards for the Friends Test bot.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import texts


def get_options_keyboard(options):
    """
    Create a keyboard with answer options.

    Args:
        options (list): List of answer options

    Returns:
        InlineKeyboardMarkup: Keyboard with answer options
    """
    builder = InlineKeyboardBuilder()

    for i, option in enumerate(options):
        builder.add(
            InlineKeyboardButton(text=option, callback_data=f"answer_{i}")
        )

    # One button per row
    builder.adjust(1)

    return builder.as_markup()


def get_start_test_keyboard():
    """
    Create a keyboard with the "Create Test" button.

    Returns:
        InlineKeyboardMarkup: Keyboard with the create test button
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=texts.CREATE_TEST_BUTTON, callback_data="create_test")
    )
    return builder.as_markup()


def get_share_keyboard(test_link):
    """
    Create a keyboard with a button to share the test.

    Args:
        test_link (str): Link to share

    Returns:
        InlineKeyboardMarkup: Keyboard with share button
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=texts.SHARE_TEST_BUTTON, url=test_link)
    )
    return builder.as_markup()
