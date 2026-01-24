
def format_exchange_rate_data(data: dict) -> str:
    """환율 데이터를 보기 좋은 문자열로 포매팅합니다."""
    short_name = data.get("shortName", "USD/KRW")
    current_price = data.get("currentPrice")
    change = data.get("change")
    change_percent = data.get("changePercent")
    
    price_str = f"{current_price:,.2f}" if current_price is not None else "N/A"
    change_str = ""
    if change is not None and change_percent is not None:
        sign = "+" if change >= 0 else ""
        change_str = f" ({sign}{change:,.2f} / {sign}{change_percent:,.2f}%)"

    open_price = data.get('open')
    day_high = data.get('dayHigh')
    day_low = data.get('dayLow')

    message = f"*{short_name} 환율*\n" \
              f"현재가: {price_str}원{change_str}\n"
    
    if open_price is not None:
        message += f"시가: {open_price:,.2f}원\n"
    if day_high is not None:
        message += f"고가: {day_high:,.2f}원\n"
    if day_low is not None:
        message += f"저가: {day_low:,.2f}원"
    
    return message.strip()

def format_stock_data(data: dict) -> str:
    """주식 데이터를 보기 좋은 문자열로 포매팅합니다."""
    short_name = data.get("shortName", "N/A")
    current_price = data.get("currentPrice")
    change = data.get("change")
    change_percent = data.get("changePercent")
    currency = data.get("currency", "")

    price_str = f"{current_price:,.2f} {currency}" if current_price is not None else "N/A"
    change_str = ""
    if change is not None and change_percent is not None:
        sign = "+" if change >= 0 else ""
        change_str = f" ({sign}{change:,.2f} / {sign}{change_percent:,.2f}%)"

    open_price = data.get('open')
    day_high = data.get('dayHigh')
    day_low = data.get('dayLow')
    volume = data.get('volume')

    message = f"*{short_name}*\n" \
              f"현재가: {price_str}{change_str}\n"
    
    if open_price is not None:
        message += f"시가: {open_price:,.2f} {currency}\n"
    if day_high is not None:
        message += f"고가: {day_high:,.2f} {currency}\n"
    if day_low is not None:
        message += f"저가: {day_low:,.2f} {currency}\n"
    if volume is not None:
        message += f"거래량: {volume:,}"
    
    return message.strip()
