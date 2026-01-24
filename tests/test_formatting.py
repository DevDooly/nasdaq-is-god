
from bot.formatting import format_exchange_rate_data, format_stock_data

def test_format_exchange_rate_data_full():
    data = {
        "shortName": "USD/KRW",
        "currentPrice": 1300.0,
        "change": 10.0,
        "changePercent": 0.77,
        "open": 1290.0,
        "dayHigh": 1310.0,
        "dayLow": 1290.0,
    }
    expected = (
        "*USD/KRW 환율*\n"
        "현재가: 1,300.00원 (+10.00 / +0.77%)\n"
        "시가: 1,290.00원\n"
        "고가: 1,310.00원\n"
        "저가: 1,290.00원"
    )
    assert format_exchange_rate_data(data) == expected

def test_format_exchange_rate_data_negative():
    data = {
        "shortName": "USD/KRW",
        "currentPrice": 1290.0,
        "change": -10.0,
        "changePercent": -0.77,
    }
    expected = (
        "*USD/KRW 환율*\n"
        "현재가: 1,290.00원 (-10.00 / -0.77%)"
    )
    assert format_exchange_rate_data(data) == expected

def test_format_stock_data_full():
    data = {
        "shortName": "Tesla",
        "currentPrice": 200.0,
        "change": 5.0,
        "changePercent": 2.5,
        "currency": "USD",
        "open": 195.0,
        "dayHigh": 205.0,
        "dayLow": 190.0,
        "volume": 1000000,
    }
    expected = (
        "*Tesla*\n"
        "현재가: 200.00 USD (+5.00 / +2.50%)\n"
        "시가: 195.00 USD\n"
        "고가: 205.00 USD\n"
        "저가: 190.00 USD\n"
        "거래량: 1,000,000"
    )
    assert format_stock_data(data) == expected

def test_format_stock_data_minimal():
    data = {
        "shortName": "Apple",
        "currentPrice": 150.0,
        "currency": "USD"
    }
    expected = (
        "*Apple*\n"
        "현재가: 150.00 USD"
    )
    assert format_stock_data(data) == expected
