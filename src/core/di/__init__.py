"""
Simplified dependency injection using factory pattern.

Features:
- SimpleServiceFactory with direct method calls
- Singletons via @lru_cache where needed
- No reflection or complex lifecycle management
- Clear service creation methods

Benefits:
- Easier to understand and maintain
- Better performance
- Simpler testing
- Implements only needed functionality
"""

# Re-export the simplified ServiceLocator for backwards compatibility
from ..services.simple_service_factory import ServiceLocator

__all__ = ["ServiceLocator"]
