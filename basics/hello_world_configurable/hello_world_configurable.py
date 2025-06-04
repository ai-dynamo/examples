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

from dynamo.runtime.logging import configure_dynamo_logging
from dynamo.sdk import api, service
from dynamo.sdk.lib.config import ServiceConfig
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
class Frontend:
    """A simple frontend HTTP API that forwards requests to the dynamo graph."""

    def __init__(self) -> None:
        # Configure logging
        configure_dynamo_logging(service_name="Frontend")

        config = ServiceConfig.get_instance()
        self.greeting = config.get("Frontend", {}).get("greeting", "Hello")
        logger.info(f"Frontend config greeting: {self.greeting}")

        self.sleep_time = config.get("Frontend", {}).get("sleep_time", 1)
        logger.info(f"Frontend config sleep_time: {self.sleep_time}")

    # alternative syntax: @endpoint(transports=[DynamoTransport.HTTP])
    @api()
    async def generate(self, request: RequestType):
        """Stream results from the pipeline."""
        logger.info(f"Frontend received: {request.text}")

        def content_generator():
            for word in request.text.split(","):
                time.sleep(self.sleep_time)
                yield f"{self.greeting} {word}!\n"

        return StreamingResponse(content_generator())
