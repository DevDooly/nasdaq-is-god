
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from bot.finance_api import find_ticker, get_stock_info

# --- Tests for find_ticker ---

@pytest.mark.asyncio
async def test_find_ticker_found():
    mock_response_data = {
        "quotes": [
            {"symbol": "TSLA", "longname": "Tesla Inc", "quoteType": "EQUITY"},
            {"symbol": "TSLA.BA", "longname": "Tesla Inc", "quoteType": "EQUITY"}
        ]
    }
    
    with patch("bot.finance_api.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client.get.return_value = mock_response
        
        result = await find_ticker("Tesla")
        assert result == {"symbol": "TSLA", "name": "Tesla Inc"}

@pytest.mark.asyncio
async def test_find_ticker_not_found():
    mock_response_data = {"quotes": []}
    
    with patch("bot.finance_api.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        mock_client.get.return_value = mock_response
        
        result = await find_ticker("UnknownStock")
        assert result is None

# --- Tests for get_stock_info ---

@pytest.mark.asyncio
async def test_get_stock_info_success():
    with patch("yfinance.Ticker") as mock_ticker:
        # Mocking info
        mock_instance = mock_ticker.return_value
        mock_instance.info = {
            "currentPrice": 100.0,
            "previousClose": 90.0,
            "open": 91.0,
            "dayHigh": 101.0,
            "dayLow": 89.0,
            "volume": 50000,
            "shortName": "Test Corp",
            "currency": "USD"
        }
        # Mocking history to be empty or irrelevant if currentPrice is in info
        # But code checks hist['Close'].iloc[-1] first
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.__len__.return_value = 2
        
        # Setting up iloc behavior for history dataframe
        # We need a way to mock hist['Close'].iloc[-1]
        # Easier to mock the dataframe behavior or just make history empty to rely on info
        
        # Let's try making history not empty
        mock_hist.__getitem__.return_value.iloc.__getitem__.side_effect = [100.0, 90.0] # current, prev
        mock_instance.history.return_value = mock_hist

        result = await get_stock_info("TEST")
        
        assert result["shortName"] == "Test Corp"
        assert result["currentPrice"] == 100.0
        assert result["change"] == 10.0
        assert result["changePercent"] == (10.0 / 90.0) * 100

@pytest.mark.asyncio
async def test_get_stock_info_error():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = mock_ticker.return_value
        # Simulate an exception
        mock_instance.history.side_effect = Exception("API Error")
        
        result = await get_stock_info("ERROR")
        assert "error" in result
