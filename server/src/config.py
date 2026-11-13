import os

from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

INSECURE_JWT_SECRETS = {
    "dev-only-change-me",
    "cambia-esta-clave-en-desarrollo",
    "change-me",
    "secret",
}


def validate_jwt_secret(secret: str | None) -> str:
    """Exige un secreto JWT propio; evita arrancar con valores conocidos."""
    value = (secret or "").strip()

    if len(value) < 32 or value.lower() in INSECURE_JWT_SECRETS:
        raise RuntimeError(
            "JWT_SECRET_KEY no está configurada o es insegura. "
            "Genera una clave con: python -c \"import secrets; print(secrets.token_hex(32))\" "
            "y agrégala a server/.env antes de iniciar el servidor."
        )

    return value


class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}"
        f"/{os.getenv('DB_NAME', 'odiseopay')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "")
    AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "")
    AUTH0_ALGORITHMS = ["RS256"]
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    FRONTEND_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            (
                "http://localhost:3000,http://localhost:5173,"
                "http://127.0.0.1:3000,http://127.0.0.1:5173"
            ),
        ).split(",")
        if origin.strip()
    ]
