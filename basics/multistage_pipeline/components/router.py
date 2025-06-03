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
from typing import Dict
import asyncio

from dynamo.sdk import endpoint, service, dynamo_context, async_on_start
from dynamo.runtime import Client

from components.backend import Backend

logger = logging.getLogger(__name__)


@service(
    dynamo={"namespace": "multistage"},
)
class Router:
    """Router service that uses workload-based routing to distribute requests."""

    backend_client: Client
    worker_loads: Dict[int, int]

    def __init__(self):
        self.worker_loads = {}
        logger.info("Router initialized with workload-based routing")

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
        """Monitor worker availability and reset loads periodically"""
        while True:
            try:
                worker_ids = self.backend_client.instance_ids()

                # Initialize new workers with zero load
                for worker_id in worker_ids:
                    if worker_id not in self.worker_loads:
                        self.worker_loads[worker_id] = 0

                # Remove stale workers
                stale_workers = [wid for wid in self.worker_loads if wid not in worker_ids]
                for wid in stale_workers:
                    del self.worker_loads[wid]

                logger.info(f"Active workers: {worker_ids}, loads: {self.worker_loads}")

            except Exception as e:
                logger.error(f"Error monitoring workers: {e}")

            await asyncio.sleep(10)  # Check every 10 seconds

    def _get_best_worker_by_load(self) -> tuple[int, float]:
        """Select worker with lowest current load"""
        if not self.worker_loads:
            return -1, 0.0

        # Find worker with minimum load
        best_worker = min(self.worker_loads.items(), key=lambda x: x[1])
        return best_worker[0], 1.0

    @endpoint()
    async def get_best_worker(self, text: str) -> str:
        """Return best worker ID based on current workload"""
        worker_id, score = self._get_best_worker_by_load()

        if worker_id >= 0:
            # Increment load for selected worker
            self.worker_loads[worker_id] += 1
            logger.info(f"Router selected worker {worker_id} (load: {self.worker_loads[worker_id]}) for text: {text[:30]}...")
            yield f"{worker_id}:{score}"
        else:
            logger.warning("No workers available")
            yield "none:0.0"
