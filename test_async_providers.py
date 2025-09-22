#!/usr/bin/env python3
"""
Simple test script for async LLM providers with aiohttp
"""

import asyncio
import os
from src.llm.openai_provider import OpenAIProvider
from src.llm.gemini_provider import GeminiProvider


async def test_openai_async():
    """Test OpenAI async provider"""
    print("Testing OpenAI async provider...")

    try:
        # Check if API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set - skipping OpenAI test")
            return

        provider = OpenAIProvider("gpt-3.5-turbo")

        if not provider.is_available():
            print("❌ OpenAI provider not available")
            return

        # Test async generation
        response = await provider.generate("Say hello in one word")
        print(f"✅ OpenAI async response: {response}")

        # Test async streaming
        print("Testing OpenAI async streaming...")
        stream_response = ""
        async for chunk in provider.generate_stream_async("Count from 1 to 3"):
            stream_response += chunk
            print(f"📡 Chunk: {chunk}")
        print(f"✅ OpenAI async stream complete: {stream_response}")

        # Clean up
        await provider.close()

    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")


async def test_gemini_async():
    """Test Gemini async provider"""
    print("\nTesting Gemini async provider...")

    try:
        # Check if API key is available
        if not os.getenv("GOOGLE_API_KEY"):
            print("❌ GOOGLE_API_KEY not set - skipping Gemini test")
            return

        provider = GeminiProvider("gemini-pro")

        if not provider.is_available():
            print("❌ Gemini provider not available")
            return

        # Test async generation
        response = await provider.generate("Say hello in one word")
        print(f"✅ Gemini async response: {response}")

        # Test async streaming
        print("Testing Gemini async streaming...")
        stream_response = ""
        async for chunk in provider.generate_stream_async("Count from 1 to 3"):
            stream_response += chunk
            print(f"📡 Chunk: {chunk}")
        print(f"✅ Gemini async stream complete: {stream_response}")

        # Clean up
        await provider.close()

    except Exception as e:
        print(f"❌ Gemini test failed: {e}")


async def main():
    """Main test function"""
    print("🚀 Testing async LLM providers with aiohttp...")

    # Test both providers
    await test_openai_async()
    await test_gemini_async()

    print("\n✅ Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())