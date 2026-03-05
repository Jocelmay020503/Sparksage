"""Compatibility entrypoint for Railway/uvicorn defaults."""

from api.main import create_app

# Supports `uvicorn main:app` deployments.
app = create_app()


if __name__ == "__main__":
    # Supports `python main.py` by delegating to the unified launcher.
    from run import main as run_main

    run_main()
