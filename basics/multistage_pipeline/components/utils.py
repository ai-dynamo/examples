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
from typing import Optional
from pydantic import BaseModel
import msgspec

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
