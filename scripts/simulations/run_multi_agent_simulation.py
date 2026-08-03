"""
멀티 에이전트 AI 헤지펀드 자동매매 시뮬레이터 (매수 체결 시나리오 포함).
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
import logging
from typing import List, Dict
from core.indicator_service import IndicatorService
from core.sentiment_engine import SentimentEngine
from core.ai_service import AIService
from core.social_service import SocialService
from core.agents import MultiAgentOrchestrator

logging.basicConfig(level=logging.WARNING)

async def run_simulation(symbols: List[str] = None, total_cash: float = 50000.0, buy_threshold: float = 60.0):
    symbols = symbols or ["NVDA", "TSLA", "AAPL", "MSFT", "AMZN", "GOOGL"]
    
    print("\n" + "="*85)
    print(f"🚀 [Nasdaq is God] 멀티 에이전트 AI 헤지펀드 자동매매 시뮬레이션")
    print(f"💰 시작 자산: ${total_cash:,.2f} | 🎯 매수 판정 임계점: {buy_threshold}점 이상")
    print(f"📊 대상 종목: {', '.join(symbols)}")
    print("="*85 + "\n")

    indicator_service = IndicatorService()
    ai_service = AIService()
    social_service = SocialService()
    sentiment_engine = SentimentEngine(ai_service, social_service)
    orchestrator = MultiAgentOrchestrator(indicator_service, sentiment_engine)

    portfolio = {
        "cash": total_cash,
        "holdings": {},
        "orders": []
    }

    results = []

    for symbol in symbols:
        try:
            decision = await orchestrator.run_hedge_fund_pipeline(symbol=symbol, total_balance=portfolio["cash"])
            
            tech = decision.agent_signals.get("TECHNICAL")
            val = decision.agent_signals.get("VALUATION")
            sent = decision.agent_signals.get("SENTIMENT")
            guru = decision.agent_signals.get("GURU")
            risk = decision.risk_metrics

            current_price = tech.details.get("current_price", 0.0) if tech else 0.0

            # 임계값에 따른 커스텀 액션 판정
            action = decision.final_action
            if decision.confidence_score >= buy_threshold:
                action = "BUY"
            elif decision.confidence_score <= 40.0:
                action = "SELL"

            print(f"📌 [{symbol}] 이사회 통합 진단 리포트 (현재가: ${current_price:.2f})")
            print(f"  ├─ 📊 Technical Analyst : {tech.recommendation} ({tech.score:.1f}점) | RSI({tech.details.get('rsi', 0):.1f})")
            print(f"  ├─ 💎 Valuation Analyst : {val.recommendation} ({val.score:.1f}점) | PER({val.details.get('pe_ratio', 'N/A')})")
            print(f"  ├─ 💬 Sentiment Analyst : {sent.recommendation} ({sent.score:.1f}점) | 소셜/뉴스 AI 점수")
            print(f"  ├─ 🧙‍♂️ Gurus Ensemble   : {guru.recommendation} ({guru.score:.1f}점) | 버핏({guru.details.get('buffett_score', 0):.0f}점), 캐시우드({guru.details.get('wood_score', 0):.0f}점), 마이클버리({guru.details.get('burry_score', 0):.0f}점)")
            print(f"  ├─ 🛡️ Risk Manager      : 승인={risk.risk_approved}, 권장 최대 비중={risk.max_position_pct:.1f}%")
            print(f"  └─ 👑 Portfolio Manager : 최종 액션 [{action}], 확신점수={decision.confidence_score:.1f}점\n")

            # 수량 계산 및 매매 체결
            if action == "BUY":
                budget = portfolio["cash"] * 0.20 # 20% 배정
                qty = int(budget // current_price) if current_price > 0 else 0
                if qty > 0 and portfolio["cash"] >= (qty * current_price):
                    cost = qty * current_price
                    portfolio["cash"] -= cost
                    portfolio["holdings"][symbol] = portfolio["holdings"].get(symbol, 0) + qty
                    portfolio["orders"].append({
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": qty,
                        "price": current_price,
                        "cost": cost
                    })
                    print(f"  ✅ [주문 체결 성공] {symbol} {qty}주 BUY 체결! (체결가: ${current_price:.2f}, 주문금액: ${cost:,.2f}, 잔여예수금: ${portfolio['cash']:,.2f})")
                else:
                    print(f"  ⚠️ [매수 보류] {symbol} (예수금 부족 또는 수량 0주)")
            else:
                print(f"  ⏸️ [관망 (HOLD)] {symbol} 매수 확신점수 기준 미달 ({decision.confidence_score:.1f}점 < {buy_threshold}점)")

            print("-" * 85 + "\n")
            results.append((symbol, current_price))
        except Exception as e:
            print(f"❌ {symbol} 시뮬레이션 중 오류: {e}")

    # 최종 포트폴리오 산출
    total_asset = portfolio["cash"]
    print("="*85)
    print("📊 [멀티 에이전트 헤지펀드 최종 포트폴리오 성과]")
    print(f"  💵 잔여 예수금: ${portfolio['cash']:,.2f}")
    print("  📦 체결된 포트폴리오 보유 현황:")
    
    for sym, price in results:
        if sym in portfolio["holdings"]:
            qty = portfolio["holdings"][sym]
            val = qty * price
            total_asset += val
            print(f"     • {sym:5s}: {qty:4d}주 | 현재가 ${price:7.2f} | 평가금액 ${val:10,.2f}")

    print(f"\n  📈 총 평가 자산 (예수금 + 주식): ${total_asset:,.2f}")
    print(f"  🧾 시뮬레이션 총 주문 체결 수: {len(portfolio['orders'])}건")
    print("="*85 + "\n")

if __name__ == "__main__":
    asyncio.run(run_simulation())
