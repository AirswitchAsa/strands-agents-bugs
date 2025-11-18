from dotenv import load_dotenv


def load_env() -> bool:
    """Load environment variables from .env file."""
    return load_dotenv(".env.local")
