#!/usr/bin/env python3
"""
Utility script to manually refresh models cache.
Run this weekly or when you want to update available models.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Change to project directory for relative paths
os.chdir(project_root)

# Import directly from llm module to avoid src.__init__.py issues
from src.llm import ModelDiscovery

async def main():
    """Refresh models cache from all providers."""
    print("🔄 Refreshing models cache...")

    try:
        cache_data = await ModelDiscovery.refresh_models_cache()

        print("✅ Cache refreshed successfully!")
        print(f"📅 Last updated: {cache_data.get_prompt('last_updated')}")
        print(f"⏰ Expires at: {cache_data.get_prompt('expires_at')}")

        # Show summary
        providers = cache_data.get_prompt("providers", {})
        for provider, data in providers.items():
            models = data.get_prompt("models", [])
            status = data.get_prompt("status", "unknown")
            print(f"  🤖 {provider}: {len(models)} models ({status})")

    except Exception as e:
        print(f"❌ Error refreshing cache: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)