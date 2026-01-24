import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.config import logger
from bot import handlers

def main() -> None:
    """봇을 시작하고 실행합니다."""
    logger.info("봇을 시작합니다...")

    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("텔레그램 토큰이 .env 파일에 설정되지 않았습니다.")
        return

    application = Application.builder().token(token).build()

    # 영어 명령어 핸들러 등록
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("sp500", handlers.sp500_command))
    application.add_handler(CommandHandler("nasdaq", handlers.nasdaq_command))
    application.add_handler(CommandHandler("vix", handlers.vix_command))
    application.add_handler(CommandHandler("stock", handlers.stock_command))
    application.add_handler(CommandHandler("exchange", handlers.exchange_command))

    # 한글 명령어 핸들러 등록
    korean_commands = ["시작", "도움말", "에스엔피500", "나스닥", "빅스", "환율", "주식"]
    regex_pattern = r'^/(' + '|'.join(korean_commands) + r')'
    application.add_handler(MessageHandler(filters.Regex(regex_pattern), handlers.korean_command_router))

    application.run_polling()

if __name__ == '__main__':
    main()
