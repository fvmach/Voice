# Tests Directory

This directory contains all testing files, demos, and backup implementations for the Cross-Channel AI Agents project.

## Files

### Test Files
- `test_class_structure.py` - Tests for the class structure implementation
- `test_log_filtering.py` - Tests for log filtering functionality
- `test_openai_functions.py` - Tests for OpenAI integration and function calling
- `test_simple_integration.py` - Simple integration tests
- `test_transcription.py` - Tests for transcription functionality
- `test_v2_integration.py` - Version 2 integration tests

### Demo and Backup Files
- `demo_clean_logs.py` - Demo script for log cleaning functionality
- `server_v1_backup.py` - Backup of the version 1 server implementation

## Running Tests

To run all tests:
```bash
cd tests
python -m pytest .
```

To run specific test files:
```bash
python test_class_structure.py
python test_openai_functions.py
```

## Test Environment

Make sure you have the necessary environment variables set up by copying `.env.example` to `.env` in the root directory and configuring your API keys and other settings.