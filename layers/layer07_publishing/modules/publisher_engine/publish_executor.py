"""Publish Executor — Execute publish, edit, delete, reschedule via plugins."""
from __future__ import annotations
import time
from typing import Any

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult,
)
from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest


class PublishExecutor:
    """Execute publish operations through platform plugins."""

    def __init__(self) -> None:
        self._execution_count = 0
        self._total_time_ms = 0.0

    def execute_publish(
        self,
        publisher: BasePublisher,
        request: PublishRequest,
    ) -> PublishResult:
        start = time.time()
        try:
            result = publisher.publish(
                content=request.content,
                media_paths=request.get_media_paths(),
                content_type=request.content_type,
            )
        except Exception as e:
            result = PublishResult(success=False, platform=request.platform)
            result.error_message = str(e)[:500]

        elapsed = (time.time() - start) * 1000
        self._execution_count += 1
        self._total_time_ms += elapsed
        return result

    def execute_edit(
        self,
        publisher: BasePublisher,
        post_id: str,
        content: str,
        **kwargs: Any,
    ) -> PublishResult:
        start = time.time()
        try:
            result = publisher.edit(post_id, content, **kwargs)
        except Exception as e:
            result = PublishResult(success=False)
            result.error_message = str(e)[:500]
        self._execution_count += 1
        self._total_time_ms += (time.time() - start) * 1000
        return result

    def execute_delete(
        self,
        publisher: BasePublisher,
        post_id: str,
    ) -> bool:
        start = time.time()
        try:
            result = publisher.delete(post_id)
        except Exception:
            result = False
        self._execution_count += 1
        self._total_time_ms += (time.time() - start) * 1000
        return result

    def execute_reschedule(
        self,
        publisher: BasePublisher,
        request: PublishRequest,
        new_time: float,
    ) -> PublishResult:
        request.scheduled_time = new_time
        request.scheduled = True
        start = time.time()
        try:
            result = publisher.schedule(
                content=request.content,
                scheduled_time=new_time,
                media_paths=request.get_media_paths(),
            )
        except Exception as e:
            result = PublishResult(success=False, platform=request.platform)
            result.error_message = str(e)[:500]
        self._execution_count += 1
        self._total_time_ms += (time.time() - start) * 1000
        return result

    @property
    def execution_count(self) -> int:
        return self._execution_count

    @property
    def avg_time_ms(self) -> float:
        return self._total_time_ms / max(1, self._execution_count)
