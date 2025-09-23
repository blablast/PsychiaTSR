"""Standalone test demonstrating logger system capabilities."""
# -*- coding: utf-8 -*-
import os
import sys
import tempfile

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.core.logging import (LoggerFactory, JsonFormatter, MemoryStorage)


def test_basic_loggers():
    """Test basic logger types."""
    print("=== BASIC LOGGERS ===")

    # Console logger with colors
    console_logger = LoggerFactory.create_console_logger(use_colors=True)
    console_logger.log_info("Witaj w systemie terapii TSR")
    console_logger.log_therapist_response("Dzien dobry! Jak sie dzis czujesz?", response_time_ms=120)

    # Memory logger
    memory_logger = LoggerFactory.create_memory_logger(max_entries=5)
    memory_logger.log_stage_transition("opening", "middle")
    memory_logger.log_model_info(
        therapist_model="gpt-4",
        supervisor_model="gpt-3.5-turbo",
        therapist_provider="openai",
        supervisor_provider="openai"
    )

    print(f"Memory logger entries: {memory_logger.entry_count}")


def test_file_logger():
    """Test file logger with different formats."""
    print("\n=== FILE LOGGERS ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        # JSON file logger
        json_file = os.path.join(temp_dir, "test.json")
        json_logger = LoggerFactory.create_file_logger(json_file, format_type="json")

        json_logger.log_info("Testowa wiadomosc uzytkownika")
        json_logger.log_therapist_response("Odpowiedz agenta", response_time_ms=150)

        # Text file logger
        text_file = os.path.join(temp_dir, "test.txt")
        text_logger = LoggerFactory.create_file_logger(text_file, format_type="text")

        text_logger.log_error("Blad podczas przetwarzania", {"error_code": 500})

        # Show file contents
        print(f"JSON file content:")
        with open(json_file, 'r', encoding='utf-8') as f:
            print(f.read())

        print(f"Text file content:")
        with open(text_file, 'r', encoding='utf-8') as f:
            print(f.read())


def test_composite_logger():
    """Test composite logger with multiple storages."""
    print("\n=== COMPOSITE LOGGER ===")

    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = os.path.join(temp_dir, "multi.log")

        # Multi-logger: file + console + memory
        multi_logger = LoggerFactory.create_multi_logger(
            file_path=log_file,
            use_console=True,
            use_streamlit=False,  # Streamlit not available in standalone
            console_colors=True
        )

        multi_logger.log_info("Wiadomosc do wszystkich storages")
        multi_logger.log_stage_transition("middle", "closing")
        multi_logger.log_model_info(
            therapist_model="gemini-pro",
            supervisor_model="gpt-4",
            therapist_provider="gemini",
            supervisor_provider="openai"
        )

        print(f"File exists: {os.path.exists(log_file)}")
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                print("File content preview:")
                print(f.read()[:300] + "...")


def test_custom_dependency_injection():
    """Test custom logger with dependency injection."""
    print("\n=== CUSTOM DEPENDENCY INJECTION ===")

    # Create custom combination: JSON formatter + Memory storage
    json_formatter = JsonFormatter(indent=4)  # Compact JSON
    memory_storage = MemoryStorage(max_entries=3)

    custom_logger = LoggerFactory.create_logger(json_formatter, memory_storage)

    custom_logger.log_info("Custom logger test 1")
    custom_logger.log_info("Custom logger test 2")
    custom_logger.log_info("Custom logger test 3")
    custom_logger.log_info("Custom logger test 4")  # Should replace oldest

    # Retrieve and show entries
    entries = memory_storage.retrieve()
    print(f"Stored entries: {len(entries)}")
    for entry in entries:
        print(f"  {entry.event_type}: {entry.message}")

    # Test new properties
    print(f"Total entries: {custom_logger.entry_count}")
    print(f"Is empty: {custom_logger.is_empty}")


def test_predefined_configurations():
    """Test predefined logger configurations."""
    print("\n=== PREDEFINED CONFIGURATIONS ===")

    # Development logger (console + file)
    dev_logger = LoggerFactory.create_development()
    dev_logger.log_info("Development environment message")

    # Production logger (file only, high capacity)
    prod_logger = LoggerFactory.create_production()
    prod_logger.log_error("Production error", {"severity": "high"})

    print("Development and production loggers created successfully")


if __name__ == "__main__":
    print("Logger System Capabilities Demo")
    print("=" * 50)

    test_basic_loggers()
    test_file_logger()
    test_composite_logger()
    test_custom_dependency_injection()
    test_predefined_configurations()

    print("\nAll tests completed successfully!")
    print("\nKEY FEATURES DEMONSTRATED:")
    print("- Multiple formatters (JSON, Text)")
    print("- Multiple storages (File, Console, Memory, Composite)")
    print("- Dependency injection pattern")
    print("- Predefined configurations")
    print("- Automatic log rotation and limits")
    print("- Structured logging with metadata")