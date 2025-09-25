"""Bridge for integrating async workflows with Streamlit."""

import asyncio
import threading
from typing import Generator, Any
from functools import wraps


class StreamlitAsyncBridge:
    """Bridge for running async workflows in Streamlit's synchronous environment."""

    _event_loop = None
    _loop_thread = None
    _loop_lock = threading.Lock()

    @classmethod
    def ensure_event_loop(cls):
        """Ensure there's a running event loop for async operations."""
        with cls._loop_lock:
            if cls._event_loop is None or cls._event_loop.is_closed():
                # Create new event loop in a separate thread
                cls._event_loop = asyncio.new_event_loop()
                cls._loop_thread = threading.Thread(
                    target=cls._run_event_loop,
                    daemon=True
                )
                cls._loop_thread.start()

    @classmethod
    def _run_event_loop(cls):
        """Run the event loop in a separate thread."""
        asyncio.set_event_loop(cls._event_loop)
        cls._event_loop.run_forever()

    @classmethod
    def run_async(cls, coro) -> Any:
        """
        Run an async coroutine from synchronous code.

        Args:
            coro: Async coroutine to run

        Returns:
            Result of the coroutine
        """
        cls.ensure_event_loop()

        future = asyncio.run_coroutine_threadsafe(coro, cls._event_loop)
        return future.result()

    @classmethod
    def stream_async(cls, async_generator) -> Generator[Any, None, None]:
        """
        Convert an async generator to a sync generator for Streamlit.

        Args:
            async_generator: Async generator to convert

        Yields:
            Items from the async generator
        """
        cls.ensure_event_loop()

        async def collect_items():
            collected_items = []
            async for async_item in async_generator:
                collected_items.append(async_item)
            return collected_items

        future = asyncio.run_coroutine_threadsafe(collect_items(), cls._event_loop)
        items = future.result()

        for item in items:
            yield item

    @classmethod
    def stream_async_realtime(cls, async_generator) -> Generator[Any, None, None]:
        """Stream items from async generator in real-time."""
        cls.ensure_event_loop()

        import queue
        item_queue = queue.Queue()
        done_event = threading.Event()

        async def producer():
            try:
                async for item in async_generator:
                    item_queue.put(item)
                item_queue.put(None)
            except Exception as e:
                item_queue.put(e)
            finally:
                done_event.set()

        future = asyncio.run_coroutine_threadsafe(producer(), cls._event_loop)

        while True:
            try:
                item = item_queue.get(timeout=0.1)

                if item is None:
                    break
                elif isinstance(item, Exception):
                    raise item
                else:
                    yield item

            except queue.Empty:
                if done_event.is_set():
                    try:
                        while True:
                            item = item_queue.get_nowait()
                            if item is None:
                                break
                            elif isinstance(item, Exception):
                                raise item
                            else:
                                yield item
                    except queue.Empty:
                        break
                continue

    @classmethod
    def is_bridge_active(cls) -> bool:
        """Check if the async bridge event loop is active."""
        return cls._event_loop is not None and not cls._event_loop.is_closed()

    @classmethod
    def close(cls):
        """Close the event loop and clean up resources."""
        with cls._loop_lock:
            if cls._event_loop and not cls._event_loop.is_closed():
                cls._event_loop.call_soon_threadsafe(cls._event_loop.stop)
                if cls._loop_thread and cls._loop_thread.is_alive():
                    cls._loop_thread.join(timeout=5)
                cls._event_loop = None
                cls._loop_thread = None


def async_to_sync(func):
    """
    Decorator to convert async functions to sync for Streamlit compatibility.

    Usage:
        @async_to_sync
        async def my_async_function():
            return await some_async_operation()

        # Can now be called synchronously in Streamlit
        result = my_async_function()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        coro = func(*args, **kwargs)
        return StreamlitAsyncBridge.run_async(coro)
    return wrapper


def async_generator_to_sync(func):
    """
    Decorator to convert async generators to sync generators for Streamlit.

    Usage:
        @async_generator_to_sync
        async def my_async_generator():
            async for item in some_async_source():
                yield item

        # Can now be used in Streamlit
        for item in my_async_generator():
            st.write(item)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        async_gen = func(*args, **kwargs)
        return StreamlitAsyncBridge.stream_async_realtime(async_gen)
    return wrapper