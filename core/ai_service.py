import os
import google.generativeai as genai
import json
import logging
import time
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ai_service")

class AIService:
    def __init__(self):
        self.default_api_key = os.getenv("GEMINI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "GOOGLE").upper()

        if self.default_api_key and self.default_api_key != "your_gemini_api_key_here":
            genai.configure(api_key=self.default_api_key)
        
        self._market_cache = None
        self._market_cache_time = 0
        self.CACHE_DURATION = 1800 

    def list_available_models(self, api_key: Optional[str] = None) -> List[Dict[str, str]]:
        # 생략 (기존 로직 유지하되 필요 시 확장)
        return [{"name": "models/gemini-2.0-flash", "display_name": "Gemini 2.0 Flash"},
                {"name": "llama3", "display_name": "Ollama: Llama3"}]

    async def analyze_sentiment_with_rotation(self, symbol: str, news_list: List[Dict[str, Any]], api_configs: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        """
        활성화된 AI 설정을 바탕으로 분석을 수행합니다. (멀티 프로바이더 지원)
        """
        # 1. 활성 설정 찾기
        active_config = next((c for c in api_configs if c['is_active']), None)
        if not active_config:
            # 활성 설정 없으면 ENV의 설정 사용
            if self.default_provider == "OLLAMA" and self.ollama_base_url:
                active_config = {"provider": "OLLAMA", "base_url": self.ollama_base_url, "id": None, "label": "Default ENV (Ollama)"}
            elif self.default_api_key:
                active_config = {"provider": "GOOGLE", "key_value": self.default_api_key, "id": None, "label": "Default ENV (Google)"}
            else:
                return {"error": "No Active AI Config and no ENV defaults found."}

        provider = active_config.get("provider", "GOOGLE").upper()
        prompt = self._build_sentiment_prompt(f"주식 종목 '{symbol}'", news_list)

        # 2. 프로바이더별 드라이버 호출
        try:
            if provider == "OLLAMA":
                result = await self._call_ollama(active_config["base_url"], model_name, prompt)
            elif provider == "GOOGLE":
                result = await self._call_google(active_config["key_value"], model_name, prompt)
            elif provider == "OPENAI":
                result = await self._call_openai(active_config["key_value"], model_name, prompt)
            else:
                return {"error": f"Unsupported provider: {provider}"}
            
            if "error" not in result:
                result["used_key_id"] = active_config.get("id")
                result["sources"] = [n.get('title') for n in news_list[:10] if n.get('title')]
            return result
        except Exception as e:
            return {"error": str(e)}

    def _build_sentiment_prompt(self, target: str, news_list: List[Dict[str, Any]]) -> str:
        titles = [n.get('title', '') for n in news_list[:10]]
        news_text = "\n".join([f"- {t}" for t in titles if t])
        return f"""
        당신은 시니어 퀀트 애널리스트입니다. {target} 최신 뉴스 분석:
        {news_text}
        반드시 다음 형식의 JSON으로만 응답하십시오:
        {{ "score": 0~100, "sentiment": "Bullish|Bearish|Neutral", "summary": "한국어 요약", "reason": "한국어 이유" }}
        """

    async def _call_ollama(self, base_url: str, model: str, prompt: str) -> Dict[str, Any]:
        """Ollama API 호출 (로컬/원격)"""
        if not base_url: return {"error": "Ollama base_url is missing"}
        # http:// 추가 체크
        if not base_url.startswith("http"): base_url = f"http://{base_url}"
        
        # 모델명 보정 (Gemini 기본값이 넘어올 경우 llama3로 대체)
        ollama_model = "llama3" if "gemini" in model else model
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                if response.status_code != 200:
                    return {"error": f"Ollama Error: {response.text}"}
                
                res_data = response.json()
                return json.loads(res_data["response"])
            except Exception as e:
                return {"error": f"Ollama Connection Failed: {str(e)}"}

    async def _call_google(self, api_key: str, model_name: str, prompt: str) -> Dict[str, Any]:
        """기존 Gemini 호출 로직"""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        # run_in_executor로 동기 함수 호출
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text: text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)

    async def _call_openai(self, api_key: str, model: str, prompt: str) -> Dict[str, Any]:
        # OpenAI SDK 연동 (생략 - 향후 필요 시 추가)
        return {"error": "OpenAI driver not implemented yet"}

    async def analyze_social_impact(self, guru_name: str, content: str, target_symbols: str = "", model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        """영향력 있는 인물의 발언을 분석합니다. (ENV 기본 설정 사용)"""
        prompt = f"""
        당신은 월스트리트의 시니어 퀀트 애널리스트입니다. 
        시장 영향력이 큰 인물 '{guru_name}'의 최근 발언을 분석하여 주식 시장에 미칠 파급력을 평가하십시오.
        [발언 원문]: "{content}"
        형식 JSON: {{ "score": 0~100, "sentiment": "Bullish|Bearish|Neutral", "summary": "요약", "reason": "이유", "main_symbol": "티커" }}
        """
        
        try:
            if self.default_provider == "OLLAMA" and self.ollama_base_url:
                return await self._call_ollama(self.ollama_base_url, model_name, prompt)
            return await self._call_google(self.default_api_key, model_name, prompt)
        except Exception as e:
            logger.error(f"Social analysis error: {e}")
            return {"score": 50, "sentiment": "Neutral", "summary": "분석 오류", "reason": str(e)}

    async def analyze_market_outlook(self, news_list: List[Dict[str, Any]], model_name: str = "models/gemini-2.0-flash") -> Dict[str, Any]:
        current_time = time.time()
        if self._market_cache and (current_time - self._market_cache_time < self.CACHE_DURATION):
            return self._market_cache
        
        prompt = self._build_sentiment_prompt("미국 주식 시장 전체", news_list)
        
        try:
            if self.default_provider == "OLLAMA" and self.ollama_base_url:
                result = await self._call_ollama(self.ollama_base_url, model_name, prompt)
            else:
                result = await self._call_google(self.default_api_key, model_name, prompt)
            
            if "error" not in result:
                self._market_cache = result
                self._market_cache_time = current_time
            return result
        except Exception as e:
            return {"error": str(e)}

    async def check_provider_health(self, provider: str, base_url: Optional[str] = None, api_key: Optional[str] = None) -> bool:
        """AI 프로바이더의 연결 상태를 확인합니다."""
        try:
            if provider.upper() == "OLLAMA":
                if not base_url: return False
                if not base_url.startswith("http"): base_url = f"http://{base_url}"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{base_url}/")
                    return response.status_code == 200
            elif provider.upper() == "GOOGLE":
                # 단순 라이브러리 설정 체크
                return api_key is not None and len(api_key) > 10
            # OpenAI 등 타 프로바이더 확장 가능
            return True
        except Exception as e:
            logger.error(f"Health check failed for {provider}: {e}")
            return False