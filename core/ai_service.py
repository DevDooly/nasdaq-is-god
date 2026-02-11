import os
import google.generativeai as genai
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ai_service")

class AIService:
    def __init__(self):
        self.default_api_key = os.getenv("GEMINI_API_KEY")
        if self.default_api_key and self.default_api_key != "your_gemini_api_key_here":
            genai.configure(api_key=self.default_api_key)
        
        self._market_cache = None
        self._market_cache_time = 0
        self.CACHE_DURATION = 1800 

    def list_available_models(self, api_key: Optional[str] = None) -> List[Dict[str, str]]:
        """사용 가능한 Gemini 모델 리스트 반환"""
        key = api_key or self.default_api_key
        if not key: return []
        try:
            if api_key: genai.configure(api_key=api_key)
            models = [{"name": m.name, "display_name": m.display_name} for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return models
        except Exception:
            return [{"name": "models/gemini-2.0-flash", "display_name": "Gemini 2.0 Flash (Stable)"}]
        finally:
            if self.default_api_key: genai.configure(api_key=self.default_api_key)

    async def analyze_sentiment_with_rotation(self, symbol: str, news_list: List[Dict[str, Any]], api_configs: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        """
        [핵심] 여러 개의 키를 순차적으로 시도하며 분석을 수행합니다.
        """
        if not api_configs and not self.default_api_key:
            return {"error": "No API Keys available."}

        # 1. 시도할 키 목록 정리 (활성 키 우선, 그 다음 나머지)
        keys_to_try = []
        if api_configs:
            # 활성 키를 가장 앞으로, 나머지는 마지막 사용 시간이 오래된 순서대로
            sorted_configs = sorted(api_configs, key=lambda x: (not x['is_active'], x.get('last_used_at') or datetime.min))
            keys_to_try = [c for c in sorted_configs]
        else:
            # 등록된 키가 없으면 환경변수 기본 키 사용
            keys_to_try = [{"key_value": self.default_api_key, "label": "Default ENV Key", "id": None}]

        last_error = ""
        for config in keys_to_try:
            current_key = config['key_value']
            logger.info(f"🔄 Attempting AI analysis with key: {config['label']}")
            
            result = await self._generate_analysis(f"주식 종목 '{symbol}'", news_list, model_name, current_key)
            
            if "error" not in result:
                # 성공 시 어떤 키가 성공했는지 ID 포함하여 반환
                result["used_key_id"] = config.get("id")
                return result
            
            # 쿼터 초과 에러인 경우에만 다음 키로 넘어감
            if "Quota Exceeded" in result["error"] or "429" in result["error"]:
                logger.warning(f"⚠️ Key '{config['label']}' limit reached. Trying next key...")
                last_error = result["error"]
                continue
            else:
                # 다른 치명적 에러면 즉시 중단
                return result

        return {"error": f"All API keys exhausted. Last error: {last_error}"}

    async def analyze_market_outlook(self, news_list: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        current_time = time.time()
        if self._market_cache and (current_time - self._market_cache_time < self.CACHE_DURATION):
            return self._market_cache

        result = await self._generate_analysis("미국 주식 시장 전체(Nasdaq/S&P500)", news_list, model_name, self.default_api_key)
        if "error" not in result:
            self._market_cache = result
            self._market_cache_time = current_time
        return result

    async def _generate_analysis(self, target_name: str, news_list: List[Dict[str, Any]], model_name: str, api_key: str) -> Dict[str, Any]:
        if not api_key: return {"error": "API Key is empty"}
        if not news_list: return {"score": 50, "summary": "뉴스가 없습니다.", "sentiment": "Neutral", "reason": "No news", "sources": []}

        titles = [news.get('title', '') for news in news_list]
        news_text = "\n".join([f"- {t}" for t in titles[:10] if t])
        prompt = f"""
        당신은 시니어 퀀트 애널리스트입니다. {target_name} 최신 뉴스 분석:
        {news_text}
        반드시 JSON: {{ "score": 0~100, "sentiment": "Bullish|Bearish|Neutral", "summary": "한국어 요약", "reason": "한국어 이유" }}
        """

        try:
            import asyncio
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
            
            text = response.text.strip()
            if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            result["sources"] = titles[:10]
            return result
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg: return {"error": "AI Quota Exceeded."}
            return {"error": error_msg}