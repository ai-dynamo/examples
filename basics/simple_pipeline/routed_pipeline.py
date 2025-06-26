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

from dynamo.sdk.lib.config import ServiceConfig
from dynamo.runtime.logging import configure_dynamo_logging
from dynamo.sdk import api, endpoint, dynamo_context, service, depends, async_on_start
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


"""
Pipeline Architecture:

Users/Clients (HTTP)
      │
      ▼
┌─────────────┐
│  Frontend   │  HTTP API endpoint (/generate)
└─────────────┘
"""


class RequestType(BaseModel):
    text: str


class ResponseType(BaseModel):
    text: str

@service(
    dynamo={"namespace": "inference"},
)
class Backend:
    def __init__(self) -> None:
        config = ServiceConfig.get_instance()
        self.greeting = config.get("Backend", {}).get("greeting", "Hello")
        logger.info(f"Backend config greeting: {self.greeting}")

        self.sleep_time = config.get("Backend", {}).get("sleep_time", 1)
        logger.info(f"Backend config sleep_time: {self.sleep_time}")

        logger.info("Starting backend")

    @endpoint()
    async def generate(self, words: str):
        logger.info(f"Backend received: {words}")

        for word in words.split(","):
            time.sleep(self.sleep_time)
            yield f"{self.greeting} {word}!\n"

@service(
    dynamo={"namespace": "inference"},
)
class Frontend:
    """A simple frontend HTTP API that forwards requests to the dynamo graph."""

    backend = depends(Backend)

    def __init__(self) -> None:
        # Configure logging
        configure_dynamo_logging(service_name="Frontend")

        config = ServiceConfig.get_instance()
        self.routing_mode = config.get("Frontend", {}).get("routing_mode", "round_robin")
        logger.info(f"Frontend config routing_mode: {self.routing_mode}")

    @async_on_start
    async def async_init(self):
        runtime = dynamo_context["runtime"]
        backend_ns, backend_name = Backend.dynamo_address()
        self.backend_client = await runtime.namespace(backend_ns).component(backend_name).endpoint("generate").client()

    # alternative syntax: @endpoint(transports=[DynamoTransport.HTTP])
    @api()
    async def generate(self, request: RequestType):
        """Stream results from the pipeline."""
        logger.info(f"Frontend received: {request.text}")

        # Or implement a custom router by using backend_client.direct(request.text, worker_id) to pick a specific worker
        if self.routing_mode == "round_robin":
            response_stream = await self.backend_client.round_robin(request.text)
        elif self.routing_mode == "random":
            response_stream = await self.backend_client.random(request.text)
        else:
            raise ValueError(f"Invalid routing mode: {self.routing_mode}")

        async def response_generator():
            async for response in response_stream:
                yield response.data()

        return StreamingResponse(response_generator())
