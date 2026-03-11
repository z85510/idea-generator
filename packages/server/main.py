try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.main import app  # noqa: F401  re-export for `uvicorn main:app`