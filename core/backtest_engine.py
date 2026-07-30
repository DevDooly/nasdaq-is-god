import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.indicator_service import IndicatorService

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0, commission_rate: float = 0.001, slippage_rate: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate

    def fetch_data(self, symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """yfinance로부터 과거 주가 데이터 수집"""
        ticker = yf.Ticker(symbol)
        if start_date and end_date:
            df = ticker.history(start=start_date, end=end_date, interval=interval)
        else:
            df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            raise ValueError(f"No data available for symbol: {symbol}")
        return df

    def generate_signals(self, df: pd.DataFrame, strategy_type: str, params: Dict[str, Any]) -> pd.Series:
        """
        전략 종류와 파라미터에 따라 매수(1), 매도(-1), 관망(0) 시그널 생성
        """
        signals = pd.Series(0, index=df.index)
        close = df['Close']

        if strategy_type == "SMA_CROSSOVER":
            fast_p = int(params.get("fast_period", 20))
            slow_p = int(params.get("slow_period", 50))
            
            fast_sma = close.rolling(window=fast_p).mean()
            slow_sma = close.rolling(window=slow_p).mean()
            
            # fast > slow -> 1, fast < slow -> -1
            condition = (fast_sma > slow_sma).astype(int)
            # 골든크로스 / 데드크로스 변화 시점에 매수/매도 시그널
            signals = condition.diff().fillna(0)
            signals = signals.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

        elif strategy_type == "RSI_REVERSAL":
            rsi_period = int(params.get("rsi_period", 14))
            buy_rsi = float(params.get("buy_rsi", 30))
            sell_rsi = float(params.get("sell_rsi", 70))
            
            rsi = IndicatorService.calculate_rsi(close, period=rsi_period)
            
            # RSI 과매도 탈출(상승) 시 매수, 과매수 탈출(하강) 시 매도
            for i in range(1, len(df)):
                if rsi.iloc[i-1] <= buy_rsi and rsi.iloc[i] > buy_rsi:
                    signals.iloc[i] = 1
                elif rsi.iloc[i-1] >= sell_rsi and rsi.iloc[i] < sell_rsi:
                    signals.iloc[i] = -1

        elif strategy_type == "MACD_CROSSOVER":
            fast_p = int(params.get("fast_period", 12))
            slow_p = int(params.get("slow_period", 26))
            signal_p = int(params.get("signal_period", 9))
            
            macd_dict = IndicatorService.calculate_macd(close, fast=fast_p, slow=slow_p, signal=signal_p)
            macd_line = macd_dict["macd"]
            signal_line = macd_dict["signal"]
            
            condition = (macd_line > signal_line).astype(int)
            signals = condition.diff().fillna(0)
            signals = signals.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

        elif strategy_type == "BOLLINGER_BANDS":
            period = int(params.get("period", 20))
            std_dev = float(params.get("std_dev", 2.0))
            
            bb_dict = IndicatorService.calculate_bollinger_bands(close, period=period, std_dev=int(std_dev))
            lower_band = bb_dict["lower"]
            upper_band = bb_dict["upper"]
            
            for i in range(1, len(df)):
                if close.iloc[i-1] <= lower_band.iloc[i-1] and close.iloc[i] > lower_band.iloc[i]:
                    signals.iloc[i] = 1
                elif close.iloc[i-1] >= upper_band.iloc[i-1] and close.iloc[i] < upper_band.iloc[i]:
                    signals.iloc[i] = -1

        elif strategy_type == "DUAL_MOMENTUM":
            lookback = int(params.get("lookback_period", 20))
            momentum = close.pct_change(periods=lookback)
            
            for i in range(1, len(df)):
                if momentum.iloc[i-1] <= 0 and momentum.iloc[i] > 0:
                    signals.iloc[i] = 1
                elif momentum.iloc[i-1] > 0 and momentum.iloc[i] <= 0:
                    signals.iloc[i] = -1

        elif strategy_type.startswith("HYBRID"):
            tech_weight = float(params.get("tech_weight", 0.6))
            sent_weight = 1.0 - tech_weight
            buy_threshold = float(params.get("buy_threshold", 65.0))
            sell_threshold = float(params.get("sell_threshold", 40.0))
            sent_score = float(params.get("sentiment_score", 65.0))

            rsi = IndicatorService.calculate_rsi(close, period=14)
            macd_dict = IndicatorService.calculate_macd(close)
            bb_dict = IndicatorService.calculate_bollinger_bands(close)

            hybrid_scores = pd.Series(50.0, index=df.index)

            for i in range(len(df)):
                r_val = float(rsi.iloc[i]) if not np.isnan(rsi.iloc[i]) else 50.0
                r_score = max(0.0, min(100.0, 100.0 - r_val))

                h_val = float(macd_dict["histogram"].iloc[i]) if not np.isnan(macd_dict["histogram"].iloc[i]) else 0.0
                m_score = max(0.0, min(100.0, 50.0 + (h_val * 10)))

                lower_b = float(bb_dict["lower"].iloc[i]) if not np.isnan(bb_dict["lower"].iloc[i]) else None
                upper_b = float(bb_dict["upper"].iloc[i]) if not np.isnan(bb_dict["upper"].iloc[i]) else None
                c_val = float(close.iloc[i])

                if lower_b is not None and upper_b is not None and upper_b > lower_b:
                    percent_b = (c_val - lower_b) / (upper_b - lower_b) * 100.0
                    b_score = max(0.0, min(100.0, 100.0 - percent_b))
                else:
                    b_score = 50.0

                if strategy_type == "HYBRID_RSI":
                    t_score = r_score
                elif strategy_type == "HYBRID_MACD":
                    t_score = m_score
                elif strategy_type == "HYBRID_BOLLINGER":
                    t_score = b_score
                else:
                    t_score = (r_score + m_score + b_score) / 3.0

                h_score = (t_score * tech_weight) + (sent_score * sent_weight)
                hybrid_scores.iloc[i] = h_score

            for i in range(1, len(df)):
                if hybrid_scores.iloc[i-1] < buy_threshold and hybrid_scores.iloc[i] >= buy_threshold:
                    signals.iloc[i] = 1
                elif hybrid_scores.iloc[i-1] > sell_threshold and hybrid_scores.iloc[i] <= sell_threshold:
                    signals.iloc[i] = -1

        return signals

    def run_backtest(self, symbol: str, strategy_type: str, params: Dict[str, Any], start_date: Optional[str] = None, end_date: Optional[str] = None, period: str = "1y") -> Dict[str, Any]:
        """
        백테스트 시뮬레이션 수행 및 결과 지표 산출
        """
        df = self.fetch_data(symbol, start_date=start_date, end_date=end_date, period=period)
        signals = self.generate_signals(df, strategy_type, params)
        
        cash = float(self.initial_capital)
        position = 0.0 # 보유 주식 수
        entry_price = 0.0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []
        
        # 벤치마크 (Buy & Hold)
        first_price = float(df['Close'].iloc[0])
        benchmark_shares = (self.initial_capital * (1 - self.commission_rate)) / first_price
        
        peak_equity = float(self.initial_capital)
        max_drawdown = 0.0
        
        for i in range(len(df)):
            date_str = df.index[i].strftime("%Y-%m-%d")
            price = float(df['Close'].iloc[i])
            sig = signals.iloc[i]
            
            # 매수 시그널
            if sig == 1 and position == 0:
                buy_price = float(price * (1 + self.slippage_rate))
                cost = float(cash * (1 - self.commission_rate))
                position = float(cost / buy_price)
                cash = 0.0
                entry_price = buy_price
                trades.append({
                    "type": "BUY",
                    "date": date_str,
                    "price": round(float(buy_price), 2),
                    "shares": round(float(position), 4)
                })
            
            # 매도 시그널
            elif sig == -1 and position > 0:
                sell_price = float(price * (1 - self.slippage_rate))
                proceeds = float((position * sell_price) * (1 - self.commission_rate))
                pnl = float(proceeds - (position * entry_price))
                pnl_percent = float((sell_price - entry_price) / entry_price * 100.0)
                
                trades.append({
                    "type": "SELL",
                    "date": date_str,
                    "price": round(float(sell_price), 2),
                    "shares": round(float(position), 4),
                    "pnl": round(float(pnl), 2),
                    "pnl_percent": round(float(pnl_percent), 2)
                })
                
                cash = proceeds
                position = 0.0
                entry_price = 0.0
            
            # 일별 자산 가치 계산
            total_equity = float(cash + (position * price))
            benchmark_equity = float(benchmark_shares * price)
            
            # MDD 계산
            if total_equity > peak_equity:
                peak_equity = total_equity
            drawdown = float((total_equity - peak_equity) / peak_equity * 100.0)
            if drawdown < max_drawdown:
                max_drawdown = drawdown
                
            equity_curve.append({
                "date": date_str,
                "portfolio_value": round(float(total_equity), 2),
                "benchmark_value": round(float(benchmark_equity), 2),
                "drawdown": round(float(drawdown), 2),
                "signal": int(sig)
            })

        final_portfolio_value = cash + (position * df['Close'].iloc[-1])
        total_return = (final_portfolio_value - self.initial_capital) / self.initial_capital * 100.0
        
        benchmark_final_value = benchmark_shares * df['Close'].iloc[-1]
        benchmark_return = (benchmark_final_value - self.initial_capital) / self.initial_capital * 100.0
        
        # 완료된 매매 거래(매수+매도 세트) 통계
        closed_trades = [t for t in trades if t["type"] == "SELL"]
        win_trades = [t for t in closed_trades if t.get("pnl", 0) > 0]
        loss_trades = [t for t in closed_trades if t.get("pnl", 0) <= 0]
        
        win_rate = (len(win_trades) / len(closed_trades) * 100.0) if closed_trades else 0.0
        
        gross_profit = sum(t["pnl"] for t in win_trades)
        gross_loss = abs(sum(t["pnl"] for t in loss_trades))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
        
        # CAGR (연평균 성장률)
        trading_days = len(df)
        years = trading_days / 252.0 if trading_days > 0 else 1.0
        cagr = (((final_portfolio_value / self.initial_capital) ** (1 / years)) - 1) * 100.0 if (years > 0 and final_portfolio_value > 0) else 0.0
        
        # Sharpe Ratio (일별 수익률 기반)
        daily_returns = pd.Series([e["portfolio_value"] for e in equity_curve]).pct_change().dropna()
        risk_free_daily_rate = 0.02 / 252.0 # 2% 연이율 가정
        excess_returns = daily_returns - risk_free_daily_rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0.0

        return {
            "symbol": symbol,
            "strategy_type": strategy_type,
            "parameters": params,
            "initial_capital": self.initial_capital,
            "final_portfolio_value": round(final_portfolio_value, 2),
            "total_return": round(total_return, 2),
            "cagr": round(cagr, 2),
            "benchmark_return": round(benchmark_return, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "total_trades_count": len(closed_trades),
            "trades": trades,
            "equity_curve": equity_curve
        }
