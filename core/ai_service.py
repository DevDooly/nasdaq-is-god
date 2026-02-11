import os
import google.generativeai as genai
import json
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger("ai_service")

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("GEMINI_API_KEY not set. AI features will be disabled.")
        
        self._market_cache = None
        self._market_cache_time = 0
        self.CACHE_DURATION = 1800 

    def list_available_models(self) -> List[Dict[str, str]]:
        """사용 가능한 Gemini 모델 리스트 반환"""
        if not self.api_key: return []
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append({"name": m.name, "display_name": m.display_name})
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return [{"name": "models/gemini-2.0-flash", "display_name": "Gemini 2.0 Flash (Default)"}]

    async def analyze_sentiment(self, symbol: str, news_list: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        """개별 종목 뉴스 분석"""
        return await self._generate_analysis(f"주식 종목 '{symbol}'", news_list, model_name)

    async def analyze_market_outlook(self, news_list: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        """전체 시장 뉴스 분석"""
        # 시장 분석은 캐싱 사용 (캐시는 기본 모델 기준)
        current_time = time.time()
        if self._market_cache and (current_time - self._market_cache_time < self.CACHE_DURATION):
            return self._market_cache

        result = await self._generate_analysis("미국 주식 시장 전체(Nasdaq/S&P500)", news_list, model_name)
        if "error" not in result:
            self._market_cache = result
            self._market_cache_time = current_time
        return result

    async def _generate_analysis(self, target_name: str, news_list: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "AI API Key not configured"}
        
        if not news_list:
            return {"score": 50, "summary": "분석할 뉴스가 부족합니다.", "sentiment": "Neutral", "sources": []}

        titles = [news.get('title', '') for news in news_list]
        news_text = "\n".join([f"- {t}" for t in titles[:10] if t])

        prompt = f"""
        당신은 월스트리트의 시니어 퀀트 애널리스트입니다.
        아래는 {target_name}에 관련된 최신 뉴스 헤드라인입니다.
        
        이 뉴스들을 종합 분석하여 '투자 심리(Sentiment)'를 평가해주세요.
        
        [분석 요청 사항]
        1. 점수 (0~100): 0(극도의 공포) ~ 50(중립) ~ 100(극도의 탐욕)
        2. 상태: "Bullish"(낙관), "Bearish"(비관), "Neutral"(중립)
        3. 요약: 현재 상황을 1~2문장으로 명확하게 요약 (한국어)
        4. 이유: 점수 산정 이유 (한국어)

        [뉴스 제목들]
        {news_text}

        반드시 아래 JSON 형식으로만 응답하세요:
        {{
            "score": 숫자,
            "sentiment": "문자열",
            "summary": "문자열",
            "reason": "문자열"
        }}
        """

        try:
            import asyncio
            model = genai.GenerativeModel(model_name)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
            
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            # 사용된 소스 뉴스 제목들도 함께 반환
            result["sources"] = titles[:10]
            return result
        except Exception as e:
            logger.error(f"Gemini Error ({model_name}): {e}")
            return {"error": f"AI Analysis Failed: {str(e)}"}
