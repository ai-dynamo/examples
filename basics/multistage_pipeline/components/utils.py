# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
from typing import Optional, ClassVar
from contextlib import asynccontextmanager
from pydantic import BaseModel
import msgspec

from dynamo._core import NatsQueue

logger = logging.getLogger(__name__)


class TextRequest(BaseModel):
    """Request model for text processing"""
    text: str
    request_id: str = "default_id"
    greeting: Optional[str] = None


class TextResponse(BaseModel):
    """Response model for processed text"""
    processed_text: str
    request_id: str
    worker_id: Optional[str] = None


class QueueTask(msgspec.Struct, omit_defaults=True, dict=True):
    """Task structure for queue processing"""
    text: str
    request_id: str
    greeting: str = "Hello"
    source_worker: str = "unknown"


class TextProcessingQueue:
    """Wrapper around NatsQueue for text processing tasks"""
    _instance: ClassVar[Optional["TextProcessingQueue"]] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(
        self,
        stream_name: str = "text_processing",
        nats_server: str = "nats://localhost:4222",
        dequeue_timeout: float = 1.0,
    ):
        self.queue = NatsQueue(stream_name, nats_server, dequeue_timeout)
        self._connected = False

    @classmethod
    @asynccontextmanager
    async def get_instance(
        cls,
        *,
        stream_name: str = "text_processing",
        nats_server: str = "nats://localhost:4222",
        dequeue_timeout: float = 1.0,
    ):
        """Get or create a singleton instance of TextProcessingQueue"""
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls(
                    stream_name=stream_name,
                    nats_server=nats_server,
                    dequeue_timeout=dequeue_timeout,
                )
                await cls._instance.connect()
            try:
                yield cls._instance
            except Exception:
                if cls._instance:
                    await cls._instance.close()
                cls._instance = None
                raise

    async def connect(self):
        """Connect to NATS server"""
        if not self._connected:
            await self.queue.connect()
            self._connected = True

    async def close(self):
        """Close connection to NATS server"""
        if self._connected:
            await self.queue.close()
            self._connected = False

    async def enqueue_task(self, task: QueueTask) -> None:
        """Enqueue a task for processing"""
        try:
            encoded_task = msgspec.json.encode(task)
            await self.queue.enqueue_task(encoded_task)
            logger.info(f"Enqueued task: {task.request_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to enqueue task: {e}")

    async def dequeue_task(self, timeout: Optional[float] = None) -> Optional[QueueTask]:
        """Dequeue and return a task"""
        try:
            task_data = await self.queue.dequeue_task(timeout)
            if task_data:
                task = msgspec.json.decode(task_data, type=QueueTask)
                logger.info(f"Dequeued task: {task.request_id}")
                return task
            return None
        except Exception as e:
            raise RuntimeError(f"Failed to dequeue task: {e}")

    async def get_queue_size(self) -> int:
        """Get the number of messages currently in the queue"""
        try:
            return await self.queue.get_queue_size()
        except Exception as e:
            raise RuntimeError(f"Failed to get queue size: {e}")


async def check_required_workers(
    workers_client,
    required_workers: int,
    poll_interval: int = 5,
    tag: str = "",
):
    """Wait until the minimum number of workers are ready."""
    worker_ids = workers_client.instance_ids()
    num_workers = len(worker_ids)

    while num_workers < required_workers:
        print(
            f"{tag} Waiting for workers to be ready. "
            f"Current: {num_workers}, Required: {required_workers}"
        )
        await asyncio.sleep(poll_interval)
        worker_ids = workers_client.instance_ids()
        num_workers = len(worker_ids)

    print(f"{tag} Workers ready: {worker_ids}")
    return worker_ids
