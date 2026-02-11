import pandas as pd
import numpy as np
from typing import Dict, Any, List
from core.stock_service import get_stock_info

class IndicatorService:
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """RSI (Relative Strength Index) 계산"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence) 계산"""
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return {
            "macd": macd,
            "signal": signal_line,
            "histogram": histogram
        }

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """볼린저 밴드 계산"""
        sma = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            "upper": upper_band,
            "middle": sma,
            "lower": lower_band
        }

    async def get_indicators(self, symbol: str, interval: str = "1d", period: str = "1mo") -> Dict[str, Any]:
        """특정 종목의 기술적 지표들을 계산하여 반환"""
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return {"error": "No data found"}

        close = df['Close']
        
        # 지표 계산
        rsi = self.calculate_rsi(close)
        macd_data = self.calculate_macd(close)
        bb_data = self.calculate_bollinger_bands(close)
        
        # 최신 값 추출
        latest_idx = -1
        return {
            "symbol": symbol,
            "price": float(close.iloc[latest_idx]),
            "rsi": float(rsi.iloc[latest_idx]) if not np.isnan(rsi.iloc[latest_idx]) else None,
            "macd": {
                "val": float(macd_data["macd"].iloc[latest_idx]),
                "signal": float(macd_data["signal"].iloc[latest_idx]),
                "hist": float(macd_data["histogram"].iloc[latest_idx])
            },
            "bollinger": {
                "upper": float(bb_data["upper"].iloc[latest_idx]),
                "middle": float(bb_data["middle"].iloc[latest_idx]),
                "lower": float(bb_data["lower"].iloc[latest_idx])
            },
            "timestamp": df.index[latest_idx].isoformat()
        }
