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

# Errors
TEST_NOT_FOUND = "Тест не найден. Возможно, создатель удалил его или ссылка неверна."
ERROR_MESSAGE = "Произошла ошибка. Пожалуйста, попробуйте еще раз или обратитесь к администратору."
