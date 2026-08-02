"""
모니터링 대상 관리 API 엔드포인트 유닛 테스트 모듈.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from main_api import app, batch_collector_scheduler


@pytest.mark.asyncio
async def test_get_monitoring_targets_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/monitoring/targets")
        assert response.status_code == 200
        data = response.json()
        assert "symbols" in data
        assert "gurus" in data
        assert "batch_running" in data


@pytest.mark.asyncio
async def test_manage_symbol_target_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. ADD
        response_add = await client.post("/monitoring/targets/symbols", json={"symbol": "TESTSYM", "action": "ADD"})
        assert response_add.status_code == 200
        assert "TESTSYM" in batch_collector_scheduler.target_symbols

        # 2. REMOVE
        response_rem = await client.post("/monitoring/targets/symbols", json={"symbol": "TESTSYM", "action": "REMOVE"})
        assert response_rem.status_code == 200
        assert "TESTSYM" not in batch_collector_scheduler.target_symbols
