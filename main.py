"""Main entry point for the FastAPI application."""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and expose the FastAPI app

if __name__ == "__main__":
    import uvicorn

    # Use localhost instead of 0.0.0.0 for security (B104)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)  # nosec B104
