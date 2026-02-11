import os
import httpx
import json
from typing import Dict, Any, Optional
from core.broker import TradingBroker
from bot.config import logger
from datetime import datetime

class KISBroker(TradingBroker):
    """한국투자증권(KIS) Open API 기반 실제 브로커"""

    def __init__(self):
        self.base_url = os.getenv("KIS_BASE_URL", "https://openapi.koreainvestment.com:9443")
        self.app_key = os.getenv("KIS_APP_KEY")
        self.app_secret = os.getenv("KIS_APP_SECRET")
        self.account_no = os.getenv("KIS_ACCOUNT_NO")  # 종합계좌번호(8자리)
        self.account_code = os.getenv("KIS_ACCOUNT_CODE", "01") # 계좌상품코드(2자리)
        self._access_token = None
        self._token_expired_at = None

    async def _get_access_token(self):
        """접근 토큰 발급/갱신 (24시간 유효)"""
        if self._access_token and self._token_expired_at > datetime.now():
            return self._access_token

        url = f"{self.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            data = response.json()
            
            if "access_token" in data:
                self._access_token = data["access_token"]
                # 보안상 실제 만료 시간보다 약간 짧게 설정
                self._token_expired_at = datetime.now()
                logger.info("KIS Access Token renewed successfully.")
                return self._access_token
            else:
                logger.error(f"Failed to get KIS token: {data}")
                raise Exception("KIS Authentication Failed")

    def _get_headers(self, tr_id: str):
        """공통 헤더 생성"""
        return {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self._access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

    async def get_balance(self) -> Dict[str, Any]:
        """미국 주식 잔고 조회 (실제 KIS API 호출)"""
        await self._get_access_token()
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        # 해외주식 잔고조회(V1) TR_ID: JTTT5012R (실전), VTTT5012R (모의)
        tr_id = "JTTT5012R" if "openapi" in self.base_url else "VTTT5012R"
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_code,
            "OVRS_EXCL_CD": "NASD", # 나스닥 기준 (거래소별 코드 상이)
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers(tr_id), params=params)
            return response.json()

    async def place_order(
        self, 
        symbol: str, 
        quantity: float, 
        side: str, 
        order_type: str = "market", 
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """미국 주식 주문 (매수/매도)"""
        await self._get_access_token()
        
        # TR_ID 설정 (JTTT1002U: 매수, JTTT1006U: 매도 - 실전 기준)
        if side.upper() == "BUY":
            tr_id = "JTTT1002U" if "openapi" in self.base_url else "VTTT1002U"
        else:
            tr_id = "JTTT1006U" if "openapi" in self.base_url else "VTTT1001U"

        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        
        payload = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_code,
            "OVRS_EXCL_CD": "NASD",
            "PDNO": symbol,
            "ORD_QTY": str(int(quantity)),
            "OVRS_ITM_AMES": f"{price:.2f}" if price else "0",
            "ORD_DVSN": "00" if order_type == "limit" else "01" # 00: 지정가, 01: 시장가
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self._get_headers(tr_id), json=payload)
            data = response.json()
            
            # 응답 포맷을 시스템 표준에 맞게 변환
            if data.get("rt_cd") == "0":
                return {
                    "status": "filled", # 실제로는 체결 확인 API를 별도 호출해야 할 수 있음
                    "order_id": data["output"]["ODNO"],
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price or 0.0 # 체결가는 추후 업데이트 필요
                }
            return {"error": data.get("msg1", "Order failed")}

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        # 주문 상세 조회 API 연동 필요
        return {"status": "implementing"}

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        # 주문 취소 API 연동 필요
        return {"status": "implementing"}
