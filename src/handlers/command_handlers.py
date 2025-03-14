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
/stats - Показать статистику ваших тестов
/top - Показать топ друзей по всем тестам
/help - Показать эту справку

Как пользоваться:
1. Нажмите на кнопку "Создать тест о себе"
2. Ответьте на вопросы о себе
3. Получите ссылку и поделитесь ею с друзьями
4. Друзья пройдут тест и узнают, насколько хорошо они вас знают
5. Вы получите уведомление о каждом прохождении теста
6. Используйте /stats чтобы увидеть статистику
    """
    await message.answer(help_text)


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """
    Handle the /stats command.
    Show statistics for the user's tests.

    Args:
        message: Message from the user
    """
    user_id = message.from_user.id

    # Get test statistics for the user
    stats = await db.get_test_statistics(user_id)

    if not stats or stats['tests_count'] == 0:
        # No tests created
        await message.answer(texts.STATS_NO_TESTS)
        return

    # Format the message
    tests_word = get_word_form(stats['tests_count'], ["тест", "теста", "тестов"])

    overview = texts.STATS_OVERVIEW.format(
        tests_count=stats['tests_count'],
        tests_word=tests_word,
        total_passes=stats['total_passes'],
        average_score=stats['average_score']
    )

    if stats['total_passes'] == 0:
        # No passes yet
        await message.answer(texts.STATS_HEADER + "\n" + overview + "\n" + texts.STATS_NO_PASSES)
        return

    # Format best friends
    best_friends_text = ""
    if stats['best_friends']:
        for i, friend in enumerate(stats['best_friends'][:5], 1):
            best_friends_text += f"{i}. {friend['username']} - {friend['score']}%\n"
    else:
        best_friends_text = "Пока нет данных"

    # Format worst friends
    worst_friends_text = ""
    if stats['worst_friends']:
        for i, friend in enumerate(stats['worst_friends'][:5], 1):
            worst_friends_text += f"{i}. {friend['username']} - {friend['score']}%\n"
    else:
        worst_friends_text = "Пока нет данных"

    best_friends_section = texts.STATS_BEST_FRIENDS.format(best_friends=best_friends_text)
    worst_friends_section = texts.STATS_WORST_FRIENDS.format(worst_friends=worst_friends_text)

    # Compile the full message
    full_message = f"{texts.STATS_HEADER}\n{overview}\n{best_friends_section}\n{worst_friends_section}"

    await message.answer(full_message)


@router.message(Command("top"))
async def cmd_top_friends(message: types.Message):
    """
    Handle the /top command.
    Show top friends across all tests.

    Args:
        message: Message from the user
    """
    # Get top friends
    top_friends = await db.get_top_friends(10)

    if not top_friends:
        await message.answer(texts.TOP_FRIENDS_EMPTY)
        return

    # Format the message
    top_text = texts.TOP_FRIENDS_HEADER + "\n\n"

    for i, friend in enumerate(top_friends, 1):
        passes_word = get_word_form(friend['passes_count'], ["тест", "теста", "тестов"])
        top_text += texts.TOP_FRIENDS_ENTRY.format(
            index=i,
            username=friend['username'],
            score=friend['average_score'],
            passes_count=friend['passes_count'],
            passes_word=passes_word
        ) + "\n"

    await message.answer(top_text)


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


def get_word_form(number, forms):
    """
    Get the correct word form based on the number.

    Args:
        number: The number to base the form on
        forms: List of three forms [singular, few, many]

    Returns:
        str: The correct word form
    """
    if number % 100 in (11, 12, 13, 14):
        return forms[2]

    remainder = number % 10
    if remainder == 1:
        return forms[0]
    if remainder in (2, 3, 4):
        return forms[1]

    return forms[2]
