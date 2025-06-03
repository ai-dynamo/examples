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

import logging
import time
import os
import socket
import asyncio
import msgspec
from typing import Optional

from dynamo.sdk import endpoint, service, async_on_start, async_on_shutdown
from dynamo.sdk.lib.config import ServiceConfig
from dynamo._core import NatsQueue

from components.utils import TextRequest, TextResponse, QueueTask

logger = logging.getLogger(__name__)


@service(
    dynamo={"namespace": "multistage"},
)
class Backend:
    """Backend worker that processes text and optionally queues tasks."""

    def __init__(self) -> None:
        config = ServiceConfig.get_instance()
        self.sleep_time = config.get("Backend", {}).get("sleep_time", 1)
        self.queue_enabled = config.get("Backend", {}).get("queue_enabled", True)
        self.queue_threshold = config.get("Backend", {}).get("queue_threshold", 10)

        # Worker identification
        self.worker_id = f"{socket.gethostname()}_{os.getpid()}"
        self.nats_server = os.environ.get("NATS_SERVER", "nats://localhost:4222")
        self.queue: Optional[NatsQueue] = None

        logger.info(f"Backend worker {self.worker_id} initialized")
        logger.info(f"Queue enabled: {self.queue_enabled}, threshold: {self.queue_threshold}")

    @async_on_start
    async def setup_queue(self):
        """Initialize queue connection if enabled"""
        if self.queue_enabled:
            try:
                self.queue = NatsQueue(
                    stream_name="text_processing",
                    nats_server=self.nats_server,
                    dequeue_timeout=1.0
                )
                await self.queue.connect()
                logger.info("Queue connection established")
            except Exception as e:
                logger.error(f"Failed to connect to queue: {e}")
                self.queue_enabled = False

    @async_on_shutdown
    async def cleanup_queue(self):
        """Clean up queue connection"""
        if self.queue:
            await self.queue.close()

    async def _should_queue_task(self, text: str) -> bool:
        """Determine if task should be queued based on criteria"""
        if not self.queue_enabled or not self.queue:
            return False

        # Queue longer texts for additional processing
        return len(text.split()) > self.queue_threshold

    async def _queue_task(self, request: TextRequest):
        """Queue a task for additional processing"""
        if self.queue:
            task = QueueTask(
                text=request.text,
                request_id=request.request_id,
                greeting=request.greeting or "Hello",
                source_worker=self.worker_id
            )
            try:
                encoded_task = msgspec.json.encode(task)
                await self.queue.enqueue_task(encoded_task)
                logger.info(f"Queued task {request.request_id} for additional processing")
            except Exception as e:
                logger.error(f"Failed to queue task: {e}")

    @endpoint()
    async def process_text(self, raw_request: str):
        """Process text and stream results."""
        request = TextRequest.model_validate_json(raw_request)
        logger.info(f"Backend {self.worker_id} processing: {request.request_id}")

        # Check if we should queue this task
        if await self._should_queue_task(request.text):
            await self._queue_task(request)
            # Continue processing normally

        # Process each word with configured greeting
        greeting = request.greeting or "Hello"
        words = request.text.split(",") if "," in request.text else request.text.split()

        for i, word in enumerate(words):
            # Simulate processing time
            await asyncio.sleep(self.sleep_time)

            response = TextResponse(
                processed_text=f"{greeting} {word.strip()}!",
                request_id=request.request_id,
                worker_id=self.worker_id
            )

            yield response.model_dump_json()


@service(
    dynamo={"namespace": "multistage"},
)
class QueueWorker:
    """Worker that pulls and processes tasks from the queue."""

    def __init__(self):
        self.worker_id = f"queue_{socket.gethostname()}_{os.getpid()}"
        self.nats_server = os.environ.get("NATS_SERVER", "nats://localhost:4222")
        self.processing = True
        self.queue: Optional[NatsQueue] = None
        logger.info(f"Queue worker {self.worker_id} initialized")

    @async_on_start
    async def start_processing(self):
        """Start processing tasks from queue"""
        self.queue = NatsQueue(
            stream_name="text_processing",
            nats_server=self.nats_server,
            dequeue_timeout=1.0
        )
        try:
            await self.queue.connect()
            logger.info("Queue worker connected to NATS")
            asyncio.create_task(self._process_queue())
        except Exception as e:
            logger.error(f"Failed to connect to queue: {e}")

    async def _process_queue(self):
        """Continuously process tasks from queue"""
        while self.processing and self.queue:
            try:
                task_data = await self.queue.dequeue_task()
                if task_data:
                    task = msgspec.json.decode(task_data, type=QueueTask)
                    logger.info(f"Queue worker processing task {task.request_id}")
                    # Process the task (could be more complex processing)
                    processed = f"[QUEUED] {task.greeting} {task.text} (from {task.source_worker})"
                    logger.info(f"Processed: {processed}")
                    # In a real system, might save results or trigger other actions
                else:
                    # No task available, wait a bit
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing queue task: {e}")
                await asyncio.sleep(1)

    @async_on_shutdown
    async def stop_processing(self):
        """Stop processing queue"""
        self.processing = False
        if self.queue:
            await self.queue.close()
