import logging
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
from handlers import start, choice, choose_survey, ask_question, answers, cancel, new_survey_response
from states import CHOOSING, CHOOSING_SURVEY, TYPING_REPLY, NEW_SURVEY

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def main() -> None:
    app = Application.builder().token("TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choice)],
            CHOOSING_SURVEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_survey)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, answers)],
            NEW_SURVEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_survey_response)]
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)]
    )

    app.add_handler(conv_handler)

    logger.info("Starting bot.")
    app.run_polling()
    logger.info("Bot stopped.")

if __name__ == '__main__':
    main()