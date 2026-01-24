from telegram import Update
from telegram.ext import ContextTypes
from .config import logger
from .finance_api import get_stock_info, find_ticker
from .formatting import format_exchange_rate_data, format_stock_data

# --- 명령어 핸들러 함수 ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start 명령어 응답"""
    user = update.effective_user
    await update.message.reply_html(
        f"안녕하세요, {user.mention_html()}님!\n"
        f"저는 증시 정보를 알려주는 봇입니다. /help 명령어로 사용법을 확인하세요."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help 명령어 응답"""
    help_text = """
    **사용 가능한 명령어 목록:**
    /start, /시작 - 봇 시작
    /help, /도움말 - 도움말 보기
    /sp500, /에스엔피500 - S&P 500 지수 조회
    /nasdaq, /나스닥 - 나스닥 지수 조회
    /vix, /빅스 - VIX 지수 조회
    /exchange, /환율 - 환율 정보 조회 (USD/KRW)
    /stock, /주식 <종목명 또는 티커> - 개별 종목 조회
    
    *추가될 기능:*
    - 정기 알림 기능
    - 사용자 포트폴리오 관리
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def fetch_index_data(update: Update, context: ContextTypes.DEFAULT_TYPE, ticker_symbol: str, index_name: str) -> None:
    """공통 인덱스 데이터 조회 및 응답 함수"""
    logger.info(f"Fetching {index_name} data for {update.effective_user.id}")
    data = await get_stock_info(ticker_symbol)

    if data.get("error"):
        await update.message.reply_text(data["error"])
        return

    message = format_stock_data(data)
    await update.message.reply_text(message, parse_mode='Markdown')

async def sp500_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sp500 명령어 응답"""
    await fetch_index_data(update, context, "^GSPC", "S&P 500")

async def nasdaq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/nasdaq 명령어 응답"""
    await fetch_index_data(update, context, "^IXIC", "Nasdaq")

async def vix_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/vix 명령어 응답"""
    await fetch_index_data(update, context, "^VIX", "VIX")

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/stock <종목명 또는 티커> 명령어 응답"""
    if not context.args:
        await update.message.reply_text("사용법: `/stock <종목명 또는 티커>`", parse_mode='Markdown')
        return

    query = ' '.join(context.args)
    sent_message = await update.message.reply_text(f"'{query}'에 대한 정보를 검색 중입니다...")

    ticker_info = await find_ticker(query)

    if not ticker_info:
        await sent_message.edit_text(f"'{query}'에 해당하는 종목을 찾을 수 없습니다. 종목명이나 티커를 확인해주세요.")
        return

    ticker_symbol = ticker_info['symbol']
    logger.info(f"Fetching stock data for {ticker_symbol} ({query}) by {update.effective_user.id}")
    
    data = await get_stock_info(ticker_symbol)

    if data.get("error"):
        await sent_message.edit_text(data["error"])
        return
    
    data['shortName'] = ticker_info.get('name', data.get('shortName'))

    message = format_stock_data(data)
    await sent_message.edit_text(message, parse_mode='Markdown')

async def exchange_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/exchange 명령어 응답 (USD/KRW)"""
    logger.info(f"Fetching exchange rate for {update.effective_user.id}")
    data = await get_stock_info("KRW=X") # USD/KRW 티커

    if data.get("error"):
        await update.message.reply_text(data["error"])
        return

    message = format_exchange_rate_data(data)
    await update.message.reply_text(message, parse_mode='Markdown')

async def korean_command_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """한글 명령어를 감지하고 적절한 함수로 라우팅합니다."""
    text = update.message.text
    command = text.split()[0][1:]

    command_map = {
        "시작": start,
        "도움말": help_command,
        "에스엔피500": sp500_command,
        "나스닥": nasdaq_command,
        "빅스": vix_command,
        "환율": exchange_command,
        "주식": stock_command,
    }

    if command in command_map:
        if command == "주식":
            context.args = text.split()[1:]
        
        await command_map[command](update, context)
