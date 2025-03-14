"""
Handlers for test creation.
"""
import json
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src import texts
from src.states import TestStates
from src.keyboards import get_options_keyboard, get_share_keyboard
from src.db.database import db

# Initialize router
router = Router()
logger = logging.getLogger(__name__)

# Load questions from JSON file
with open('questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS = json.load(f)['questions']


@router.callback_query(F.data == "create_test")
async def create_test(callback: types.CallbackQuery, state: FSMContext):
    """
    Start the test creation process.

    Args:
        callback: Callback query from the "Create Test" button
        state: FSM context for managing conversation state
    """
    await callback.answer()

    await callback.message.answer(texts.CREATE_TEST_START)

    # Set state
    await state.set_state(TestStates.creating_test)
    await state.update_data(current_question=0, answers={})

    # Send first question
    await send_next_question(callback.bot, callback.message.chat.id, state)


@router.callback_query(TestStates.creating_test, F.data.startswith("answer_"))
async def process_creating_answer(callback: types.CallbackQuery, state: FSMContext):
    """
    Process answer when creating a test.

    Args:
        callback: Callback query with the selected answer
        state: FSM context for managing conversation state
    """
    await callback.answer()

    # Get the selected answer index
    answer_index = int(callback.data.split("_")[1])

    # Get current state data
    data = await state.get_data()
    current_question_index = data['current_question']
    answers = data['answers']

    # Save this answer
    question_id = str(QUESTIONS[current_question_index]['id'])
    answers[question_id] = answer_index

    # Move to next question
    current_question_index += 1
    await state.update_data(current_question=current_question_index, answers=answers)

    if current_question_index < len(QUESTIONS):
        # Still have questions - send the next one
        await send_next_question(callback.bot, callback.message.chat.id, state, callback.message.message_id)
    else:
        # Test completed - save it and generate link
        user_id = callback.from_user.id
        test_id = await db.create_test(user_id, answers)

        # Get bot username for creating the deep link
        bot = callback.bot
        bot_info = await bot.get_me()
        bot_username = bot_info.username

        test_link = f"https://t.me/{bot_username}?start={test_id}"

        # Send completion message with the link
        await bot.edit_message_text(
            text=texts.TEST_CREATED.format(link=test_link),
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=get_share_keyboard(test_link)
        )

        # Reset state
        await state.clear()


async def send_next_question(bot, chat_id, state, message_id=None):
    """
    Send the next question based on the current state.

    Args:
        bot: Bot instance to send messages
        chat_id: ID of the chat to send the message to
        state: FSM context for managing conversation state
        message_id: Optional message ID to edit instead of sending a new message
    """
    # Get current state data
    data = await state.get_data()
    current_question_index = data['current_question']

    # Get the current question
    question = QUESTIONS[current_question_index]

    # Prepare the message text
    message_text = texts.QUESTION_TEMPLATE.format(
        current=current_question_index + 1,
        total=len(QUESTIONS),
        question=question['text']
    )

    # Get the keyboard with options
    markup = get_options_keyboard(question['options'])

    # Send or edit the message
    if message_id:
        await bot.edit_message_text(
            text=message_text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup
        )
    else:
        await bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=markup
        )
