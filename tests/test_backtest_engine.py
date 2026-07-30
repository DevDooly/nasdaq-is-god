import pytest
import pandas as pd
import numpy as np
from core.backtest_engine import BacktestEngine

@pytest.fixture
def sample_df():
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    # 상승 후 하락하는 가상의 주가 패턴 생성
    prices = 100.0 + np.sin(np.linspace(0, 3 * np.pi, 100)) * 20.0 + np.linspace(0, 10, 100)
    df = pd.DataFrame({
        "Open": prices - 0.5,
        "High": prices + 1.0,
        "Low": prices - 1.0,
        "Close": prices,
        "Volume": 10000
    }, index=dates)
    return df

def test_sma_crossover_signals(sample_df):
    engine = BacktestEngine()
    signals = engine.generate_signals(sample_df, "SMA_CROSSOVER", {"fast_period": 5, "slow_period": 20})
    assert len(signals) == len(sample_df)
    assert set(signals.unique()).issubset({-1, 0, 1})

def test_rsi_reversal_signals(sample_df):
    engine = BacktestEngine()
    signals = engine.generate_signals(sample_df, "RSI_REVERSAL", {"rsi_period": 14, "buy_rsi": 30, "sell_rsi": 70})
    assert len(signals) == len(sample_df)

def test_macd_crossover_signals(sample_df):
    engine = BacktestEngine()
    signals = engine.generate_signals(sample_df, "MACD_CROSSOVER", {"fast_period": 12, "slow_period": 26, "signal_period": 9})
    assert len(signals) == len(sample_df)

def test_bollinger_bands_signals(sample_df):
    engine = BacktestEngine()
    signals = engine.generate_signals(sample_df, "BOLLINGER_BANDS", {"period": 20, "std_dev": 2.0})
    assert len(signals) == len(sample_df)

def test_dual_momentum_signals(sample_df):
    engine = BacktestEngine()
    signals = engine.generate_signals(sample_df, "DUAL_MOMENTUM", {"lookback_period": 10})
    assert len(signals) == len(sample_df)

from unittest.mock import patch

def test_run_backtest_with_mock_data(sample_df):
    engine = BacktestEngine()
    with patch.object(engine, 'fetch_data', return_value=sample_df):
        result = engine.run_backtest(
            symbol="AAPL",
            strategy_type="SMA_CROSSOVER",
            params={"fast_period": 5, "slow_period": 20},
            period="1y"
        )
        
        assert result["symbol"] == "AAPL"
        assert "total_return" in result
        assert "cagr" in result
        assert "max_drawdown" in result
        assert "sharpe_ratio" in result
        assert "equity_curve" in result
        assert len(result["equity_curve"]) == len(sample_df)
