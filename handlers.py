from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
import logging
import requests
from data import simple_questions, detailed_questions, simple_buttons, detailed_buttons
from states import CHOOSING_SURVEY, TYPING_REPLY, CHOOSING, NEW_SURVEY
from utils.categorization import categorize_user_data


logger = logging.getLogger(__name__)


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.effective_user.id} started the bot.")
    keyboard = [
        ["Программа тренировок", "Диета"],
        ["Оба варианта"],
        ["Отмена"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    logger.info("Sending start message with options.")
    await update.message.reply_text(
        'Добро пожаловать! Выберите, что хотите получить:',
        reply_markup=reply_markup
    )
    logger.info("Start message sent.")
    return CHOOSING


# Обработчик выбора типа результата
async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.message.from_user.id} chose: {update.message.text}.")
    if update.message.text == 'Программа тренировок':
        context.user_data['type'] = 'workout'
    elif update.message.text == 'Диета':
        context.user_data['type'] = 'diet'
    elif update.message.text == 'Оба варианта':
        context.user_data['type'] = 'both'
    else:
        return await cancel(update, context)

    keyboard = [
        ["Простой опрос", "Расширенный опрос"],
        ["Отмена"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        'Выберите тип опроса:',
        reply_markup=reply_markup
    )
    return CHOOSING_SURVEY


# Обработчик выбора типа опросника
async def choose_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"User {update.message.from_user.id} chose survey: {update.message.text}.")
    if update.message.text == 'Простой опрос':
        context.user_data['questions'] = simple_questions
        context.user_data['buttons'] = simple_buttons
    elif update.message.text == 'Расширенный опрос':
        context.user_data['questions'] = detailed_questions
        context.user_data['buttons'] = detailed_buttons
    else:
        return await cancel(update, context)

    context.user_data['current_question'] = 0
    logger.info("Asking the first question.")
    await update.message.reply_text("Отлично! Теперь давайте соберем некоторые данные о вас.",
                                    reply_markup=ReplyKeyboardRemove())
    return await ask_question(update.message, context)


# Обработчик вопросов
async def ask_question(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_index = context.user_data.get('current_question', 0)

    questions = context.user_data.get('questions', [])
    buttons = context.user_data.get('buttons', [])

    if question_index < len(questions):
        question = questions[question_index]
        reply_markup = buttons[question_index]
        logger.info(f"Asking question: {question}")

        if reply_markup:
            await message.reply_text(question, reply_markup=ReplyKeyboardMarkup(reply_markup, one_time_keyboard=True,
                                                                                resize_keyboard=True))
        else:
            await message.reply_text(question, reply_markup=ReplyKeyboardMarkup([["Отмена"]], one_time_keyboard=True,
                                                                                resize_keyboard=True))

        logger.info("Question sent.")
        return TYPING_REPLY
    else:
        return await process_data(message, context)


# Обработчик ответов
async def answers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text

    if answer == 'Отмена':
        return await cancel(update, context)

    question_index = context.user_data.get('current_question', 0)
    context.user_data[question_index] = answer

    logger.info(f"User {update.effective_user.id} answered: {answer}.")

    context.user_data['current_question'] = question_index + 1
    questions = context.user_data.get('questions', [])
    if question_index + 1 < len(questions):
        return await ask_question(update.message, context)
    else:
        return await process_data(update.message, context)


# Обработка данных и отправка на сервер
async def process_data(message, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Получаем вопросы из контекста
    questions = context.user_data.get('questions', [])
    # Формируем user_info из данных, введенных пользователем
    user_info = {questions[i]: context.user_data.get(i, '') for i in range(len(questions))}
    # Получаем тип данных из контекста, устанавливаем значение по умолчанию
    data_type = context.user_data.get('type', 'unknown')

    logger.info(f"User {message.from_user.id} data to send to server: {user_info}")

    # Категоризация данных пользователя
    categorized_data = categorize_user_data(user_info)

    # Отправка данных на сервер
    response = requests.post(
        'http://localhost:5000/process_data',
        json={'type': data_type, 'data': categorized_data}
    )

    logger.info(f"Server response status code: {response.status_code}")

    if response.status_code != 200:
        await message.reply_text("Произошла ошибка при обработке данных. Попробуйте еще раз позже.")
        logger.error(f"Error from server: {response.status_code}")
    else:
        plan = response.json()
        await message.reply_text(f"Ваш персонализированный план готов:\n{plan}")
        logger.info(f"User {message.from_user.id} received plan: {plan}")

    await show_new_survey_menu(message, context)
    return NEW_SURVEY

async def show_new_survey_menu(message, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Программа тренировок", "Диета"],
        ["Оба варианта"],
        ["Отмена"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await message.reply_text("Хотите начать новый опрос?", reply_markup=reply_markup)

# Обработчик ответа на вопрос о новом опросе
async def new_survey_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text

    if answer == 'Да':
        return await start(update, context)
    else:
        await update.message.reply_text('Спасибо за участие! Вы можете начать новый опрос командой /start.',
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


# Отмена опроса
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Опрос отменен.', reply_markup=ReplyKeyboardRemove())
    logger.info(f"User {update.effective_user.id} cancelled the conversation.")
    return ConversationHandler.END
