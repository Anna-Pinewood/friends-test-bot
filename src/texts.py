"""
All text messages used in the bot.
"""

# Start messages
START_MESSAGE = "👋 Привет! Это бот для создания теста \"Насколько хорошо тебя знают твои друзья\"."
CREATE_TEST_BUTTON = "🎮 Создать тест о себе"
CREATE_TEST_START = "Отлично! Сейчас я задам тебе несколько вопросов о тебе. Выбери правильные ответы."

# Test flow messages
QUESTION_TEMPLATE = "Вопрос {current}/{total}:\n\n{question}"
TEST_CREATED = "🎉 Поздравляю! Вы создали свой тест.\nВаша ссылка: {link}"
SHARE_TEST_BUTTON = "📲 Поделиться тестом"

# Taking a test messages
TAKING_TEST_START = "Вы проходите тест пользователя {creator_name}. Ответьте на вопросы и узнайте, насколько хорошо вы знаете этого человека!"
TAKING_TEST_QUESTION = "Вопрос {current}/{total}:\n\n{question}"
TEST_COMPLETED = "Тест завершен!\n\nВы знаете {creator_name} на {percentage}%\n{status}"

# Notifications
NEW_RESULT_NOTIFICATION = "Пользователь {username} прошёл ваш тест с результатом: {percentage}% ({status})\n\nВопросы и ответы:\n{answers_details}"

# Statistics messages
STATS_HEADER = "📊 Статистика ваших тестов"
STATS_OVERVIEW = """
У вас {tests_count} {tests_word}
Всего прохождений: {total_passes}
Средний результат: {average_score}%
"""
STATS_BEST_FRIENDS = """
🥇 Лучшие друзья (знают вас лучше всех):
{best_friends}
"""
STATS_WORST_FRIENDS = """
Друзья, которые знают вас меньше всего:
{worst_friends}
"""
STATS_NO_TESTS = "У вас пока нет созданных тестов. Нажмите на кнопку \"Создать тест о себе\", чтобы создать свой первый тест!"
STATS_NO_PASSES = "Ваши тесты ещё никто не проходил. Поделитесь ссылкой с друзьями!"

# Top friends statistics
TOP_FRIENDS_HEADER = "🏆 Топ-10 друзей по знанию всех тестов:"
TOP_FRIENDS_ENTRY = "{index}. {username} - {score}% (прошёл {passes_count} {passes_word})"
TOP_FRIENDS_EMPTY = "Пока не набрано достаточно статистики. Чем больше людей пройдут тесты, тем точнее будет топ!"

# Errors
TEST_NOT_FOUND = "Тест не найден. Возможно, создатель удалил его или ссылка неверна."
ERROR_MESSAGE = "Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору."
