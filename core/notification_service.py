import asyncio
import json
import logging
import os
import httpx
from typing import List, Dict, Any, Set
from fastapi import WebSocket

logger = logging.getLogger("notification_service")

class NotificationService:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {} # user_id -> Set of WebSockets
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected via WebSocket.")

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket.")

    async def notify_user(self, user_id: int, message: Dict[str, Any], send_telegram: bool = True):
        """특정 사용자에게 알림을 보냅니다 (WebSocket + Telegram)."""
        # 1. WebSocket 알림
        if user_id in self.active_connections:
            disconnected = set()
            for ws in list(self.active_connections[user_id]):
                try:
                    await ws.send_json({
                        "type": "notification",
                        "data": message
                    })
                except Exception:
                    disconnected.add(ws)
            
            for ws in disconnected:
                self.active_connections[user_id].remove(ws)

        # 2. Telegram 알림 (설정된 경우)
        if send_telegram and self.telegram_token and self.telegram_chat_id:
            asyncio.create_task(self._send_telegram(message))

    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결된 사용자에게 알림을 보냅니다."""
        for user_id in list(self.active_connections.keys()):
            # 브로드캐스트 시에는 텔레그램은 제외 (너무 많을 수 있음)
            if user_id in self.active_connections:
                for ws in list(self.active_connections[user_id]):
                    try:
                        await ws.send_json(message)
                    except Exception:
                        pass

    async def _send_telegram(self, message: Dict[str, Any]):
        """텔레그램 봇을 통해 메시지를 전송합니다."""
        title = message.get("title", "알림")
        body = message.get("body", "")
        formatted_msg = f"🔔 *{title}*\n\n{body}"
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": formatted_msg,
            "parse_mode": "Markdown"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

# 글로벌 인스턴스
notification_service = NotificationService()