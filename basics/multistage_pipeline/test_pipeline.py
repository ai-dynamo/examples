#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Test script for the multi-stage pipeline example."""

import asyncio
import aiohttp
import json


async def test_pipeline():
    """Test the pipeline with various requests."""
    base_url = "http://localhost:8000"

    # Test cases
    test_cases = [
        {
            "name": "Simple comma-separated text",
            "data": {"text": "hello,world,test"},
            "expected_words": ["hello", "world", "test"]
        },
        {
            "name": "Text with request ID",
            "data": {"text": "sun,moon,stars", "request_id": "space-123"},
            "expected_words": ["sun", "moon", "stars"]
        },
        {
            "name": "Long text for queue testing",
            "data": {
                "text": "This is a much longer text with more than ten words that should trigger the queue processing feature",
                "request_id": "long-text-456"
            },
            "expected_words": None  # Too many to check individually
        }
    ]

    async with aiohttp.ClientSession() as session:
        for test in test_cases:
            print(f"\n--- Testing: {test['name']} ---")

            try:
                async with session.post(
                    f"{base_url}/generate",
                    json=test["data"],
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"Status: {response.status}")

                    if response.status == 200:
                        # Read streaming response
                        async for line in response.content:
                            if line:
                                text = line.decode('utf-8').strip()
                                if text:
                                    print(f"Response: {text}")

                                    # Verify expected words if specified
                                    if test["expected_words"]:
                                        for word in test["expected_words"]:
                                            if word in text:
                                                print(f"✓ Found expected word: {word}")
                    else:
                        error = await response.text()
                        print(f"Error: {error}")

            except Exception as e:
                print(f"Failed to connect: {e}")
                print("Make sure the pipeline is running!")
                return

    print("\n--- Test completed ---")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
