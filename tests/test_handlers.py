
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.handlers import start, help_command, stock_command

# Note: I need to mock get_stock_info and find_ticker in handlers.py context
# But since I can't easily modify the imports in handlers.py without patching, I will use patch.

@pytest.mark.asyncio
async def test_start_command():
    update = AsyncMock()
    context = AsyncMock()
    # mention_html is not async, so we must use MagicMock
    update.effective_user.mention_html = MagicMock(return_value="User")
    
    await start(update, context)
    
    update.message.reply_html.assert_called_once()
    assert "안녕하세요" in update.message.reply_html.call_args[0][0]

@pytest.mark.asyncio
async def test_help_command():
    update = AsyncMock()
    context = AsyncMock()
    
    await help_command(update, context)
    
    update.message.reply_text.assert_called_once()
    assert "사용 가능한 명령어" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_stock_command_no_args():
    update = AsyncMock()
    context = AsyncMock()
    context.args = []
    
    await stock_command(update, context)
    
    update.message.reply_text.assert_called_with("사용법: `/stock <종목명 또는 티커>`", parse_mode='Markdown')

@pytest.mark.asyncio
@patch("bot.handlers.find_ticker")
@patch("bot.handlers.get_stock_info")
async def test_stock_command_success(mock_get_info, mock_find_ticker):
    update = AsyncMock()
    context = AsyncMock()
    context.args = ["Tesla"]
    
    # Mock finding ticker
    mock_find_ticker.return_value = {"symbol": "TSLA", "name": "Tesla Inc"}
    
    # Mock getting info
    mock_get_info.return_value = {
        "shortName": "Tesla Inc",
        "currentPrice": 200.0,
        "change": 10.0,
        "changePercent": 5.0,
        "currency": "USD"
    }
    
    await stock_command(update, context)
    
    # Check that it replied initially
    assert update.message.reply_text.call_count == 1
    # Check that it edited the message with result
    sent_message = update.message.reply_text.return_value
    sent_message.edit_text.assert_called_once()
    args = sent_message.edit_text.call_args[0][0]
    assert "*Tesla Inc*" in args
    assert "200.00" in args

@pytest.mark.asyncio
@patch("bot.handlers.find_ticker")
async def test_stock_command_not_found(mock_find_ticker):
    update = AsyncMock()
    context = AsyncMock()
    context.args = ["Invalid"]
    
    mock_find_ticker.return_value = None
    
    await stock_command(update, context)

    sent_message = update.message.reply_text.return_value
    sent_message.edit_text.assert_called_once()
    assert "찾을 수 없습니다" in sent_message.edit_text.call_args[0][0]
