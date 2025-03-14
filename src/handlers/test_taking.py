"""
Handlers for taking tests created by other users.
"""
import json
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src import texts
from src.states import TestStates
from src.keyboards import get_options_keyboard
from src.db.database import db

# Initialize router
router = Router()
logger = logging.getLogger(__name__)

# Load questions from JSON file
with open('questions.json', 'r', encoding='utf-8') as f:
    QUESTIONS = json.load(f)['questions']


@router.callback_query(TestStates.taking_test, F.data.startswith("answer_"))
async def process_taking_answer(callback: types.CallbackQuery, state: FSMContext):
    """Process answer when taking someone else's test."""
    await callback.answer()

    # Get the selected answer index
    answer_index = int(callback.data.split("_")[1])

    # Get current state data
    data = await state.get_data()
    current_question_index = data['current_question']
    answers = data['answers']
    test_id = data['test_id']
    creator_id = data['creator_id']

    # Check if index is valid
    if current_question_index >= len(QUESTIONS):
        logger.error(f"Question index out of range: {current_question_index}, total questions: {len(QUESTIONS)}")
        await callback.bot.edit_message_text(
            text="Произошла ошибка при обработке ответа. Пожалуйста, начните тест заново.",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
        await state.clear()
        return

    # Save this answer
    question_id = str(QUESTIONS[current_question_index]['id'])
    answers[question_id] = answer_index

    # Move to next question
    current_question_index += 1
    await state.update_data(current_question=current_question_index, answers=answers)

    # Rest of the function remains the same...

    if current_question_index < len(QUESTIONS):
        # Still have questions - send the next one
        await send_next_question(callback.bot, callback.message.chat.id, state, callback.message.message_id)
    else:
        # Test completed - calculate results
        taker_id = callback.from_user.id
        taker_username = callback.from_user.username or callback.from_user.first_name or str(taker_id)

        # Save result
        result = await db.save_test_result(test_id, taker_id, taker_username, answers)

        if not result:
            await callback.bot.edit_message_text(
                text=texts.ERROR_MESSAGE,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id
            )
            await state.clear()
            return

        # Send result to test taker
        creator_name = result['creator']['first_name'] or result['creator']['username'] or "этого пользователя"
        await callback.bot.edit_message_text(
            text=texts.TEST_COMPLETED.format(
                creator_name=creator_name,
                percentage=result['percentage'],
                status=result['status']
            ),
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        # Prepare detailed answers for notification
        # Prepare detailed answers for notification
        answers_details = ""
        for question in QUESTIONS:
            q_id = str(question['id'])
            if q_id in answers:
                user_answer_index = answers[q_id]
                user_answer = question['options'][user_answer_index]

                # Check if the creator has answered this question
                if q_id in result['creator']['answers']:
                    correct_answer_index = result['creator']['answers'][q_id]
                    correct_answer = question['options'][correct_answer_index]

                    # Mark if answer is correct
                    is_correct = "✅" if user_answer_index == correct_answer_index else "❌"

                    answers_details += f"{is_correct} {question['text']}\n"
                    answers_details += f"- Выбран ответ: {user_answer}\n"
                    if user_answer_index != correct_answer_index:
                        answers_details += f"- Правильный ответ: {correct_answer}\n"
                    answers_details += "\n"
                else:
                    # Creator didn't answer this question
                    answers_details += f"❓ {question['text']}\n"
                    answers_details += f"- Выбран ответ: {user_answer}\n"
                    answers_details += "- Создатель теста не ответил на этот вопрос\n\n"

        # Notify test creator
        await callback.bot.send_message(
            chat_id=creator_id,
            text=texts.NEW_RESULT_NOTIFICATION.format(
                username=f"@{taker_username}" if '@' not in taker_username else taker_username,
                percentage=result['percentage'],
                status=result['status'],
                answers_details=answers_details
            )
        )

        # Reset state
        await state.clear()


@router.message(TestStates.taking_test)
async def handle_message_during_test(message: types.Message, state: FSMContext):
    """
    Handle messages sent while taking a test.

    Args:
        message: Message from the user
        state: FSM context for managing conversation state
    """
    # Tell the user to use the buttons
    await message.answer("Пожалуйста, используйте кнопки для ответа на вопросы теста.")

    # Resend the current question
    data = await state.get_data()
    current_question_index = data.get('current_question', 0)

    # Only resend if we're within question bounds
    if 0 <= current_question_index < len(QUESTIONS):
        await send_next_question(message.bot, message.chat.id, state)


async def send_next_question(bot, chat_id, state, message_id=None):
    """
    Send the next question based on the current state.
    """
    # Get current state data
    data = await state.get_data()
    current_question_index = data['current_question']

    # Check if index is valid
    if current_question_index >= len(QUESTIONS):
        logger.error(f"Question index out of range: {current_question_index}, total questions: {len(QUESTIONS)}")
        await bot.send_message(
            chat_id=chat_id,
            text="Произошла ошибка при загрузке следующего вопроса. Пожалуйста, начните тест заново."
        )
        await state.clear()
        return

    # Get the current question
    question = QUESTIONS[current_question_index]

    # Rest of the function remains the same...

    # Prepare the message text
    message_text = texts.TAKING_TEST_QUESTION.format(
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
