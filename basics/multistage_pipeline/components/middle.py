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
from typing import Optional
import os

from dynamo.sdk import async_on_start, depends, dynamo_context, endpoint, service
from dynamo.sdk.lib.config import ServiceConfig
from dynamo.sdk.lib.dependency import DynamoClient
from dynamo._core import Client

from components.router import Router
from components.backend import Backend
from components.utils import TextRequest, TextResponse, check_required_workers

logger = logging.getLogger(__name__)


@service(
    dynamo={"namespace": "multistage"},
)
class Middle:
    """Processing layer that coordinates between router and backend workers."""

    router: DynamoClient = depends(Router)
    backend_client: Client
    routing_mode: str
    min_workers: int
    greeting: str

    def __init__(self):
        config = ServiceConfig.get_instance()
        self.routing_mode = config.get("Middle", {}).get("routing_mode", "smart")
        self.min_workers = config.get("Middle", {}).get("min_workers", 2)
        self.greeting = config.get("Middle", {}).get("greeting", "Hello")
        logger.info(f"Middle initialized: routing_mode={self.routing_mode}, min_workers={self.min_workers}")

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

        # Wait for minimum workers
        await check_required_workers(
            self.backend_client, self.min_workers, tag="[Middle]"
        )

    async def _process_with_routing(self, request: TextRequest):
        """Process request with intelligent routing"""
        # Add greeting to request if not present
        if request.greeting is None:
            request.greeting = self.greeting

        # Determine routing based on mode
        if self.routing_mode == "smart":
            # Query router for best worker
            async for route_response in self.router.get_best_worker(request.text):
                worker_info = route_response
                worker_id, score = worker_info.split(":")
                score = float(score)
                logger.info(f"Router selected worker {worker_id} with score {score}")
                break

            if worker_id and worker_id != "none":
                # Use specific worker
                backend_generator = await self.backend_client.direct(
                    request.model_dump_json(),
                    int(worker_id),
                )
            else:
                # Fallback to round-robin
                backend_generator = await self.backend_client.round_robin(
                    request.model_dump_json()
                )
        elif self.routing_mode == "random":
            backend_generator = await self.backend_client.random(
                request.model_dump_json()
            )
        elif self.routing_mode == "round_robin":
            backend_generator = await self.backend_client.round_robin(
                request.model_dump_json()
            )
        else:
            # Default to round-robin
            backend_generator = await self.backend_client.round_robin(
                request.model_dump_json()
            )

        # Stream responses from backend
        async for resp in backend_generator:
            response = TextResponse.model_validate_json(resp.data())
            yield response

    @endpoint()
    async def process(self, raw_request: str):
        """Process text through the pipeline with routing."""
        request = TextRequest.model_validate_json(raw_request)
        logger.info(f"Middle processing request: {request.request_id}")

        async for response in self._process_with_routing(request):
            yield response.model_dump_json()
