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
from dynamo.runtime.logging import configure_dynamo_logging
from dynamo.sdk import api, service, depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

# Import from this package
from components.middle import Middle
from components.utils import TextRequest

logger = logging.getLogger(__name__)


class HTTPRequest(BaseModel):
    """HTTP request model"""
    text: str
    request_id: Optional[str] = None


@service(
    dynamo={"namespace": "multistage"},
)
class Frontend:
    """Frontend HTTP API that forwards requests to the processing pipeline."""

    middle = depends(Middle)

    def __init__(self) -> None:
        # Configure logging
        configure_dynamo_logging(service_name="Frontend")
        logger.info("Frontend service initialized")

    @api()
    async def generate(self, request: HTTPRequest):
        """Stream results from the multi-stage pipeline."""
        logger.info(f"Frontend received request: text='{request.text}', id='{request.request_id}'")

        # Create internal request
        text_request = TextRequest(
            text=request.text,
            request_id=request.request_id or f"req_{id(request)}"
        )

        # Stream response from middle component
        async def response_generator():
            async for response in self.middle.process(text_request.model_dump_json()):
                yield f"{response}\n"

        return StreamingResponse(response_generator(), media_type="text/plain")
