import jwt
from flask import current_app
from jwt import PyJWKClient


def _auth0_settings() -> tuple[str, str, list[str]]:
    """Devuelve el dominio, la audiencia y los algoritmos configurados."""
    raw_domain = (current_app.config.get("AUTH0_DOMAIN") or "").strip()
    domain = (
        raw_domain
        .removeprefix("https://")
        .removeprefix("http://")
        .rstrip("/")
    )
    audience = (current_app.config.get("AUTH0_AUDIENCE") or "").strip()
    algorithms = current_app.config.get("AUTH0_ALGORITHMS") or ["RS256"]
    return domain, audience, algorithms


def is_auth0_configured() -> bool:
    domain, audience, _ = _auth0_settings()
    return bool(domain and audience)


def validate_auth0_token(token: str) -> dict:
    domain, audience, algorithms = _auth0_settings()

    if not domain or not audience:
        raise RuntimeError(
            "Auth0 no está configurado. Define AUTH0_DOMAIN y "
            "AUTH0_AUDIENCE en server/.env."
        )

    issuer = f"https://{domain}/"
    jwks_url = f"{issuer}.well-known/jwks.json"

    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=algorithms,
        audience=audience,
        issuer=issuer,
    )

    return payload
