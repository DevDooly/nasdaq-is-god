import os
import google.generativeai as genai
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("ai_service")

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("GEMINI_API_KEY not set or default. AI features will be limited.")

    async def analyze_sentiment(self, symbol: str, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """뉴스 제목들을 분석하여 종합적인 투자 심리 점수(0~100)를 도출합니다."""
        if not self.model:
            return {"error": "AI Service not configured (GEMINI_API_KEY missing)"}
        
        if not news_list:
            return {
                "score": 50, 
                "summary": "최근 뉴스가 없습니다.", 
                "sentiment": "Neutral",
                "reason": "분석할 데이터가 부족합니다."
            }

        titles = [news.get('title', '') for news in news_list]
        news_text = "\n".join([f"- {t}" for t in titles if t])

        prompt = f"""
        당신은 시니어 퀀트 애널리스트입니다. 다음은 주식 종목 '{symbol}'에 대한 최신 뉴스 제목들입니다.
        이 뉴스들을 종합적으로 분석하여 투자 심리 점수(0~100)와 한 줄 요약을 제공해주세요.
        0점은 극도의 공포/매도, 100점은 극도의 탐욕/매수, 50점은 중립을 의미합니다.

        뉴스 제목들:
        {news_text}

        반드시 아래 JSON 형식으로만 답변하세요:
        {{
            "score": 점수(숫자),
            "sentiment": "Bullish" | "Bearish" | "Neutral",
            "summary": "한 줄 요약 (한국어)",
            "reason": "점수 산정 이유 (한국어)"
        }}
        """

        try:
            # 동기 함수를 비동기 루프에서 실행 (Gemini SDK는 동기 호출)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: self.model.generate_content(prompt))
            
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            logger.error(f"Gemini Analysis Error: {e}")
            return {"error": "Failed to analyze sentiment"}