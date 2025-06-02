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
import hashlib
from typing import Dict, List
import asyncio

from dynamo.sdk import endpoint, service, dynamo_context, async_on_start
from dynamo.sdk.lib.config import ServiceConfig
from dynamo._core import Client

from components.backend import Backend

logger = logging.getLogger(__name__)


@service(
    dynamo={"namespace": "multistage"},
)
class Router:
    """Router service that determines best worker for each request."""

    backend_client: Client
    worker_states: Dict[int, Dict]
    routing_algorithm: str

    def __init__(self):
        config = ServiceConfig.get_instance()
        self.routing_algorithm = config.get("Router", {}).get("algorithm", "hash")
        self.worker_states = {}
        logger.info(f"Router initialized with algorithm: {self.routing_algorithm}")

    @async_on_start
    async def async_init(self):
        runtime = dynamo_context["runtime"]
        backend_ns, backend_name = Backend.dynamo_address()
        self.backend_client = (
            await runtime.namespace(backend_ns)
            .component(backend_name)
            .endpoint("process_text")
            .client()
        )

        # Start worker monitoring
        asyncio.create_task(self._monitor_workers())

    async def _monitor_workers(self):
        """Monitor worker availability and states"""
        while True:
            try:
                worker_ids = self.backend_client.instance_ids()

                # Update worker states
                for worker_id in worker_ids:
                    if worker_id not in self.worker_states:
                        self.worker_states[worker_id] = {
                            "available": True,
                            "processed_count": 0,
                            "last_text_hash": None
                        }

                # Remove stale workers
                stale_workers = [wid for wid in self.worker_states if wid not in worker_ids]
                for wid in stale_workers:
                    del self.worker_states[wid]

            except Exception as e:
                logger.error(f"Error monitoring workers: {e}")

            await asyncio.sleep(5)  # Check every 5 seconds

    def _get_text_hash(self, text: str) -> str:
        """Get hash of text for consistent routing"""
        return hashlib.md5(text.encode()).hexdigest()

    def _get_best_worker_by_hash(self, text: str) -> tuple[int, float]:
        """Select worker based on text hash for sticky sessions"""
        if not self.worker_states:
            return -1, 0.0

        text_hash = self._get_text_hash(text)
        worker_ids = list(self.worker_states.keys())

        # Simple hash-based selection
        selected_idx = int(text_hash, 16) % len(worker_ids)
        selected_worker = worker_ids[selected_idx]

        # Score based on whether this worker has seen similar text
        score = 1.0
        if self.worker_states[selected_worker]["last_text_hash"] == text_hash[:8]:
            score = 2.0  # Higher score for cache hit

        return selected_worker, score

    def _get_best_worker_by_load(self) -> tuple[int, float]:
        """Select worker with lowest load"""
        if not self.worker_states:
            return -1, 0.0

        # Find worker with lowest processed count
        best_worker = min(
            self.worker_states.items(),
            key=lambda x: x[1]["processed_count"]
        )

        return best_worker[0], 1.0

    @endpoint()
    async def get_best_worker(self, text: str) -> str:
        """Return best worker ID and score for the given text"""
        worker_id = -1
        score = 0.0

        if self.routing_algorithm == "hash":
            worker_id, score = self._get_best_worker_by_hash(text)
        elif self.routing_algorithm == "load":
            worker_id, score = self._get_best_worker_by_load()
        else:
            # Default to hash-based
            worker_id, score = self._get_best_worker_by_hash(text)

        if worker_id >= 0:
            # Update worker state
            self.worker_states[worker_id]["processed_count"] += 1
            self.worker_states[worker_id]["last_text_hash"] = self._get_text_hash(text)[:8]

        logger.info(f"Router selected worker {worker_id} with score {score} for text: {text[:30]}...")

        if worker_id < 0:
            yield "none:0.0"
        else:
            yield f"{worker_id}:{score}"
