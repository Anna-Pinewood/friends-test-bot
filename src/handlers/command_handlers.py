"""
Command handlers for the bot.
"""
import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src import texts
from src.keyboards import get_start_test_keyboard
from src.db.database import db
from src.states import TestStates
from src.handlers.test_taking import send_next_question

# Initialize router
router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handle the /start command.
    Check if there's a deep link parameter to take a test.

    Args:
        message: Message from the user
        state: FSM context for managing conversation state
    """
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Save user to database
    await db.add_user(user_id, username, first_name, last_name)

    # Check if we have a test_id in the deep link
    if args and args[0].startswith('s_'):
        test_id = args[0]
        test_info = await db.get_test(test_id)

        if not test_info:
            await message.answer(texts.TEST_NOT_FOUND)
            return

        # Start taking the test
        creator_name = test_info['first_name'] or test_info['username'] or "этого пользователя"
        await message.answer(
            texts.TAKING_TEST_START.format(creator_name=creator_name)
        )

        # Set state and data
        await state.set_state(TestStates.taking_test)
        await state.update_data(
            test_id=test_id,
            creator_id=test_info['user_id'],
            current_question=0,
            answers={}
        )

        # Send the first question
        await send_next_question(message.bot, message.chat.id, state)
    else:
        # Normal start - offer to create a test
        await message.answer(
            texts.START_MESSAGE,
            reply_markup=get_start_test_keyboard()
        )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """
    Handle the /help command.

    Args:
        message: Message from the user
    """
    help_text = """
Этот бот поможет вам создать тест "Насколько хорошо тебя знают твои друзья".

Команды:
/start - Начать работу с ботом
/help - Показать эту справку

Как пользоваться:
1. Нажмите на кнопку "Создать тест о себе"
2. Ответьте на вопросы о себе
3. Получите ссылку и поделитесь ею с друзьями
4. Друзья пройдут тест и узнают, насколько хорошо они вас знают
5. Вы получите уведомление о каждом прохождении теста
    """
    await message.answer(help_text)


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """
    Handle the /cancel command.
    Cancel any ongoing operation.

    Args:
        message: Message from the user
        state: FSM context for managing conversation state
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять.")
        return

    await state.clear()
    await message.answer("Действие отменено. Вы можете начать заново.")
