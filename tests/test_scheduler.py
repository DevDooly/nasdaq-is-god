"""
배치 수집 스케줄러 유닛 테스트 모듈.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from core.scheduler import BatchCollectorScheduler

@pytest.mark.asyncio
async def test_batch_scheduler_init_and_start():
    scheduler = BatchCollectorScheduler(target_symbols=["AAPL", "NVDA"])
    assert scheduler.target_symbols == ["AAPL", "NVDA"]
    assert scheduler.scheduler.running is False

    scheduler.start()
    assert scheduler.scheduler.running is True

    # 3개 인터벌 태스크 등록 확인
    jobs = scheduler.scheduler.get_jobs()
    job_ids = [j.id for j in jobs]
    assert "fetch_news_batch" in job_ids
    assert "fetch_guru_insights_batch" in job_ids
    assert "analyze_pending_sentiments_batch" in job_ids

    scheduler.stop()
    await asyncio.sleep(0.1)
    assert scheduler.scheduler.running is False

@pytest.mark.asyncio
async def test_fetch_news_batch():
    scheduler = BatchCollectorScheduler(target_symbols=["AAPL"])
    
    with patch("core.scheduler.news_scraper.run_batch_scrape", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = 2
        
        await scheduler.fetch_news_batch()
        mock_scrape.assert_called()
