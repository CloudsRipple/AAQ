from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable

from ..ai import LowAnalysis, analyze_low_lane_async
from ..llm_gateway import UnifiedLLMGateway
from .bus import AsyncEventBus

logger = logging.getLogger(__name__)

# 全局内存缓存
LOW_ANALYSIS_CACHE: dict[str, LowAnalysis] = {}

def get_cached_low_analysis(symbol: str) -> LowAnalysis | None:
    return LOW_ANALYSIS_CACHE.get(symbol.upper()) or LOW_ANALYSIS_CACHE.get("MACRO")

class LowEngine:
    """
    后台运行的低频分析引擎，定期或基于宏观事件更新低频分析缓存。
    """
    def __init__(
        self,
        event_bus: AsyncEventBus,
        market_snapshot_provider: Callable[[], dict[str, dict[str, float | str]]],
        committee_models: list[str],
        committee_min_support: int,
        strategy_name: str = "macro_rotation",
        strategy_confidence: float = 0.8,
        interval_seconds: float = 3600.0,
        llm_gateway: UnifiedLLMGateway | None = None,
        headlines_provider: Callable[[], list[str]] | None = None,
    ):
        self.event_bus = event_bus
        self.market_snapshot_provider = market_snapshot_provider
        self.committee_models = committee_models
        self.committee_min_support = committee_min_support
        self.strategy_name = strategy_name
        self.strategy_confidence = strategy_confidence
        self.interval_seconds = interval_seconds
        self.llm_gateway = llm_gateway
        self.headlines_provider = headlines_provider
        
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._macro_event_queue: asyncio.Queue[Any] = asyncio.Queue()

    def start(self) -> None:
        """启动后台分析循环"""
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run_loop())
            logger.info("LowEngine started.")

    def stop(self) -> None:
        """停止后台分析循环"""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            logger.info("LowEngine stopped.")

    def trigger_macro_event(self, event_data: Any = None) -> None:
        """外部调用以触发特殊宏观事件的分析"""
        try:
            self._macro_event_queue.put_nowait(event_data)
        except asyncio.QueueFull:
            pass

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                # 获取数据
                market_snapshot = self.market_snapshot_provider()
                headlines = self.headlines_provider() if self.headlines_provider else []
                
                # 执行分析
                analysis = await analyze_low_lane_async(
                    market_snapshot=market_snapshot,
                    committee_models=self.committee_models,
                    committee_min_support=self.committee_min_support,
                    strategy_name=self.strategy_name,
                    strategy_confidence=self.strategy_confidence,
                    llm_gateway=self.llm_gateway,
                    headlines=headlines,
                )
                
                # 更新缓存，由于是宏观层面分析，将其保存为 MACRO，或者遍历 snapshot 中的 symbol
                LOW_ANALYSIS_CACHE["MACRO"] = analysis
                for symbol in market_snapshot.keys():
                    LOW_ANALYSIS_CACHE[symbol.upper()] = analysis
                
                # 发布事件
                event_payload = {
                    "lane": "low",
                    "event_type": "analysis.updated",
                    "preferred_sector": analysis.preferred_sector,
                    "strategy_fit": analysis.strategy_fit,
                    "sector_allocation": analysis.sector_allocation,
                    "committee_approved": analysis.committee_approved,
                    "committee_votes": [
                        {"model": vote.model, "support": vote.support, "score": vote.score}
                        for vote in analysis.committee_votes
                    ],
                    "analyzed_at": datetime.now(tz=timezone.utc).isoformat(),
                }
                
                self.event_bus.publish("low.analysis.updated", event_payload)
                logger.info("LowEngine analysis updated and event published.")
                
                # 等待下一次间隔，或监听宏观事件
                macro_task = asyncio.create_task(self._macro_event_queue.get())
                stop_task = asyncio.create_task(self._stop_event.wait())
                
                done, pending = await asyncio.wait(
                    [macro_task, stop_task],
                    timeout=self.interval_seconds,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in pending:
                    task.cancel()
                    
                if stop_task in done:
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in LowEngine _run_loop: {e}")
                await asyncio.sleep(60)  # 发生错误时后退
