"""Хаб WebSocket-подключений купольного экрана.

По сокету уходят только метаданные и url — сам png купол забирает обычным GET.
Гонять base64 через туннель нельзя: это мегабайты на каждую плитку.
"""

import asyncio
import contextlib
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Туннели закрывают простаивающий сокет, поэтому шлём keepalive чаще, чем их таймаут.
PING_INTERVAL_SECONDS = 25


class DomeHub:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._ping_task: asyncio.Task | None = None

    @property
    def client_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info("Купол подключился, всего экранов: %s", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("Купол отключился, осталось экранов: %s", len(self._connections))

    async def broadcast(self, event: dict) -> None:
        async with self._lock:
            targets = list(self._connections)

        dead: list[WebSocket] = []
        for websocket in targets:
            try:
                await websocket.send_json(event)
            except Exception:  # noqa: BLE001 — мёртвое подключение просто выбрасываем
                dead.append(websocket)

        if dead:
            async with self._lock:
                for websocket in dead:
                    self._connections.discard(websocket)
            logger.info("Убрано мёртвых подключений купола: %s", len(dead))

    def start_ping_loop(self) -> None:
        if self._ping_task is None:
            self._ping_task = asyncio.create_task(self._ping_loop())

    async def stop_ping_loop(self) -> None:
        if self._ping_task is not None:
            self._ping_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._ping_task
            self._ping_task = None

    async def _ping_loop(self) -> None:
        while True:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            if self._connections:
                await self.broadcast({"type": "ping"})


hub = DomeHub()
