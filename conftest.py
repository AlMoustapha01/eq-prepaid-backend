"""Pytest configuration file to set up the Python path for tests."""

import sys
from pathlib import Path

# Add the src directory to Python path so tests can import modules
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
